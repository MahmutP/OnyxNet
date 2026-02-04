import asyncio
import websockets
from server.connection import handle_client, handle_websocket

import argparse

import socket

def get_lan_ip():
    try:
        # Connect to a public DNS server to determine the route
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

async def main(host, port):
    """
    Starts both TCP and WebSocket servers.
    """
    ws_port = port + 1
    lan_ip = get_lan_ip()

    # Start TCP Server
    tcp_server = await asyncio.start_server(
        handle_client, host, port
    )
    print(f'[CRITICAL] OnyxNet TCP Relay serving on {host}:{port}')
    print(f'[INFO] LAN Address: {lan_ip}:{port} (Share this with local peers)')

    # Start WebSocket Server
    print(f'[CRITICAL] OnyxNet WebSocket Relay serving on {host}:{ws_port}')
    async with websockets.serve(handle_websocket, host, ws_port):
        # Run both until stopped
        async with tcp_server:
            await tcp_server.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="OnyxNet Relay Server")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8888, help='TCP Port (WS will use Port+1)')
    args = parser.parse_args()

    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        print("\n[!] Server stopped by user.")
