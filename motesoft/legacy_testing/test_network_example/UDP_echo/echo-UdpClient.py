import socket
 
def run_client(HOST, PORT):

    data = b'Hello World'
    
    serverAddrPort = ("127.0.0.1", 20001)
    
    # conncting to hosts
    with socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM) as s:
        
        # sending username by encoding it
        print("///Sending Client data:", data)
        s.sendto(data, serverAddrPort) 

        # receiving status from server
        data2, addr = s.recvfrom(1024)
        print("///Received back Server data:", repr(data2))

    #repr() pass eval function to return string representation of data

if __name__ == "__main__":
    HOST = "127.0.0.1"
    PORT = 20001
    run_client(HOST, PORT)