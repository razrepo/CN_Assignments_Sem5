q3.pyimport socket
import sys


serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(("0.0.0.0", 10403))
serverSocket.listen(1)

while True:
    print("SERVER IS RUNNING")
    connectionSocket, addr = serverSocket.accept()

    try:
        message = connectionSocket.recv(1024).decode()

        if len(message.split()) > 1:
            filename = message.split()[1]
            try:
                f = open(filename[1:])
                outputdata = f.read()

                connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
                connectionSocket.send("Content-Type: text/html\r\n\r\n".encode())

                connectionSocket.sendall(outputdata.encode())

            except IOError:
                f = open("404.html")
                outputdata = f.read()

                connectionSocket.send("HTTP/1.1 404 Not Found\r\n".encode())
                connectionSocket.send("Content-Type: text/html\r\n\r\n".encode())
                connectionSocket.sendall(outputdata.encode())
        else:
            # If the message is invalid, ignore it or handle it gracefully
            print("Invalid HTTP request received.")

    except Exception as e:
        print(f"Error: {e}")

    connectionSocket.close()
serverSocket.close()
sys.exit()
