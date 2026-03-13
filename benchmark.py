import socket
import time
import threading

HOST = "127.0.0.1"
PORT = 6379

REQUESTS_PER_THREAD = 5000
THREADS = 100

def worker(thread_id, results):
    s = socket.socket()
    s.connect((HOST, PORT))
    start = time.time()
    for i in range(REQUESTS_PER_THREAD):
        key = f"k{i}".encode()
        cmd = b"*3\r\n$3\r\nSET\r\n$" + str(len(key)).encode() + b"\r\n" + key + b"\r\n$1\r\n1\r\n"
        s.sendall(cmd)
        s.recv(1024)
    end = time.time()
    s.close()
    results[thread_id] = end - start
    
def run_benchmark():
    threads = []
    results = {}
    start = time.time()
    for i in range(THREADS):
        t = threading.Thread(target=worker, args=(i, results))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    end = time.time()
    
    total_requests = REQUESTS_PER_THREAD * THREADS
    total_time = end - start
    rps = total_requests / total_time
    
    print("Total Requests:", total_requests)
    print("Total Time:", round(total_time, 2), "seconds")
    print("Requests per Second:", int(rps))
    
if __name__ == "__main__":
    run_benchmark()