from cgitb import reset
from concurrent.futures import thread
import imp
import gui_class, gui
from operator import imod
import socket
import time
import threading
from threading import Thread
import socketserver
import unit_convert
import sensor_logging
import autoseq
import subprocess
import re

from gi.repository import GLib

import configuration
from configuration import get_interface_type_number
from configuration import load_config

actuators, sensors = load_config()

# Sending config and actuator commands
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

USE_FAKE_MOTE = False
SCALE_INTERN_TEMP = False

start_epoch = time.time()

num_motes = 4
mote_status = []

bangbang_status = [False, False]
firex_status =False

TIMEOUT_LIMIT = 1.5
last_mote_packet_time = start_epoch
for m in range(num_motes):
    mote_status.append(False)

aborted = False
def check_abort_setpoints():
    if not gui_class.setpoint_toggle_button.get_state():
        return
    
    for point in configuration.setpoints:
        val = sensor_logging.sensor_log_rolling_avg[point['ID']][0]
        if val is None or val == "None":
            return
        val = float(val)
        #print(val)
        if  val <= float(point['Min']) or val >= float(point['Max']):
                #print("OUT OF SAFE RANGE")
                for i in range(1, 4):
                    for seq in autoseq.autoseq_threads:
                        #print(seq)
                        if seq != None and i in seq[0] and not autoseq.abort_mutex.locked() and seq[2] == point['State']:
                            print(f"SETPOINT HIT {point['P and ID']} at {val}: ABORTING!!")
                            autoseq.abort_autoseq(None, autoseq.autoseq_threads.index(seq), actuators, abort_type="ABORT")

def mote_timeout(sensor_labels):
    while True:
        if (time.time() - TIMEOUT_LIMIT) > last_mote_packet_time:
            for i, m in enumerate(mote_status):
                mote_status[i] = False

                try:
                    for pin, switches in gui_class.actuator_switches[i + 1].items():
                        for s in switches:
                            GLib.idle_add(s.set_sensitive, False)
                        sensor_logging.actuator_acks[(i, pin)] = False
                        #switches[3].set_from_icon_name('gtk-no', 1)
                except:
                    print("error reseting ACK")
                
                #for seq in autoseq.autoseq_threads:
                #    if seq != None and i in seq[0]:
                #        autoseq.abort_autoseq(None, autoseq.autoseq_threads.index(seq), actuators)
                #        print("Disconnect. Aborting relevant autoseq")

                for s in sensor_logging.sensor_log_values.keys():
                    sensor_logging.sensor_log_values[s] = "None"
                    sensor_logging.sensor_log_rolling_avg[s][0] = "None"
                for label_key in sensor_labels.keys():
                    if int(label_key[0]) < 10:
                        GLib.idle_add(sensor_labels[label_key].set_text, str("NO CONNECTION"))
                
            #print(mote_status)
        time.sleep(TIMEOUT_LIMIT/2)

def get_mote_status(num):
    return mote_status[num - 1] 

def get_ip(mote_id=None):
    if mote_id == None or USE_FAKE_MOTE:
        return '127.0.0.1'
    return '192.168.1.' + str(100 + (int(mote_id)))

def send_config_to_mote(sensors):
    print("sent sensor config data to mote")
    print(sensors)

    for m in range(1, 4):
        reset_command = bytearray(2) 
        reset_command[0] = 0
        reset_command[1] |= 0b00000000
        reset_command[1] |= 0b00111111 & get_interface_type_number('Clear_Config')

        sock.sendto(reset_command, (get_ip(m), 8888))

    for sensor in sensors:
        #skip labjacks
        if int(sensor['Mote id']) >= 10:
            continue

        print(sensor['Interface Type'])
        #print("at least one sensor has been accessed")
        ip = get_ip(sensor['Mote id'])  # '192.168.2.'+sensor['Mote id']
        # See Readme for explenation of config_command
        config_command = bytearray(2)  # 2 byte byte array
        config_command[0] = int(sensor['Pin'])  # set first byte
        # set this to 0b10000000 for actuator write command
        config_command[1] |= 0b00000000
        config_command[1] |= 0b00111111 & get_interface_type_number(
            sensor['Interface Type'])
        
        print(config_command, "config_command")
        print(config_command[0])
        print(config_command[1])
        print(ip)
        sock.sendto(config_command, (ip, 8888))
        time.sleep(0.1)
        
