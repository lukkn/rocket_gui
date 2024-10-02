from datetime import datetime
import csv
import re
import time
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
        if actuator['Unpowered State'] == 'Open':
            actuator_states[actuator['P and ID']] = 'On'
        else:
            actuator_states[actuator['P and ID']] = 'Off'
        actuator_acks[actuator['P and ID']] = False

    # initialize actuator_log 
    csv_header_list = ['Timestamp (ms)', "P and ID", "State"]
    global actuator_log_path


    folder_name = time.strftime("%Y-%m-%d") + "_" + config_name 
    folder_path = os.path.join("logs",folder_name)

    if not os.path.exists(folder_path): 
        print(f"Creating {folder_name}")
        os.mkdir(folder_path)

        #this is fishy here since it will always try to generate the 0th file 

    filenames = sorted(
        list(filter(lambda flname: re.search(r'actuators_\d+\.csv', flname), 
        next(os.walk(folder_path), (None, None, []))[2])),
        key=lambda flname: int(re.search(r'\d+', flname).group())
    )

    try:
        current_filenum = int(re.findall(r'\d+', filenames[-1])[0]) + 1 # r makes python interpret \ as a regular character instead of an escape character
    except: 
        current_filenum = 1


    file_name = "actuators" + "_" + str(current_filenum) + ".csv"
    actuator_log_path = os.path.join(folder_path, file_name) 
    with open(actuator_log_path,  "w") as file:
        csv.writer(file).writerow(csv_header_list)
        file.flush()
        file.close()

def file_num_from_name(fname):
    try:
        return int(re.findall(r'\d+', fname)[0]) + 1 # r makes python interpret \ as a regular character instead of an escape character
    except:
        return 0

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