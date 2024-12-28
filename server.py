import random
import socket
import time

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("localhost", 10404))

while True:
    print("SERVER IS RUNNING")
    message, address = server_socket.recvfrom(1024)
    rand = random.randint(0, 10)
    loss = rand < 4
    if not loss:
        recieve_time = time.time()
        ping_number, sent_time = message.decode().split()[1:]
        sent_time = float(sent_time)

        time_difference = recieve_time - sent_time

        res_msg = f"Ping {ping_number} is recieved in {time_difference : .4f} sec"
        server_socket.sendto(res_msg.encode(), address)