def send_actuator_command(mote_id, pin_num, state, interface_type='Binary GPIO'):
    if interface_type != 'Heartbeat':
        print(f"Sending {state} command to pin {pin_num} on MoTE {mote_id}, via {interface_type}")
    if interface_type == 'servoPWM_12V':
            #the GPIO pin we connect to is equal to the 5V the servo is "connected" to + 28
            #send_actuator_command(mote_id, 22, True)
            pass
    actuator_write_command = 0b10000000
    actuator_state_mask = 0b01000000 if state else 0
    interface_type_number = get_interface_type_number(
        interface_type) & 0b00111111
    config_byte = actuator_write_command | actuator_state_mask | interface_type_number
    ip = get_ip(mote_id=mote_id)
    #for _ in range(3):
    sock.sendto(bytes([pin_num, config_byte]), (ip, 8888))

    if interface_type != 'Heartbeat':
        p_and_id = [actuator['P and ID'] for actuator in actuators if (actuator['Mote id'] == str(mote_id) and actuator['Pin'] == str(pin_num))]
        assert len(p_and_id) <= 1
        try:
            p_and_id = p_and_id[0]
        except:
            p_and_id = "NULL"

        sensor_logging.append_cmd_log_file([time.time() - start_epoch, mote_id, pin_num, state, p_and_id])
        sensor_logging.actuator_states[p_and_id] = state

    if interface_type != 'Bang-Bang' and interface_type != 'FireX':
        sensor_logging.actuator_acks[(int(mote_id), int(pin_num))] = False

