from socket import *
import time
import csv

# Address of device we are communicating with (must match Teensy address/port)
address = ('192.168.1.101', 8888)
client_socket = socket(AF_INET, SOCK_DGRAM)  # Set up the socket
client_socket.settimeout(1)  # Wait 1 second for a response

# Message is 3 bytes (24 bits)
message = []
byte_message = bytearray()
# Function to convert the CSV to a byte array (3 bytes)
# Byte 1: MOTE ID
# Byte 2: Pin Number
# Byte 3: Config Byte


# Function to convert the CSV file to the bytearray to send
# ERROR: Something about using Pin 9 in CSV causes error in bytearray conversion
def converttobytearray():
    with open('example_config.csv') as config:
        readCSV = csv.reader(config, delimiter=',')
        next(readCSV, None)
        for row in readCSV:
            message = [0, 0, 0]
            message[0] = int(row[0])
            message[1] = int(row[1])
            if row[2] == "S":
                message[2] |= int('00000000', 2)
            elif row[2] == "A":
                message[2] |= int('10000000', 2)

            if row[3] == "TeensyACD":
                message[2] |= int('00000001', 2)
            elif row[3] == "i2c_ADC_1ch":
                message[2] |= int('00000010', 2)
            elif row[3] == "i2c_ADC_2ch":
                message[2] |= int('00000011', 2)
            elif row[3] == "FlowMeterCounter":
                message[2] |= int('00000100', 2)
            elif row[3] == "servoPWM":
                message[2] |= int('00000101', 2)
            elif row[3] == "BinaryGPIO":
                message[2] |= int('00000110', 2)
            byte_message = bytearray(message)
            print(message)
            print(byte_message)
            sendUDPPacket(byte_message)


# Function to send the bytearray over UDP
def sendUDPPacket(message):
    client_socket.sendto(message, address)
    try:
        rec_data, addr = client_socket.recvfrom(2048)
        print(rec_data)
    except:
        pass
    time.sleep(2)


converttobytearray()
