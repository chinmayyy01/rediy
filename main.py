import sys
import asyncio
from rediy.server import Server
from rediy.async_server import AsyncServer

def run_threaded():
    server = Server()
    server.start()

def run_async():
    server = AsyncServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Shutting down server...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py [threaded|async]")
        sys.exit(1)

    mode = sys.argv[1]
    
    if mode == "threaded":
        run_threaded()
    elif mode == "async":
        run_async()
    else:
        print("Invalid mode. Use 'threaded' or 'async'.")
        sys.exit(1)