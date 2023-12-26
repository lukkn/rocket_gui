from setting import *

class client_object:
   def __init__(self, HOST, PORT, ID, RANGE):
      self.HOST = HOST
      self.PORT = PORT
      self.ID = ID
      self.RANGE = RANGE

   def send_data(self):
       #randomly create measurements from range
       val = random.uniform(self.RANGE[0], self.RANGE[1])
       concat_val = round(val, 2)
       run_client(self.HOST, self.PORT, self.ID, concat_val)
      

def run_client(HOST, PORT, ID, val = 0):

    msg = 'Hello World, I am Client ' + str(ID) + "! "
    data = "Data Measured: " + str(val)
    msg += data
    data = msg.encode()
    
    serverAddrPort = ("127.0.0.1", 20001)
    
    # conncting to hosts
    with socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM) as s:
        print(str(time.ctime(time.time())))
        # sending username by encoding it
        print("@->@Sending Client data:", data)
        s.sendto(data, serverAddrPort) 

        # receiving status from server
        data2, addr = s.recvfrom(1024)
        print("@<-@Received back Server data:", repr(data2))

    #repr() pass eval function to return string representation of data

if __name__ == "__main__":
    Client_IDS = [1, 2, 3]

    clients_object_list = list()

    #imaginery ranges for data generation 
    temperature = (-30, 100)
    speed = (0, 160)
    pressure = (0, 1)

    Ranges = [temperature, speed, pressure]

    #creation of client objects
    for index in range(3):
        clients_object_list.append(client_object (CLIENT_IPS[index], CLIENT_PORT[index], Client_IDS[index], Ranges[index]))

    threads = list() ##returns a list

    #creation of threads
    for index in range(3):
        logging.info("===Main: create and start thread %d.===", index)
        x = threading.Thread(target=clients_object_list[index].send_data(), args=())
        threads.append(x)
        x.start()

    # waiting till all threads are done sending and receiving data
    for index, thread in enumerate(threads):
        logging.info("===Main: before joining thread %d.===", index)
        thread.join()
        logging.info("===Main: thread %d done===", index)

    print("===Main: all threads done===")

# no need for priority queue
# advantages of thread is running them concurrently
#https://www.tutorialspoint.com/python/python_multithreading.htm
#https://realpython.com/intro-to-python-threading/#working-with-many-threads
#https://realpython.com/python-sockets/#handling-multiple-connections
