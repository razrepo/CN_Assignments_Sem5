import socket
import sys

if len(sys.argv) != 4:
    print(
        "ERROR: Invalid arguments. Usage: client.py <server_host> <server_port> <filename>"
    )
    sys.exit()

server_host = sys.argv[1]
server_port = int(sys.argv[2])
filename = sys.argv[3]

try:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Set timeout for the client socket
    clientSocket.settimeout(10)

    # Try to connect to the server
    clientSocket.connect((server_host, server_port))

    # Prepare and send HTTP GET request
    request = f"GET /{filename} HTTP/1.1\r\nHost: {server_host}\r\n\r\n"
    clientSocket.send(request.encode())

    response = ""
    while True:
        try:
            # Receive data in chunks
            chunk = clientSocket.recv(4096).decode()
            if not chunk:  # No more data, break the loop
                break
            response += chunk  # Append received chunk to the full response
        except socket.timeout:
            print("ERROR: Timeout while waiting for the response.")
            break

    # Print the server's full response
    print("Server Response:\n")
    print(response)

except socket.timeout:
    print("ERROR: Connection timed out.")
except socket.error as e:
    print(f"ERROR: Socket error occurred: {e}")
except Exception as e:
    print(f"ERROR: An unexpected error occurred: {e}")
finally:
    # Ensure the socket is closed
    clientSocket.close()
