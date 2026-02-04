import os
import base64
import logging
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class OnyxCrypto:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.public_key_pem = None

    def generate_keys(self):
        """Generates RSA 2048-bit key pair."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # Serialize public key to PEM format for sharing
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

    def load_public_key(self, pem_string):
        """Loads a public key from a PEM string."""
        try:
            return serialization.load_pem_public_key(pem_string.encode('utf-8'))
        except Exception as e:
            logging.error(f"Failed to load public key: {e}")
            logging.error(f"PEM Content: {pem_string}")
            return None

    def encrypt_aes_key_for_recipient(self, aes_key, recipient_pub_key):
        """Encrypts the AES session key with the recipient's RSA public key."""
        ciphertext = recipient_pub_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(ciphertext).decode('utf-8')

    def decrypt_aes_key(self, encrypted_aes_key_b64):
        """Decrypts the AES session key with our private key."""
        encrypted_aes_key = base64.b64decode(encrypted_aes_key_b64)
        plaintext = self.private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext

    def encrypt_message(self, message, recipient_pub_keys):
        """
        Hybrid Encryption:
        1. Generate random AES key.
        2. Encrypt message with AES-GCM.
        3. Encrypt AES key with each recipient's Public Key.
        """
        # Generate AES Key (32 bytes) and IV (12 bytes)
        aes_key = os.urandom(32)
        iv = os.urandom(12)

        # Encrypt Message with AES-GCM
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(message.encode('utf-8')) + encryptor.finalize()
        
        # Encrypt key for each recipient
        encrypted_keys = {}
        for user_id, pub_key in recipient_pub_keys.items():
            encrypted_keys[user_id] = self.encrypt_aes_key_for_recipient(aes_key, pub_key)

        return {
            "iv": base64.b64encode(iv).decode('utf-8'),
            "tag": base64.b64encode(encryptor.tag).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "keys": encrypted_keys
        }

    def decrypt_payload(self, iv_b64, tag_b64, ciphertext_b64, encrypted_aes_key_b64):
        try:
            aes_key = self.decrypt_aes_key(encrypted_aes_key_b64)
            iv = base64.b64decode(iv_b64)
            tag = base64.b64decode(tag_b64)
            ciphertext = base64.b64decode(ciphertext_b64)
            
            cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag))
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')
        except Exception as e:
            return f"[Decryption Error: {e}]"
