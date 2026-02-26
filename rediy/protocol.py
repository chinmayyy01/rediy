class ProtocolError(Exception):
    pass

class ProtocolHandler:
    def read_line(self, conn):
        buffer = b""
        while not buffer.endswith(b"\r\n"):
            chunk = conn.recv(1)
            if not chunk:
                raise ConnectionError("Client Disconnected")
            buffer+=chunk
        return buffer[:-2]
    
    def parse(self, conn):
        first_byte = conn.recv(1)
        if not first_byte:
            raise ConnectionError("Client Disconnected")
        if first_byte == b"+":
            return self.read_line(conn).decode()
        elif first_byte == b"$":
            length = int(self.read_line(conn))
            if length == -1:
                return None
            data=b""
            while len(data) < length:
                data += conn.recv(length - len(data))
            conn.recv(2)  # Consume the trailing \r\n
            return data.decode()
        elif first_byte == b"*":
            count = int(self.read_line(conn))
            return [self.parse(conn) for _ in range(count)]
        else:
            raise ProtocolError("Unknown protocol type")