import socket
import socketserver
import threading
from threading import Thread

HOST, PORT = "0.0.0.0", 8888
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def telemetry_reciever():
    print("Started telemetry thread")
    HOST, PORT = "0.0.0.0", 8888
    with socketserver.UDPServer((HOST, PORT), generate_handler()) as server:
        server.serve_forever()

def start_telemetry_thread():
    telemetry_thread = Thread(target=telemetry_reciever, daemon=True)
    telemetry_thread.start()

def generate_handler():
    class TelemetryRecieveHandler(socketserver.BaseRequestHandler):
        def handle(self):
            packet_data = self.request
            mote_id = self.client_address[0][-1]
            data_list = convert_to_values(packet_data, mote_id)

    return TelemetryRecieveHandler

def convert_to_values(packet, mote_id):
    data = packet[0]
    parsed_data = []
    for i in range(len(data)//5):
        pin_num = data[5*i]
        value = int.from_bytes(data[5*i+1:5*i+5], byteorder='little', signed=True) # Tim did not have signed parameter in his networking code
        parsed_data.append({'Mote id': mote_id, 'Pin': pin_num, 'Value': value})
    return parsed_data

sock.bind((HOST, PORT))
while True:
    data, address = sock.recvfrom(1024)
    print("received message: %s from %s" % (data, address))