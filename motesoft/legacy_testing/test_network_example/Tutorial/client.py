import socket               # Import socket module

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name (Jennas-MacBook-Air.local)
                            # Can be ip address: '127.0.0.1'
port = 12345                # Reserve a port for your service. (can be any number)

s.connect((host, port))
print (s.recv(1024))        # only receiving data from server
s.close()                     # Close the socket when done