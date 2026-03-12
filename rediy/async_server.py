import asyncio
import os
import time
import random
from io import BytesIO

from rediy.protocol import ProtocolHandler

class AsyncServer:
    def __init__(self, host="127.0.0.1", port=6379):
        self.host=host
        self.port=port
        self.protocol = ProtocolHandler()
        self.store = {}
        self.expiry = {}
        self.commands = {
            "GET": self.get,
            "SET": self.set,
            "DELETE": self.delete,
            "MGET": self.mget,
            "MSET": self.mset,
            "FLUSH": self.flush,
            "TTL": self.ttl
        }
    
    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"Server started on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()
    
    async def handle_client(self, reader, writer):
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                stream = BytesIO(data)
                message = self.protocol.parse(stream)
                if not isinstance(message, list):
                    message = [message]
                command = message[0].upper()
                if command not in self.commands:
                    writer.write(b"-ERR unknown command\r\n")
                    await writer.drain()
                    continue
                result = self.commands[command](*message[1:])
                response = self.serialize(result)
                writer.write(response)
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            
    def serialize(self, data):
        if data is None:
            return b"$-1\r\n"
        if isinstance(data, str):
            encoded = data.encode()
            return f"${len(encoded)}\r\n".encode() + encoded + b"\r\n"
        if isinstance(data, int):
            return f":{data}\r\n".encode()
        if isinstance(data, list):
            response = f"*{len(data)}\r\n".encode()
            for item in data:
                response += self.serialize(item)
            return response
        return b"-ERR unknown response type\r\n"
    
    def get(self, key):
        if key in self.expiry and time.time() > self.expiry[key]:
            self.store.pop(key, None)
            self.expiry.pop(key, None)
            return None
        return self.store.get(key, None)
    
    def set(self, key, value, *args):
        self.store[key] = value
        if len(args) == 2 and args[0].upper() == "EX":
            seconds = int(args[1])
            self.expiry[key] = time.time() + seconds
        else:
            self.expiry.pop(key, None)
        return "OK"
    
    def delete(self, key):
        if key in self.store:
            self.store.pop(key, None)
            self.expiry.pop(key, None)
            return 1
        return 0
    
    def mget(self, *keys):
        return [self.store.get(key, None) for key in keys]
    
    def mset(self, *items):
        if len(items) % 2 != 0:
            raise Exception("MSET requires an even number of arguments")
        for i in range(0, len(items), 2):
            key = items[i]
            value = items[i + 1]
            self.store[key] = value
        return "OK"
    
    def flush(self):
        count = len(self.store)
        self.store.clear()
        self.expiry.clear()
        return count
    
    def ttl(self, key):
        if key not in self.store:
            return -2
        if key not in self.expiry:
            return -1
        remaining = int(self.expiry[key] - time.time())
        if remaining < 0:
            self.store.pop(key, None)
            self.expiry.pop(key, None)
            return -2
        return remaining