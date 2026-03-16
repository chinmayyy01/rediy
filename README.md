# Rediy v2.0

Rediy is a minimal Redis like key value store built from scratch in Python.

It implements both a threaded TCP server and an asyncio based event driven server, RESP protocol parsing, command dispatching, append only file persistence, TTL expiration, runtime observability commands, and a benchmarking tool.

The goal of this project is to deeply understand how Redis works internally starting from network communication and protocol parsing all the way to persistence, concurrency models, and system performance analysis.

---

## Project Structure

```
rediy/
│
├── rediy/
│   ├── server.py
│   ├── async_server.py
│   └── protocol.py
│
├── main.py
├── benchmark.py
├── README.md
└── .gitignore
```

---

## Installation and Setup

Clone the repository

```
git clone https://github.com/chinmayyy01/rediy.git
cd rediy
```

Create virtual environment

```
python -m venv venv
```

Activate environment

Windows

```
venv\Scripts\activate
```

Linux or macOS

```
source venv/bin/activate
```

No external dependencies are required.

---

## Run the Server

Threaded server

```
python main.py threaded
```

Async server

```
python main.py async
```

Server starts on

```
127.0.0.1:6379
```

---

## Manual Testing Using Python Socket

Open another terminal

```
python
```

Then run

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

# PING
s.sendall(b"*1\r\n$4\r\nPING\r\n")
print(s.recv(1024))
```

---

## Benchmark

A benchmarking tool is included to measure throughput under concurrent load.

Run the benchmark

```
python benchmark.py
```

Example benchmark results observed during testing

```
40000 requests      about 16000 to 17000 operations per second
200000 requests     about 17000 to 19000 operations per second
500000 requests     about 12000 operations per second
```

The benchmark simulates multiple concurrent clients sending RESP commands to the server and measures total execution time and throughput.

This allows comparison between the threaded server and the asyncio event driven server architectures.

---

## Persistence Using Append Only File

Rediy uses append only file persistence.

All write commands are logged to

```
appendonly.aof
```

On restart the server replays the file to rebuild memory.

To test persistence

```
python main.py threaded
```

Write some keys

Stop the server

Restart the server

Data will still exist.

The system also supports AOF rewrite to compact the log and reduce startup replay time.

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

## Features (v2)

- TCP server using threading  
- Async TCP server using asyncio event loop  
- RESP protocol parsing and serialization  
- Command dispatcher  
- In memory key value store  
- GET SET DELETE  
- MGET MSET  
- FLUSH  
- TTL support using EX argument in SET  
- Background expiration cleanup  
- Append only file persistence  
- Replay on startup  
- AOF rewrite for log compaction  
- PING command  
- DBSIZE command  
- INFO command exposing runtime statistics  
- Benchmark tool for throughput testing  
- Threaded versus async architecture comparison  

Rediy v2 behaves like a small Redis style database capable of handling concurrent client requests while exposing runtime information about the system.

---

## How It Works

Rediy is built in layers

Transport Layer  
TCP socket server supporting both threaded and async concurrency models.

Protocol Layer  
RESP parser and serializer implementing Redis compatible wire format.

Command Layer  
Command dispatcher executing database operations.

Storage Layer  
Python dictionary storing key value pairs and expiration metadata.

Persistence Layer  
Append only file logging with replay on startup and rewrite for log compaction.

Execution flow

Client sends RESP command  
Server parses command  
Dispatcher executes database operation  
Result serialized into RESP response  
Write commands appended to AOF log  
Server responds to client