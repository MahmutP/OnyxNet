import asyncio

# Global list to keep track of connected clients (writers or websockets)
connected_clients = []

async def broadcast(data, sender=None):
    """
    Broadcasts raw bytes to all connected clients (TCP and WebSocket).
    """
    for client in connected_clients:
        if client == sender:
            continue
            
        try:
            # Check if it's a WebSocket (has 'send' method) or TCP (has 'write')
            if hasattr(client, 'send'):
                # WebSocket expects str or bytes. data is bytes here (from TCP readline)
                # But wait, TCP readline returns bytes with \n.
                # WebSocket text frame is usually preferred for JSON.
                # Let's decode to str for WebSocket to be safe, or send bytes.
                # If we send bytes, browser receives Blob/ArrayBuffer.
                # If we send str, browser receives Text.
                # Our protocol is JSON-lines.
                
                # If data is bytes, decode it for WS text frame
                text_data = data.decode('utf-8').strip()
                await client.send(text_data)
                
            elif hasattr(client, 'write'):
                # TCP Writer
                client.write(data)
                await client.drain()
                
        except Exception as e:
            print(f"Error broadcasting to client: {e}")
            # We might remove client here, but main loops handle that.

async def handle_client(reader, writer):
    """
    Handles a single TCP client connection.
    """
    addr = writer.get_extra_info('peername')
    print(f"[+] New TCP connection from {addr}")

    connected_clients.append(writer)

    try:
        while True:
            # Read line-by-line (expecting JSON + newline)
            data = await reader.readline()
            if not data:
                break

            # Broadcast to everyone (including WebSockets)
            await broadcast(data, sender=writer)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error handling TCP client {addr}: {e}")
    finally:
        print(f"[-] TCP Connection closed from {addr}")
        if writer in connected_clients:
            connected_clients.remove(writer)
        writer.close()
        await writer.wait_closed()

async def handle_websocket(websocket):
    """
    Handles a single WebSocket client connection.
    """
    addr = websocket.remote_address
    print(f"[+] New WebSocket connection from {addr}")

    connected_clients.append(websocket)
    
    try:
        async for message in websocket:
            # message is str (text frame) or bytes (binary frame)
            # We treat it as our JSON protocol line.
            # TCP clients expect bytes ending with \n.
            
            if isinstance(message, str):
                data_bytes = (message + "\n").encode('utf-8')
            else:
                data_bytes = message + b"\n"
                
            await broadcast(data_bytes, sender=websocket)
            
    except Exception as e:
        print(f"Error handling WebSocket client {addr}: {e}")
    finally:
        print(f"[-] WebSocket Connection closed from {addr}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)
