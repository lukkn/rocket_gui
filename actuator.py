from datetime import datetime
import csv

actuator_log_path = "logs/actuator_log_"

actuator_acks = {}
actuator_states = {}

def log_actuator_ack(p_and_id, binary_state):
    global actuator_acks
    actuator_acks[p_and_id] = True

    # state = "On" if binary_state == 1 else "Off" if binary_state == 0 else None
    # actuator_states[p_and_id] = state

def initialize_actuator_states(actuator_list):
    global actuator_states
    global actuator_acks

    for actuator in actuator_list:
        actuator_states[actuator['P and ID']] = 'Off'
        actuator_acks[actuator['P and ID']] = False

    # initialize actuator_log 
    csv_header_list = ['Timestamp (ms)', "P and ID", "State"]
    global actuator_log_path
    dt_string = datetime.now().strftime("%d%m%Y_%H%M%S")
    actuator_log_path += dt_string + ".csv"
    with open(actuator_log_path,  "w") as file:
        csv.writer(file).writerow(csv_header_list)
        file.flush()
        file.close()

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