import socket
import time

# this server needs to sned msg firs (send msg first so client can respond)
# if client is reloaded (sets up connection first), server must be reloaded
def run_server(IP, PORT, msg):

    time_str = str(time.ctime(time.time()))
    msg = msg + time_str
    # print(len(msg))
    data = bytes(msg, 'utf-8')
    addressPort= (IP, PORT) #define server IP and port

    with socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM) as s:
        s.sendto(data, addressPort) #Send the data request
        data2, addr = s.recvfrom(2048) #Read response from arduino
        print (data2)

    
# s.settimeout(1) #Only wait 1 second for a response# time.sleep(2) #delay before sending next command
if __name__ == "__main__":
    HOST = "192.168.0.36"
    PORT = 5000
    counter = 0

    start_time = time.time()
    while(counter < 500):
        msg = "MSG "+ str(counter) + ": Hello World"

        run_server(HOST, PORT, msg)
        # time.sleep(0.01) #100hz or 1/100 sec
        counter+=1
    elapsed_time = time.time() - start_time
    print(elapsed_time)
