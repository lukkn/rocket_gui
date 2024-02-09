import socket

def run_server(HOST, PORT):
    with socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))

        #doesn't include by listen() or accept()
        #no need to create a new socket
            
        while(True):
            # receiving name from client
            data, addr = s.recvfrom(1024) 
            print("### Data received Server:", data)
            # sending encoded status of name and pwd
            print("### Data sent back")

            s.sendto(data, addr) 

if __name__ == "__main__":
    HOST = "127.0.0.1"
    PORT = 20001
    run_server(HOST, PORT)