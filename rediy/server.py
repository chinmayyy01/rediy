import os
import random
import time
import socket
import threading
from rediy.protocol import ProtocolError, ProtocolHandler

class Server:
    def __init__(self, host="127.0.0.1", port=6379):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.protocol = ProtocolHandler()
        self.store = {}
        self.expiry = {}
        self.store_lock = threading.Lock()
        self.aof_lock = threading.Lock()
        self.commands = {
            "GET": self.get,
            "SET": self.set,
            "DELETE": self.delete,
            "MGET": self.mget,
            "MSET": self.mset,
            "FLUSH": self.flush,
            "TTL": self.ttl
        }
        self.aof_file = "appendonly.aof"
        self.aof_handle = open(self.aof_file, "ab")
        self.load_aof()
        self.commands["REWRITE"] = self.rewrite_command
        
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(1)
        
        print(f"Server started on {self.host}:{self.port}")
        
        cleanup_thread = threading.Thread(target=self.cleanup_expired_keys, daemon=True)
        cleanup_thread.start()

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
                try:
                    message = self.protocol.parse(stream)
                except ProtocolError:
                    conn.sendall(b"-ERR protocol error\r\n")
                    continue
                except ConnectionError:
                    break
                
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
                    conn.sendall(error.encode())
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
        with self.store_lock:
            if key in self.expiry and time.time() > self.expiry[key]:
                self.store.pop(key, None)
                self.expiry.pop(key, None)
                return None
            return self.store.get(key, None)
    
    def set(self, key, value, *args):
        with self.store_lock:
            self.store[key] = value
            if len(args) == 2 and args[0].upper() == "EX":
                seconds = int(args[1])
                self.expiry[key] = time.time() + seconds
            else:
                if key in self.expiry:
                    self.expiry.pop(key, None)
        return "OK"
    
    def delete(self, key):
        with self.store_lock:
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
    
    def ttl(self, key):
        with self.store_lock:
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
            conn.sendall(error.encode())
            
    def rewrite_aof(self):
        temp_file = "appendonly.tmp"
        with open(temp_file, "wb") as f:
            with self.store_lock:
                for key, value in self.store.items():
                    command = ["SET", key, value]
                    f.write(f"*{len(command)}\r\n".encode())
                    for item in command:
                        encoded = str(item).encode()
                        f.write(f"${len(encoded)}\r\n".encode())
                        f.write(encoded + b"\r\n")
        self.aof_handle.close()
        os.replace(temp_file, self.aof_file)
        self.aof_handle = open(self.aof_file, "ab")
        
    def rewrite_command(self):
        self.rewrite_aof()
        return "OK"
    
    def cleanup_expired_keys(self):
        while True:
            time.sleep(5)
            with self.store_lock:
                if not self.expiry:
                    continue
                now = time.time()
                keys = list(self.expiry.keys())
                sample_size = min(20, len(keys))
                sampled = random.sample(keys, sample_size)
                expired_count = 0
                for key in sampled:
                    if now > self.expiry[key]:
                        self.store.pop(key, None)
                        self.expiry.pop(key, None)
                        expired_count += 1
                if expired_count > sample_size:
                    continue