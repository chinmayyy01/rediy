import socket
import threading


class Server:
    def __init__(self, host="127.0.0.1", port=6379):
        self.host = host
        self.port = port

        # Create a TCP socket
        self.server_socket = socket.socket(
            socket.AF_INET,     # IPv4
            socket.SOCK_STREAM  # TCP
        )

    def start(self):
        # Bind to address
        self.server_socket.bind((self.host, self.port))

        # Start listening
        self.server_socket.listen()

        print(f"Server started on {self.host}:{self.port}")

        while True:
            # Accept new client connection
            conn, addr = self.server_socket.accept()
            print(f"Connection from {addr}")

            # Create new thread for each client
            thread = threading.Thread(
                target=self.handle_client,
                args=(conn, addr),
                daemon=True
            )
            thread.start()

    def handle_client(self, conn, addr):
        try:
            while True:
                # Receive data (bytes!)
                data = conn.recv(1024)

                if not data:
                    break

                print(f"Received from {addr}: {data}")

                # Send response
                conn.sendall(b"OK\n")

        finally:
            print(f"Closing connection from {addr}")
            conn.close()