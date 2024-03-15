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
redline_file_name = None
redline_limits = []
redline_sensor_data_window = {}
redline_data_window_size = 10  # number of consecutive datapoints that need to exceed redline limit to abort 

# Format check
sequence_header = ['P and ID', 'State','Time(ms)','Comments']
redline_header = ['P and ID', 'Min', 'Max','State' ]

# Machine state
state_list = ['IDLE', 'MANUAL', 'ABORT', 'LIVE', 'LAUNCH']
current_state = None

socketio = None

def setup_socket(socket):
    global socketio
    socketio = socket

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

def check_sensors_in_sequence(sensors_in_commands):
    global sensor_list
    print(sensors_in_commands)
    print(sensor_list)
    for sensor in sensors_in_commands:
        if not any(config_sensor['P and ID'] == sensor for config_sensor in sensor_list):
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

    formatted_commands = {}
    sensors_in_redline_list = []
    index = 0
    for command in commands:
        sensors_in_redline_list.append(command[0])
        command_line = {'Min': command[1], 'Max': command[2], 'State': command[3]}
        index += 1
        formatted_commands[command[0]] = command_line

    if not check_file_format(header, redline_header):
        return 'file_header_error'
    elif not check_sensors_in_sequence(sensors_in_redline_list):
        return 'file_sensors_error'
    else:
        global redline_limits
        global redline_file_name
        redline_file_name = filename
        redline_limits = formatted_commands
        return 'valid_file_received'

def redline_check(sensor_data_dict):
    if (redline_on):
        for sensor in redline_limits:
            try:
                redline_sensor_data_window[sensor].append(sensor_data_dict[sensor['P and ID']])
                if len(redline_sensor_data_window[sensor]) > redline_data_window_size:
                    redline_sensor_data_window[sensor].pop(0)
                    # TODO: check if current machine state matches redline state, if not, redline is inactive for current sensor
                    if redline_exceeded(sensor['P and ID'], redline_sensor_data_window[sensor]):
                        socketio.emit('abort_request')
            except:
                redline_sensor_data_window[sensor] = []

def redline_exceeded(sensor_id, most_recent_data):
    sensor_limits_dict = redline_limits[sensor_id]
    for data in most_recent_data:
        # TODO: create separate checks for min and max
        if data > sensor_limits_dict['Min'] and data < sensor_limits_dict['Max']:
            return False
    return True
