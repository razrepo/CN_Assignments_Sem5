import socket
import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(1)

server_address = ('localhost',10404)

serverIs = True
lost = 0
recieved = 0
i = 0

while(serverIs):
    i = i + 1
    send_time = time.time()
    message = f"Ping no.:{i} {send_time}"
    client_socket.sendto(message.encode(), server_address)
    try:
        response, _ = client_socket.recvfrom(1024)
        recieve_time = time.time()
        recieved += 1
        print(f"Response:- {response.decode()}")
        print(f"RTT: {(recieve_time - send_time) *1000 : .8f} ms")
        lost = 0
    except socket.timeout:
        print("Request timed out")
        lost +=1
        if (lost == 3):
            serverIs = False
print("SERVER IS CLOSED")