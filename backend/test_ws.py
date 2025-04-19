import asyncio
import websockets
import msgpack
import json

API_KEY = "AKKD5BDJP5D1SB5FW8AE"
API_SECRET = "MuuUeQLbRuQN926rZ6gLYW8Rji43VTHuW7QFSRPX"
WS_URL = "wss://stream.data.alpaca.markets/v2/iex"

async def test_websocket():
    try:
        async with websockets.connect(WS_URL) as ws:
            # Auth
            auth_msg = {
                "action": "auth",
                "key": API_KEY,
                "secret": API_SECRET
            }
            await ws.send(msgpack.packb(auth_msg))
            auth_response = await ws.recv()
            print("Auth response:", msgpack.unpackb(auth_response, strict_map_key=False))

            # Subscribe to AAPL quotes
            sub_msg = {
                "action": "subscribe",
                "quotes": ["AAPL"]
            }
            await ws.send(msgpack.packb(sub_msg))
            sub_response = await ws.recv()
            print("Subscribe response:", msgpack.unpackb(sub_response, strict_map_key=False))

            # Listen for messages
            print("Listening for messages...")
            while True:
                msg = await ws.recv()
                print("Received:", msgpack.unpackb(msg, strict_map_key=False))

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 
