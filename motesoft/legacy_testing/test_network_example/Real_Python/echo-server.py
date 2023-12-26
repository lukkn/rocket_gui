#!/usr/bin/env python3

import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

# with statements used for resource management and exception handling 
# if creation of socket object is sucessful, execute below code block otherwise return exception
# also closes socket object
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()

    #with statements also closes the connection
    with conn:
        print('Connected by', addr)
        while True:
            #data is a bytes object and recv takes number of bytes
            data = conn.recv(1024)
            if not data: #data has second argument as number of bytes, if not 0, break
                break
            conn.sendall(data)

# socket is file thus needs  to be closed with socket.close()
# conn is a new socket object created by socket.accept()
# conn also needs to be closed