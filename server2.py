import socket
import sys
import threading
import time


def handleClient(connectionSocket):
    try:
        message = connectionSocket.recv(1024).decode()

        # Check if the message is valid
        parts = message.split()
        if len(parts) < 2:
            print("Malformed request received")
            connectionSocket.send("HTTP/1.1 400 Bad Request\r\n".encode())
            connectionSocket.send("Content-Type: text/html\r\n\r\n".encode())
            connectionSocket.send(
                "<html><body><h1>400 Bad Request</h1></body></html>".encode()
            )
            return

        filename = parts[1]

        # Attempt to open and read the requested file
        try:
            with open(filename[1:], "r") as f:  # Skip the leading '/'
                outputdata = f.read()

            connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
            connectionSocket.send("Content-Type: text/html\r\n\r\n".encode())
            connectionSocket.sendall(outputdata.encode())

        except IOError:
            # If the file is not found, send a 404 response
            try:
                with open("404.html") as f:
                    outputdata = f.read()
                connectionSocket.send("HTTP/1.1 404 Not Found\r\n".encode())
                connectionSocket.send("Content-Type: text/html\r\n\r\n".encode())
                connectionSocket.sendall(outputdata.encode())
            except IOError:
                # If 404.html is also not found
                connectionSocket.send("HTTP/1.1 500 Internal Server Error\r\n".encode())
                connectionSocket.send("Content-Type: text/html\r\n\r\n".encode())
                connectionSocket.send(
                    "<html><body><h1>500 Internal Server Error</h1></body></html>".encode()
                )

    finally:
        connectionSocket.close()


serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(("0.0.0.0", 10403))
serverSocket.listen(1)

while True:
    print("SERVER IS RUNNING")
    connectionSocket, addr = serverSocket.accept()
    new_thread = threading.Thread(target=handleClient, args=(connectionSocket,))
    new_thread.start()
serverSocket.close()
sys.exit()
