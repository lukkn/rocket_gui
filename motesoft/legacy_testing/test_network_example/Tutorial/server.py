import socket               # Import socket module

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 12345                # Reserve a port for your service.
s.bind((host, port))        # Bind to the port

# argument of listen is default = 0 but 5 is number of unaccepted connections allowed before closing
s.listen(5)                 # Now wait for client connection.

# will run continuously: accepting, sending message, and closing ()
while True:
   c, addr = s.accept()     # Establish connection with client.
   print ('Got connection from', addr)
   # needs to be sent in bytes
   c.send(b'Thank you for connecting') #only sending data to client, not receiving
   c.close()                # Close the connection