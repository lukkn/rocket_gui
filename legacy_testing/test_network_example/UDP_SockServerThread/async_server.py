import threading
import socketserver
import time

#references: #socketserver: https://pymotw.com/3/socketserver/ (slightly outdated in 3.9.5)
#(outadated: self.request is tuple)
#https://docs.python.org/3/library/socketserver.html
#https://pythontic.com/socketserver/tcpserver/introduction
#https://www.bogotobogo.com/python/python_network_programming_socketserver_framework_for_network_servers.php

#has attributs: request, data, server and client_address(both are tuples)
# if override socketserver.streamrequesthandler
# self.rfile.readline().strip()
# self.wfile.write()

#self.request is a tuple: 
#request (tuple) : (1) (b'Hello World this is threaded UDP', 
# (2) <socket.socket fd=3, family=AddressFamily.AF_INET, type=SocketKind.SOCK_DGRAM, proto=0, laddr=('127.0.0.1', 20001)>)

#Request Handler has __init__(), setup(), handle(), finish()

#UDPClass has server_activate(), serve_forever(), handle_request(), 
# verify_request(), process_request(), server_close(), finish_request(), 
# close_request(), shutdown()
class ThreadedUDPHandler (socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip() #strips leading, trailing characters such as white 
        socket = self.request[1]
        print("{} wrote {}".format(self.client_address[0], data))
        socket.sendto(data.upper(), self.client_address)

#attribute wfile and rfile used to read and write content for client

#we will use socketserver.ThreadingMixin for threads
#for processes: socketserver.ForkingMixIn

# allows asynchronous requests (requests do not need to finish, can run multiple requests concurrently)
class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

if __name__ == "__main__":
    HOST = "127.0.0.1"
    PORT = 20001

    with socketserver.UDPServer((HOST, PORT), ThreadedUDPHandler) as UDPServer:
        thread_server = threading.Thread(target=UDPServer.serve_forever, daemon = True) #set object of UDPserver running forever #make it as a daemon (background)
        thread_server.start() #begin daemon thread
        thread_server.name = "UDP thread"
        try:
            while True: #make sure to keep running until ctrl-c (cannot t.join from client programs)
                time
                seconds = time.time()
                print("Seconds since epoch =", seconds)	
                for thread in threading.enumerate(): 
                    print(thread.name)
                time.sleep(5)
                for thread in threading.enumerate(): 
                    print(thread.name)
        except KeyboardInterrupt:
            print('interrupted!')
