import socket

def send_clientData (ip, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(data, (ip, port))
        print("Sent: {}".format(data))
        received = str(sock.recv(1024), "UTF-8")
        print("Received: {}".format(received))

if __name__ == "__main__":
    HOST = "localhost"
    PORT = 20001

    data1 = b"client 1: Hello World this is threaded UDP 1"
    data2 = b"client 1: Hello World this is threaded UDP 2"
    data3 = b"client 1: Hello World this is threaded UDP 3"

    send_clientData(HOST, PORT, data1)
    send_clientData(HOST, PORT, data2)
    send_clientData(HOST, PORT, data3)

    
