# from rediy.server import Server

# if __name__ == "__main__":
#     server = Server()
#     server.start()



import asyncio

from rediy.async_server import AsyncServer

if __name__ == "__main__":
    server = AsyncServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Shutting down server...")