def generate_handler(sensor_value_gtk_labels,sensor_value_gtk_slider):
    # Recieving telemetry
    internal_temp = 25

    class TelemetryRecieveHandler(socketserver.BaseRequestHandler):
        def handle(self):
            #print(time.time() - start_epoch)
            global internal_temp
            global last_gui_update_time
            #time.sleep(0.1)
            #print("We handled a packed!!!")
            cfg = load_config()
            expected_num = len(cfg[1])
            
            data = self.request[0]
            data_to_log = [time.time() - start_epoch]
            #print(f"data = {data}, len = {len(data)}, type = {type(data)}")
            assert len(data) % 5 == 0
            for i in range(len(data)//5):
                pin_num = data[5*i]
                value = int.from_bytes(data[5*i+1:5*i+5], byteorder='little')
                #print(self.client_address, "Client Adress")
                # print(f'Pin {pin_num} is {value} from {self.client_address}')

                if USE_FAKE_MOTE:
                    Mote_id = '1'
                else:
                    Mote_id = self.client_address[0][-1]
                
                mote_status[int(Mote_id) - 1] = True
                global last_mote_packet_time
                last_mote_packet_time = time.time()
                #print(time.time() - start_epoch, mote_status)

                sensor_id = (Mote_id, str(pin_num))
                #print(sensor_id)
                if sensor_id[1] == '99' or sensor_id[1] == '127':
                    #print(f"bang-bang state {value}")
                    if sensor_id[0] == '3':
                        set_bangbang_stat(bool(value & 0b10), 0)
                        set_bangbang_stat(bool(value & 0b01), 1)
                        set_firex_stat(bool(value & 0b100))
                        
                    continue

                if int(sensor_id[1]) >= 100:
                    print(f"ACK!, T = {time.time() - start_epoch}")
                    #print(gui_class.actuator_switches)
                    sensor_logging.actuator_acks[(int(sensor_id[0]), int(sensor_id[1]) - 100)] = True

                    continue
                
                try:
                    s_dict = next(s for s in cfg[1] if s['Mote id'] == sensor_id[0] and s['Pin'] == sensor_id[1])
                except:
                    print("Sensor", sensor_id[0], sensor_id[1], "Not found")
                    continue
                
                min = float(s_dict['min'])
                max = float(s_dict['max'])
                slider_fraction = (value - min)/(max - min)
                
                if s_dict['unit'] == 'PSI_1k':
                    value = unit_convert.adc_to_volts(value)
                    if sensor_id[0] == '2':
                        value = unit_convert.volts_to_psi1k(value, double=False)
                    else:
                        value = unit_convert.volts_to_psi1k(value, double=True)
                elif s_dict['unit'] == 'PSI_5k':
                    value = unit_convert.adc_to_volts(value)
                    value = unit_convert.volts_to_psi5k(value)
                elif s_dict['unit'] == 'Degrees C':
                    value = unit_convert.adc_to_volts(value)
                    #log raw voltage for degrees C
                    sensor_logging.sensor_log_values[(sensor_id[0], sensor_id[1] + 'V')] = value
                    value = unit_convert.volts_to_degC(value)
                    value += unit_convert.internal_temp
                elif s_dict['unit'] == 'Volts':
                    value = unit_convert.adc_to_volts(value)
                elif s_dict['unit'] == '*C Internal':
                    unit_convert.internal_temp = value/1000 if SCALE_INTERN_TEMP else value
                elif s_dict['unit'] == 'lbs_tank':
                    value = unit_convert.adc_to_volts(value)
                    value = unit_convert.volts_to_lbs_tank(value)
                elif s_dict['unit'] == 'lbs_engine':
                    value = unit_convert.adc_to_volts(value)
                    value = unit_convert.volts_to_lbs_engine(value)

                value += unit_convert.tares[sensor_id]

                value = round(value, 5)
                #print("recv sensor packet!", time.time())

                sensor_logging.sensor_log_values[sensor_id] = value
                sensor_logging.update_rolling_values(sensor_id, value)
                data_to_log.append(value)
            
            sensor_logging.append_sensor_log_file([time.time() - start_epoch] +  list(sensor_logging.sensor_log_values.values()))
            sensor_logging.append_actuator_log_file(time.time() - start_epoch)

            try:
                check_abort_setpoints()
            except:
                print("ERROR with AUTO ABORT. DO NOT IGNORE")

    return TelemetryRecieveHandler


def telemetry_reciever(sensor_value_gtk_labels,sensor_value_gtk_slider):
    #IP Adresses for HOST
    #Tim's Laptop: 192.168.1.106
    #TESTOP 1: 192.168.1.115
    HOST, PORT = "0.0.0.0", 8888
    with socketserver.UDPServer((HOST, PORT), generate_handler(sensor_value_gtk_labels,sensor_value_gtk_slider)) as server:
        server.serve_forever()


def start_telemetry_thread(sensor_value_gtk_labels,sensor_value_gtk_slider):
    telemetry_thread = Thread(target=telemetry_reciever, args=( 
        sensor_value_gtk_labels,sensor_value_gtk_slider), daemon=True)
    telemetry_thread.start()

def set_bangbang_stat(status, idx):
    global bangbang_status
    bangbang_status[idx] = status

def set_firex_stat(status):
    global firex_status
    firex_status = status

def send_heartbeat():
    while True:
        send_actuator_command(1, 100, True, interface_type='Heartbeat')
        send_actuator_command(2, 100, True, interface_type='Heartbeat')
        send_actuator_command(3, 100, True, interface_type='Heartbeat')
        time.sleep(2.5)

heartbeat_thread = Thread(target=send_heartbeat, daemon=True)
heartbeat_thread.start()

mote_ping = [None, None, None]

def ping_mote():
    while True:
        for moteID in range(1, 4):
            ipaddr = get_ip(mote_id=moteID)
            try:
                output = subprocess.check_output(['ping','-c','2',ipaddr])
                avgRTT = re.search("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)", str(output)).group(2)
                delay = float(float(avgRTT)/2)
                mote_ping[moteID-1] = delay
                #print("thread ping", delay)
            except:
                pass
                #print(f"ping for mote {moteID} returned error code 1")
        time.sleep(5)

ping_thread = Thread(target=ping_mote, daemon=True)   # Make a new thread to run ping_mote function
ping_thread.start()  # Run the program
