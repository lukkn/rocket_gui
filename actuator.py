from datetime import datetime
import csv
import re
import os

actuator_log_path = "logs/actuator_log_"

actuator_acks = {}
actuator_states = {}

def log_actuator_ack(p_and_id, binary_state):
    global actuator_acks
    actuator_acks[p_and_id] = True

    # state = "On" if binary_state == 1 else "Off" if binary_state == 0 else None
    # actuator_states[p_and_id] = state

def initialize_actuator_states(actuator_list, config_name):
    global actuator_states
    global actuator_acks

    for actuator in actuator_list:
        actuator_states[actuator['P and ID']] = 'Off'
        actuator_acks[actuator['P and ID']] = False

    # initialize actuator_log 
    csv_header_list = ['Timestamp (s)', "P and ID", "State"]
    global actuator_log_path

    filenames = sorted(list(filter(lambda flname: "actuator_log" in flname, next(os.walk("logs"), (None, None, []))[2])), key=file_num_from_name)
    try:
        current_filenum = int(re.findall('\d+', filenames[-1])[0]) + 1
    except: 
        current_filenum = 0 

    actuator_log_path = "logs/actuator_log_" + str(current_filenum) + "_" + config_name + ".csv"
    with open(actuator_log_path,  "w") as file:
        csv.writer(file).writerow(csv_header_list)
        file.flush()
        file.close()

def file_num_from_name(fname):
    return int(re.findall('\d+', fname)[0]) + 1

def get_actuator_states():
    return actuator_states

def get_actuator_acks():
    return actuator_acks

def log_actuator_data(timestamp, actuator_state_dict):

    data_to_log = [timestamp]

    for actuator in actuator_state_dict:
        try:
            data_to_log.extend([actuator, actuator_state_dict[actuator]])
        except: 
            data_to_log.extend([None, None, None])

    with open(actuator_log_path, "a") as file:
        csv.writer(file).writerow(data_to_log)
        file.flush()
        file.close()