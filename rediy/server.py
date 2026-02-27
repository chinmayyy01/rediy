import socket
import threading
from rediy.protocol import ProtocolHandler

class Server:
    def __init__(self, host="127.0.0.1", port=6379):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.protocol = ProtocolHandler()
        self.store = {}
        self.commands = {
            "GET": self.get,
            "SET": self.set,
            "DELETE": self.delete
        }
        
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        
        print(f"Server started on {self.host}:{self.port}")

        while True:
            conn, addr = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
            thread.start()

    def handle_client(self, conn, addr):
        try:
            while True:
                message = self.protocol.parse(conn)
                
                if not isinstance(message, list):
                    message = [message]
                    
                command_name = message[0].upper()
                
                if command_name not in self.commands:
                    response = f"-ERR unknown command\r\n"
                    conn.sendall(response.encode())
                    continue
                
                try:
                    result = self.commands[command_name](*message[1:])
                    self.send_response(conn, result)
                except Exception as e:
                    error = f"-ERR {str(e)}\r\n"
                    conn.sendall(error.encode())
                
        except ConnectionError:
            pass
        finally:
            conn.close()
            
    def get(self, key):
        return self.store.get(key, None)
    def set(self, key, value):
        self.store[key] = value
        return "OK"
    def delete(self, key):
        if key in self.store:
            del self.store[key]
            return 1
        return 0
        
    def send_response(self, conn, data):
        if data is None:
            conn.sendall(b"$-1\r\n")
        elif isinstance(data, str):
            encoded = data.encode()
            response = f"${len(encoded)}\r\n".encode() + encoded + b"\r\n"
            conn.sendall(response)
        elif isinstance(data, int):
            response = f":{data}\r\n".encode()
            conn.sendall(response)
        else:
            error = f"-ERR unsupported response type\r\n"
            conn.sendall(error)