import sys
import random
import errno
import time
import socket
import socketserver

def sensor_pin_to_i2c(pin_num):
    #1ch I2C = (adress, pin_num) : [42, 62)
    #2ch I2C = (adress, pin1_num, pin2_num) : [62, 82)
    #flowmeters -- special case
    
    if (pin_num >= 42 and pin_num < 62):
        return ((64 + pin_num - 42), (pin_num - 42)%4)
    elif (pin_num >= 62 and pin_num < 82):
        return ((64 + pin_num - 42), (pin_num - 42)%4, (pin_num - 42)%4 + 1)
    else:
        print('Error. Interface number is not valid', pin_num)
   
def handle_command_from_server(data):  # data supposed to be 2 bytes long
    if len(data) != 2:  # incomplete command packet
        print('packet too small')
        return
    pin_num = data[0]
    config_byte = data[1]
    actuator_write_command = config_byte & 0b10000000 == 0b10000000
    actuator_state = config_byte & 0b01000000 == 0b01000000
    interface_type_number = config_byte & 0b00111111
    if actuator_write_command:
        print(
            f'Setting pin {pin_num} to {actuator_state} with interface {get_interface_name_from_number(interface_type_number)}')
        return None
    else:  # if config command
        if get_interface_name_from_number(interface_type_number) != 'FlowMeterCounter':
            #is an I2C ADC
            i2c_pin_num = sensor_pin_to_i2c(pin_num)
        print(
            f'Sensor config command: pin {pin_num} can be read using interface {get_interface_name_from_number(interface_type_number)}')
        #the dicts in sensors should never have more than 2 elements!!!
        return {'pin_num': pin_num, 'interface_type_number': interface_type_number}


def get_interface_name_from_number(number):
    if number == 1:
        return 'Teensy ADC'
    elif number == 2:
        return 'i2c ADC 1ch'
    elif number == 3:
        return 'i2c ADC 2ch'
    elif number == 4:
        return 'FlowMeterCounter'
    elif number == 5:
        return 'servoPWM'
    elif number == 6:
        return 'Binary GPIO'
    else:
        print('Error. Interface number is not valid', number)


#HOST, PORT = "localhost", 5006
# with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
#	server.serve_forever()

print("fakeMote initialized")

UDP_IP = "127.0.0.1"
UDP_PORT = 5006

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(0)

sensors = []

while True:
    try:
        data, addr = sock.recvfrom(2)
    except socket.error as e:  # check if no message recieved, or actual error
        err = e.args[0]
        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            # FIXME in real Teensy, this would not be here. loop as fast as possible
            time.sleep(.2)
            #print('No data available')
            # continue
        else:
            # a "real" error occurred
            print(e)
            sys.exit(-1)
    else:
        # got a message, do something
        sensor_config = handle_command_from_server(data)
        #print(sensor_config)
        if sensor_config:
            print("recieved sensor config info")
            sensors.append(sensor_config)
            sensor_config = handle_command_from_server(data)
    telemetry_to_send = bytearray(5*len(sensors))
    for i, sensor in enumerate(sensors):
        sensor_reading = random.randint(0, 100)
        telemetry_to_send[5*i] = sensor['pin_num']
        telemetry_to_send[5*i+1:5*i +
                          5] = sensor_reading.to_bytes(4, byteorder='big')
    # print(telemetry_to_send)
    sock.sendto(telemetry_to_send, ('localhost', 5008))
