# Rediy v1.0

Rediy is a minimal Redis-like key-value store built from scratch in Python.

It implements a threaded TCP server, RESP protocol parsing, command dispatching, and append-only file (AOF) persistence.

This project was built to deeply understand how Redis works internally — from network layer to persistence layer.

---

## Features (v1)

- TCP server using threading
- RESP protocol parsing
- Command dispatcher
- In-memory key-value store
- GET / SET / DELETE
- MGET / MSET
- FLUSH
- Proper RESP array and bulk string serialization
- Append-only file (AOF) persistence
- Replay on startup
- Graceful shutdown handling

Rediy v1 behaves like a minimal persistent Redis clone.

---

## Project Structure

```
rediy/
│
├── rediy/
│   ├── __init__.py
│   ├── server.py
│   └── protocol.py
│
├── main.py
├── README.md
└── .gitignore
```

---

## Installation & Setup

Clone the repository:

```bash
git clone https://github.com/yourusername/rediy.git
cd rediy
```

Create virtual environment:

```bash
python -m venv venv
```

Activate environment:

**Windows**
```bash
venv\Scripts\activate
```

**Linux / macOS**
```bash
source venv/bin/activate
```

No external dependencies are required.

---

## Run the Server

```bash
python main.py
```

Server will start on:

```
127.0.0.1:6379
```

---

## Manual Testing (Using Python Socket)

Open another terminal:

```bash
python
```

Then:

```python
import socket
s = socket.socket()
s.connect(("127.0.0.1", 6379))

# SET
s.sendall(b"*3\r\n$3\r\nSET\r\n$1\r\na\r\n$3\r\n100\r\n")
print(s.recv(1024))

# GET
s.sendall(b"*2\r\n$3\r\nGET\r\n$1\r\na\r\n")
print(s.recv(1024))
```

---

## Persistence (AOF)

Rediy uses append-only file persistence.

All write commands are logged to:

```
appendonly.aof
```

On restart, the server replays the file to rebuild memory.

To test persistence:

```bash
python main.py
```

Write some keys.

Stop server.

Restart server.

Data will still exist.

---

## How It Works

Rediy is built in layers:

- Transport Layer (TCP socket server)
- Protocol Layer (RESP parser)
- Command Layer (GET, SET, etc.)
- Storage Layer (Python dictionary)
- Persistence Layer (Append-only file logging)

On every write command:
- Execute command
- Append command to AOF

On startup:
- Read AOF
- Replay commands
- Restore state

---