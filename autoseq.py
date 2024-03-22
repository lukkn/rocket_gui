from threading import Event
import time

import networking

# contains names for non-command lines in autosequence 
actuator_name_exceptions = ["NULL", "STATE_IDLE", "STATE_ACTIVE"]

actuator_list = []
sensor_list = []

time_to_show = 0

# Autosequence
autosequence_cancel = False # has cancel button been pressed
autosequence_occuring = False # this will be used to block most functions while autosequence is occuring
autosequence_file_name = None
autosequence_commands = []

# Abort sequence
abort_sequence_file_name = None
abort_sequence_commands = []

# Redline
redline_on = False
sensor_redline = {}
redline_file_name = None
redline_states = []

# Format check
sequence_header = ['P and ID', 'State','Time(ms)','Comments']
redline_header = ['P and ID', 'Min', 'Max','State' ]


def initialize_sensors_and_actuators(sensors, actuators):
    global sensor_list
    global actuator_list
    sensor_list = sensors
    actuator_list = actuators


def parse_file(file):
    file_content = [line.rstrip('\n') for line in file.decode("utf-8").splitlines() if line.strip()]
    header = file_content[0].split(",")
    command_list = [line.split(",") for line in file_content[1:]]
    sleep_times_list = [abs(int(command_list[i][2]) - int(command_list[i+1][2])) for i in range(len(command_list)-1)] + [0] # 0 on the end so we dont go out of range and instead delay for 0 seconds after autoseq is finished
    formatted_commands = []
    index = 0
    for command in command_list:
        command_line = {'P and ID': command[0], 'State': command[1], 'Time(ms)': command[2], 'Comments': command[3], 'Sleep time(ms)': sleep_times_list[index], 'Complete': False}
        index += 1
        formatted_commands.append(command_line)
    return header, formatted_commands

def check_actuators_in_sequence(commands):
    global actuator_list
    file_valid = True
    for command in commands:
        if not any(actuator['P and ID'] == command['P and ID'] for actuator in actuator_list):
            command['Type'] = 'Placeholder'
            if command['P and ID'] not in actuator_name_exceptions:
                command['Type'] = 'Invalid'
                file_valid = False
        else:
            command['Type'] = 'Actuator'
    return file_valid

def check_sensors_in_sequence(commands):
    global sensor_list
    for command in commands:
        if not any (sensor['P and ID'] == command ['P and ID'] for sensor in sensor_list):
            return False
    return True

def check_file_format(file_header, valid_header):
    return file_header == valid_header


def parse_and_check_sequence_files(sequence_name, filename, file):
    header, commands = parse_file(file)
    if not check_file_format(header, sequence_header):
        return 'file_header_error'
    elif not check_actuators_in_sequence(commands):
        return 'file_actuators_error'
    else:
        match sequence_name:
            case 'autosequence':
                global autosequence_commands
                global autosequence_file_name
                autosequence_file_name = filename
                autosequence_commands = commands
            case 'abort_sequence':
                global abort_sequence_commands
                global abort_sequence_file_name
                abort_sequence_file_name = filename 
                abort_sequence_commands = commands
        return 'valid_file_received'
    
    
def parse_and_check_redline(file, filename):
    file_content = [line.rstrip('\n') for line in file.decode("utf-8").splitlines() if line.strip()]
    header = file_content[0].split(",")
    commands = [line.split(",") for line in file_content[1:]]

    formatted_commands = []
    index = 0
    for command in commands:
        command_line = {'P and ID': command[0], 'Min': command[1], 'Max': command[2], 'State': command[3]}
        index += 1
        formatted_commands.append(command_line)

    if not check_file_format(header, redline_header):
        return 'file_header_error'
    elif not check_sensors_in_sequence(formatted_commands):
        return 'file_sensors_error'
    else:
        global redline_states
        global redline_file_name
        redline_file_name = filename
        redline_states = formatted_commands
        print(redline_states)
        return 'valid_file_received'

def redline_check(sensor_data_dict):
    pass
