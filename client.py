import socket
import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(1)

server_address = ('localhost',10404)

RTT_time = []
number_of_pings = 10
recieved = 0

for i in range(number_of_pings):
    
    send_time = time.time()
    message = f"Ping no.:{i + 1} {send_time}"

    client_socket.sendto(message.encode(), server_address)

    try:
        response, _ = client_socket.recvfrom(1024)
        recieve_time = time.time()
        RTT_time.append(recieve_time - send_time)
        recieved += 1

        print(f"Response:- {response.decode()}")
        print(f"RTT: {(recieve_time - send_time) *1000 : .8f} ms")
    
    except socket.timeout:
        print("Request timed out")

if RTT_time:
    average_RTT = sum(RTT_time) / len(RTT_time)
    min_RTT = min(RTT_time)
    max_RTT = max(RTT_time) 
else:
    average_RTT = 0
    min_RTT = max_RTT = 0

packet_loss_rate = ((number_of_pings - recieved) / number_of_pings) * 100

print(f"MinRTT: {min_RTT *1000:.8f} ms")
print(f"MaxRTT: {max_RTT * 1000:.8f} ms")
print(f"AvgRTT: {average_RTT * 1000:.8f} ms")
print(f"packet loss: {packet_loss_rate:.8f} %")