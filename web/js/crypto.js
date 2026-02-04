const OnyxCrypto = {
    keyPair: null,
    publicKeyPem: null,
    peerPublicKeys: {}, // {id: CryptoKey}

    // Helper: ArrayBuffer to Base64
    ab2str: function (buf) {
        return String.fromCharCode.apply(null, new Uint8Array(buf));
    },

    // Helper: Base64 to ArrayBuffer
    str2ab: function (str) {
        const buf = new ArrayBuffer(str.length);
        const bufView = new Uint8Array(buf);
        for (let i = 0, strLen = str.length; i < strLen; i++) {
            bufView[i] = str.charCodeAt(i);
        }
        return buf;
    },

    // Helper: PEM String to ArrayBuffer (strips headers)
    pemToArrayBuffer: function (pem) {
        const b64 = pem.replace(/-----BEGIN PUBLIC KEY-----/g, '')
            .replace(/-----END PUBLIC KEY-----/g, '')
            .replace(/\\n/g, '');
        return Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    },

    // Helper: ArrayBuffer to PEM String
    arrayBufferToPem: function (buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        const b64 = btoa(binary);
        // Insert newlines every 64 characters
        const formatted = b64.match(/.{1,64}/g).join('\n');
        return `-----BEGIN PUBLIC KEY-----\n${formatted}\n-----END PUBLIC KEY-----\n`;
    },

    /**
     * Generates a new RSA-OAEP 2048-bit key pair for this session.
     * Also exports the public key to PEM format.
     */
    generateKeys: async function () {
        this.keyPair = await window.crypto.subtle.generateKey(
            {
                name: "RSA-OAEP",
                modulusLength: 2048,
                publicExponent: new Uint8Array([1, 0, 1]), // 65537
                hash: "SHA-256"
            },
            true,
            ["encrypt", "decrypt"]
        );

        // Export Public Key to PEM for sharing
        const exported = await window.crypto.subtle.exportKey("spki", this.keyPair.publicKey);
        this.publicKeyPem = this.arrayBufferToPem(exported);
        console.log("Keys Generated.");
    },

    /**
     * Imports a peer's public key from PEM format.
     * @param {string} id - The peer's unique identifier.
     * @param {string} pem - The peer's public key in PEM format.
     */
    importPeerKey: async function (id, pem) {
        try {
            const binaryDer = this.pemToArrayBuffer(pem);
            const key = await window.crypto.subtle.importKey(
                "spki",
                binaryDer,
                {
                    name: "RSA-OAEP",
                    hash: "SHA-256"
                },
                true,
                ["encrypt"]
            );
            this.peerPublicKeys[id] = key;
            console.log(`Imported key for ${id}`);
        } catch (e) {
            console.error(`Failed to import key for ${id}:`, e);
        }
    },

    /**
     * Encrypts a message using Hybrid Encryption (AES-GCM + RSA-OAEP).
     * 1. Generates a random AES-256 session key.
     * 2. Encrypts the message with this AES key.
     * 3. Encrypts the AES key separately for each known peer using their RSA Public Key.
     * 
     * @param {string} message - The plaintext message to encrypt.
     * @returns {Object} The encrypted payload containing IV, Tag, Ciphertext, and Encrypted Keys.
     */
    encryptMessage: async function (message) {
        // 1. Generate AES Key (Session Key)
        const aesKey = await window.crypto.subtle.generateKey(
            { name: "AES-GCM", length: 256 },
            true,
            ["encrypt", "decrypt"]
        );

        // 2. Encrypt Message with AES-GCM
        const iv = window.crypto.getRandomValues(new Uint8Array(12));
        const encodedMsg = new TextEncoder().encode(message);

        const ciphertext = await window.crypto.subtle.encrypt(
            { name: "AES-GCM", iv: iv },
            aesKey,
            encodedMsg
        );

        // We need auth tag? SubtleCrypto appends the tag to the ciphertext automatically for GCM!
        // Python `cryptography` separates them.
        // SubtleCrypto result = Ciphertext + Tag (last 16 bytes usually). 
        // We need to split them to match Python's expectation if Python expects separate tag.
        // Let's check `client/crypto.py`:
        // encryptor.tag is separate.
        // In python decrypt: `modes.GCM(iv, tag)`

        // So for JS -> Python:
        // We need to extract the last 16 bytes as tag.

        const encryptedBytes = new Uint8Array(ciphertext);
        const tagLength = 16;
        const msgLength = encryptedBytes.length - tagLength;

        const actualCiphertext = encryptedBytes.slice(0, msgLength);
        const tag = encryptedBytes.slice(msgLength);

        // 3. Encrypt AES Key for each recipient
        const encryptedKeys = {};

        // Export AES key to raw bytes to encrypt it
        const rawAesKey = await window.crypto.subtle.exportKey("raw", aesKey);

        for (const [id, pubKey] of Object.entries(this.peerPublicKeys)) {
            const encryptedKeyBuffer = await window.crypto.subtle.encrypt(
                { name: "RSA-OAEP" },
                pubKey,
                rawAesKey
            );
            encryptedKeys[id] = btoa(String.fromCharCode(...new Uint8Array(encryptedKeyBuffer)));
        }

        // Return formatted payload
        return {
            iv: btoa(String.fromCharCode(...iv)),
            tag: btoa(String.fromCharCode(...tag)),
            ciphertext: btoa(String.fromCharCode(...actualCiphertext)),
            keys: encryptedKeys
        };
    },

    /**
     * Decrypts an incoming message.
     * 1. Finds the encrypted AES key meant for us.
     * 2. Decrypts the AES key using our Private Key.
     * 3. Decrypts the message content using the AES key.
     * 
     * @param {Object} payload - The received encrypted payload.
     * @param {string} myId - Our own user ID to find the correct key.
     * @returns {string} The decrypted plaintext message.
     */
    decryptMessage: async function (payload, myId) {
        // Find my encrypted key
        const myEncryptedKeyB64 = payload.keys[myId];
        if (!myEncryptedKeyB64) {
            throw new Error("No key for me in this message.");
        }

        // 1. Decrypt AES Key
        const encryptedKeyBuffer = Uint8Array.from(atob(myEncryptedKeyB64), c => c.charCodeAt(0));

        const rawAesKey = await window.crypto.subtle.decrypt(
            { name: "RSA-OAEP" },
            this.keyPair.privateKey,
            encryptedKeyBuffer
        );

        const aesKey = await window.crypto.subtle.importKey(
            "raw",
            rawAesKey,
            { name: "AES-GCM" },
            false,
            ["decrypt"]
        );

        // 2. Decrypt Message (AES-GCM)
        // Python sends ciphertext and tag separately.
        // SubtleCrypto expects them combined (Ciphertext + Tag).

        const iv = Uint8Array.from(atob(payload.iv), c => c.charCodeAt(0));
        const tag = Uint8Array.from(atob(payload.tag), c => c.charCodeAt(0));
        const ciphertext = Uint8Array.from(atob(payload.ciphertext), c => c.charCodeAt(0));

        // Combine Ciphertext + Tag
        const combined = new Uint8Array(ciphertext.length + tag.length);
        combined.set(ciphertext);
        combined.set(tag, ciphertext.length);

        const decryptedBuffer = await window.crypto.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            aesKey,
            combined
        );

        return new TextDecoder().decode(decryptedBuffer);
    }
};
