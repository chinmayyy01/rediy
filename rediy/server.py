import os
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
            "DELETE": self.delete,
            "MGET": self.mget,
            "MSET": self.mset,
            "FLUSH": self.flush
        }
        self.aof_file = "appendonly.aof"
        self.aof_handle = open(self.aof_file, "ab")
        self.load_aof()
        self.store_lock = threading.Lock()
        self.aof_lock = threading.Lock()
        self.commands["REWRITE"] = self.rewrite_command
        
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(1)
        
        print(f"Server started on {self.host}:{self.port}")

        try:
            while True:
                try:
                    conn, addr = self.server_socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("Shutting down server...")
            self.aof_handle.close()
            self.server_socket.close()

    def handle_client(self, conn, addr):
        stream = conn.makefile("rb")
        try:
            while True:
                message = self.protocol.parse(stream)
                
                if not isinstance(message, list):
                    message = [message]
                    
                command_name = message[0].upper()
                
                if command_name not in self.commands:
                    conn.sendall(b"-ERR unknown command\r\n")
                    continue
                
                try:
                    result = self.commands[command_name](*message[1:])
                    if command_name in ["SET", "DELETE", "MSET", "FLUSH"]:
                        self.append_to_aof(message)
                    self.send_response(conn, result)
                except Exception as e:
                    error = f"-ERR {str(e)}\r\n"
                    conn.sendall(error)
                
        except ConnectionError:
            pass
        finally:
            stream.close()
            conn.close()
            
    def load_aof(self):
        try:
            with open(self.aof_file, "rb+") as f:
                last_valid_pos = 0
                while True:
                    try:
                        last_valid_pos = f.tell()
                        command = self.protocol.parse(f)
                    except Exception as e:
                        print("Detected corrupted AOF file, truncating to last valid position")
                        f.truncate(last_valid_pos)
                        break
                    if isinstance(command, list):
                        cmd = command[0].upper()
                        with self.store_lock:
                            if cmd in self.commands:
                                self.commands[cmd](*command[1:])
        except FileNotFoundError:
            pass
    
    def append_to_aof(self, command):
        with self.aof_lock:
            f = self.aof_handle
            f.write(f"*{len(command)}\r\n".encode())
            for item in command:
                encoded = item.encode()
                f.write(f"${len(encoded)}\r\n".encode())
                f.write(encoded + b"\r\n")       
            f.flush() 
         
    def get(self, key):
        return self.store.get(key, None)
    def set(self, key, value):
        with self.store_lock:
            self.store[key] = value
        return "OK"
    def delete(self, key):
        with self.store_lock:
            if key in self.store:
                del self.store[key]
                return 1
            return 0
    def mget(self, *keys):
        return [self.store.get(key, None) for key in keys]
    def mset(self, *items):
        if len(items) % 2 != 0:
            raise Exception("MSET requires an even number of arguments")
        with self.store_lock:
            for i in range(0, len(items), 2):
                key = items[i]
                value = items[i + 1]
                self.store[key] = value
        return "OK"
    def flush(self):
        with self.store_lock:
            count = len(self.store)
            self.store.clear()
        return count
        
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
        elif isinstance(data, list):
            conn.sendall(f"*{len(data)}\r\n".encode())
            for item in data:
                self.send_response(conn, item)
        else:
            error = f"-ERR unsupported response type\r\n"
            conn.sendall(error)
            
    def rewrite_aof(self):
        temp_file = "appendonly.tmp"
        with open(temp_file, "wb") as f:
            with self.store_lock:
                for key, value in self.store.items():
                    command = ["SET", key, value]
                    f.write(f"*{len(command)}\r\n".encode())
                    for item in command:
                        encoded = item.encode()
                        f.write(f"${len(encoded)}\r\n".encode())
                        f.write(encoded + b"\r\n")
        self.aof_handle.close()
        os.replace(temp_file, self.aof_file)
        self.aof_handle = open(self.aof_file, "ab")
        
    def rewrite_command(self):
        self.rewrite_aof()
        return "OK"