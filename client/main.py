import asyncio
import sys
import json
import uuid
import logging
import curses
import argparse
from client.crypto import OnyxCrypto
from client.ui import OnyxUI

HOST = '127.0.0.1'
PORT = 8888

# Setup Logging to file instead of stdout since curses uses stdout
# Setup Logging: specific file logging disabled per user request
# logging.basicConfig(filename='client.log', level=logging.INFO, format='%(asctime)s - %(message)s')
# Redirect logs to nowhere to prevent file creation and preserve TUI
logging.getLogger().addHandler(logging.NullHandler())

class OnyxClient:
    def __init__(self, stdscr, host, port):
        self.id = str(uuid.uuid4())
        self.crypto = OnyxCrypto()
        self.peer_keys = {} # {uuid: pubkey_obj}
        self.writer = None
        self.reader = None # Ensure reader is initialized
        self.ui = OnyxUI(stdscr)
        self.ui.commands = ['/exit', '/quit', '/clear', '/help']
        self.running = True
        self.host = host
        self.port = port
        
    async def connect(self):
        self.ui.add_message("SYSTEM", f"Generating Keys... ID: {self.id[:8]}", system=True)
        self.crypto.generate_keys()
        
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.ui.connection_status = "Connected"
            self.ui.redraw_all()
            self.ui.add_message("SYSTEM", f"Connected to relay {self.host}:{self.port}", system=True)

            # Send Handshake
            await self.send_handshake()

            # Start reading/writing tasks
            await asyncio.gather(
                self.read_from_server(self.reader),
                self.main_loop()
            )
        except ConnectionRefusedError:
            self.ui.connection_status = "Failed"
            self.ui.redraw_all()
            self.ui.add_message("ERROR", "Connection refused.", system=True)
            await asyncio.sleep(5)
        except Exception as e:
            if self.running: # Only log if not intentional shutdown
                self.ui.add_message("ERROR", f"Error: {e}", system=True)
                logging.error(f"Startup error: {e}")

    # ... (rest of methods remain same)

    async def disconnect(self):
        self.running = False
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:
                pass
        self.ui.add_message("SYSTEM", "Disconnected.", system=True)

    async def send_json(self, data):
        """Helper to send JSON data with a newline delimiter."""
        if self.writer:
            msg = json.dumps(data) + "\n"
            self.writer.write(msg.encode())
            await self.writer.drain()

    async def send_handshake(self):
        payload = {
            "type": "handshake",
            "sender_id": self.id,
            "pubkey": self.crypto.public_key_pem
        }
        await self.send_json(payload)

    async def handle_handshake(self, data):
        sender_id = data.get("sender_id")
        pubkey_pem = data.get("pubkey")
        
        if sender_id == self.id:
            return 
            
        if sender_id not in self.peer_keys:
            key_obj = self.crypto.load_public_key(pubkey_pem)
            if key_obj:
                self.peer_keys[sender_id] = key_obj
                self.ui.user_count = len(self.peer_keys) + 1 # peers + me
                self.ui.add_message("SYSTEM", f"New Peer: {sender_id[:8]}", system=True)
                self.ui.redraw_all()
                # Reply with basic handshake so they know us (simplified)
                asyncio.create_task(self.send_handshake())

    async def handle_message(self, data):
        sender_id = data.get("sender_id")
        if sender_id == self.id:
            return
            
        encrypted_payload = data.get("payload")
        
        keys_map = encrypted_payload.get("keys", {})
        if self.id in keys_map:
            encrypted_aes_key = keys_map[self.id]
            plaintext = self.crypto.decrypt_payload(
                encrypted_payload['iv'],
                encrypted_payload['tag'],
                encrypted_payload['ciphertext'],
                encrypted_aes_key
            )
            self.ui.add_message(sender_id[:8], plaintext)
        else:
            self.ui.add_message("SYSTEM", f"Unreadable msg from {sender_id[:8]}", system=True)

    async def read_from_server(self, reader):
        while self.running:
            try:
                line = await reader.readline()
                if not line:
                    break
                
                try:
                    line_str = line.decode().strip()
                    logging.info(f"Received RAW: {line_str}")
                    data = json.loads(line_str)
                    msg_type = data.get("type")
                    
                    if msg_type == "handshake":
                        await self.handle_handshake(data)
                    elif msg_type == "msg":
                        await self.handle_message(data)
                except json.JSONDecodeError:
                    pass
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.running:
                    self.ui.add_message("ERROR", f"Read Error: {e}", system=True)
                break

    async def main_loop(self):
        while self.running:
            user_input = await self.ui.get_input()
            
            if user_input:
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                else:
                    await self.send_chat_message(user_input)
            
            await asyncio.sleep(0.05)

    async def handle_command(self, cmd_str):
        parts = cmd_str.split()
        cmd = parts[0].lower()
        
        if cmd == '/exit' or cmd == '/quit':
            await self.disconnect()
        elif cmd == '/clear':
            self.ui.messages = []
            self.ui.draw_messages()
        elif cmd == '/help':
            help_text = "Commands:\n/exit - Close Client\n/quit - Close Client\n/clear - Clear History\n/help - Show this message\n(TAB to complete)"
            self.ui.show_popup("HELP", help_text)
        else:
            self.ui.add_message("ERROR", f"Unknown command: {cmd}", system=True)

    async def send_chat_message(self, msg):
        if not self.peer_keys:
            self.ui.add_message("SYSTEM", "Waiting for peers...", system=True)
            return

        # Show my own message in UI immediately
        self.ui.add_message("Me", msg)

        try:
            encrypted_data = self.crypto.encrypt_message(msg, self.peer_keys)
            payload = {
                "type": "msg",
                "sender_id": self.id,
                "payload": encrypted_data
            }
            await self.send_json(payload)
        except Exception as e:
            self.ui.add_message("ERROR", f"Send Failed: {e}", system=True)

def main(stdscr, host, port):
    # Curses wrapper calls this
    client = OnyxClient(stdscr, host, port)
    try:
        asyncio.run(client.connect())
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="OnyxNet Terminal Client")
    parser.add_argument('--host', default='127.0.0.1', help='Server Host')
    parser.add_argument('--port', type=int, default=8888, help='Server Port')
    args = parser.parse_args()
    
    # Use curses.wrapper to handle setup/teardown
    curses.wrapper(main, args.host, args.port)
