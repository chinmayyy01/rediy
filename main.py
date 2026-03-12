import asyncio

from rediy.async_server import AsyncServer

if __name__ == "__main__":
    server = AsyncServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Shutting down server...")