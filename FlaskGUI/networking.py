import socket
import socketserver
import time
import threading
from threading import Thread

import configuration


num_motes = 4
mote_status = []

sensor_dictionary = {'1, 99': 'FireX'}
most_recent_data_packet = []

# Sending config and actuator commands
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

def get_mote_status(num):
    return mote_status[num - 1]

def get_ip(mote_id=None):
    if mote_id == None:
        return '127.0.0.1'
    return '192.168.1.' + str(100 + (int(mote_id)))

def send_actuator_command(mote_id, pin_num, state, interface_type='Binary GPIO'):
    if interface_type != 'Heartbeat':
        print(f"Sending {state} command to pin {pin_num} on MoTE {mote_id}, via {interface_type}")
    if interface_type == 'servoPWM_12V':
            #the GPIO pin we connect to is equal to the 5V the servo is "connected" to + 28
            #send_actuator_command(mote_id, 22, True)
            pass
    actuator_write_command = 0b10000000
    actuator_state_mask = 0b01000000 if state else 0
    interface_type_number = configuration.get_interface_type_number(
        interface_type) & 0b00111111
    config_byte = actuator_write_command | actuator_state_mask | interface_type_number
    ip = get_ip(mote_id=mote_id)
    #for _ in range(3):
    sock.sendto(bytes([int(pin_num), config_byte]), (ip, 8888))

def send_heartbeat():
    while True:
        # send 3 UDP packets for redundancy
        send_actuator_command(1, 100, True, interface_type='Heartbeat')
        send_actuator_command(2, 100, True, interface_type='Heartbeat')
        send_actuator_command(3, 100, True, interface_type='Heartbeat')
        #print("sending hearbeat")S
        time.sleep(2.5)

heartbeat_thread = Thread(target=send_heartbeat, daemon=True)

def send_config_to_mote(sensor_list, actuator_list):
    global sensor_dictionary
    sensor_dictionary.update(create_sensor_dictionary(sensor_list))
    sensors_and_actuators_list = sensor_list + actuator_list
    print("sent sensor config data to mote")
    for m in range(1, 4):
        reset_command = bytearray(2)
        reset_command[0] = 0
        reset_command[1] |= 0b00000000
        reset_command[1] |= 0b00111111 & configuration.get_interface_type_number('Clear_Config')

        sock.sendto(reset_command, (get_ip(m), 8888))

        try:
            heartbeat_thread.start()
        except:
            print("heartbeat thread already started")

    print (sensors_and_actuators_list)
    for sensor in sensors_and_actuators_list:
        #skip labjacks
        if int(sensor['Mote id']) >= 10:
            continue

        ip = get_ip(sensor['Mote id'])  # '192.168.2.'+sensor['Mote id']

        # See Readme for explenation of config_command
        config_command = bytearray(2)  # 2 byte byte array
        config_command[0] = int(sensor['Pin'])  # set first byte

        # set this to 0b10000000 for actuator write command
        config_command[1] |= 0b00000000
        config_command[1] |= 0b00111111 & configuration.get_interface_type_number(
            sensor['Interface Type'])

        sock.sendto(config_command, (ip, 8888))
        time.sleep(0.1)

def send_abort_request_to_mote():
    # TODO
    return

def send_cancel_request_to_mote():
    # TODO
    return

def send_launch_request_to_mote():
    # TODO
    return

def generate_handler():
    class TelemetryRecieveHandler(socketserver.BaseRequestHandler):
        def handle(self):
            data = self.request
            mote_id = self.client_address[0][-1]
            data_to_send_to_frontend = convert_to_values(data, mote_id)

            global sensor_dictionary
            global most_recent_data_packet

            parsed_data = []

            for data in data_to_send_to_frontend:

                sensor_name = sensor_dictionary[str(data["Mote id"]) + ", " + str(data["Pin"])]
                sensor_value = data['Value']

                if (sensor_name == 'FireX'):
                    #print('FireX status received')
                    pass
                else:
                    sensor_value_pair = (sensor_name, sensor_value)
                    parsed_data.append(sensor_value_pair)

            most_recent_data_packet = parsed_data

    return TelemetryRecieveHandler

def telemetry_reciever():
    #IP Adresses for HOST
    #Tim's Laptop: 192.168.1.106
    #TESTOP 1: 192.168.1.115
    HOST, PORT = "0.0.0.0", 8888
    with socketserver.UDPServer((HOST, PORT), generate_handler()) as server:
        server.serve_forever()

def start_telemetry_thread():
    telemetry_thread = Thread(target=telemetry_reciever, daemon=True)
    telemetry_thread.start()


def convert_to_values(packet, mote_id):
    data = packet[0]
    parsed_data = []

    if mote_id == '9':
        print("data =", data)

    for i in range(len(data)//5):
        pin_num = data[5*i]
        value = int.from_bytes(data[5*i+1:5*i+5], byteorder='little')
        parsed_data.append({'Mote id': mote_id, 'Pin': pin_num, 'Value': value})
    return parsed_data

def create_sensor_dictionary(sensor_list):
    dict = {}
    for sensor in sensor_list:
        dict[sensor["Mote id"] + ", " + sensor["Pin"]] = sensor["P and ID"]
    return dict

def get_sensor_data():
    global most_recent_data_packet
    return most_recent_data_packet
