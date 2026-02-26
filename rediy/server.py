import socket
import threading
from rediy.protocol import ProtocolHandler

class Server:
    def __init__(self, host="127.0.0.1", port=6379):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.protocol = ProtocolHandler()
        
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
                print(f"Parsed: {message}")
                response = f"+You sent: {message}\r\n"
                conn.sendall(response.encode())
                
        except ConnectionError:
            print("Client disconnected")

        finally:
            print(f"Closing connection from {addr}")
            conn.close()