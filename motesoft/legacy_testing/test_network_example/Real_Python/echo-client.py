import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

# AF_INET designate type of address: IPV4 addr (safest option)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, world') #
    data = s.recv(1024) # receive message from server

print('Received', repr(data))

# send returns number of bytes sent (doesn't gurantee full send)
# sendall gurantees all bytes sent otherwise an exception