# contains names for non-command lines in autosequence 
actuator_name_exceptions = ["NULL", "STATE_IDLE", "STATE_ACTIVE"]

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

def check_actuators_in_sequence(commands, actuator_list):
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


def execute_autosequence(commands):
    global autosequence_occuring
    global time_to_show
    global cancel

    autosequence_occuring = True
    cancel = False
    time_to_show = int(int(autosequence_commands[0]['Time(ms)'])/1000)
    for command in commands:
        timeAtBeginning = time.perf_counter()
        stringState = 'on' if command['State'] == True else 'off' # on/off state used in webpages
        socketio.emit('responding_with_button_data', [command['P and ID'], stringState])
        command['Completed'] = True
        socketio.emit('autosequence_command_sent', command)
        # send actuator to mote #
        if command['Type'] == 'Actuator' :
            buttonDict = [config_line for config_line in actuator_list if config_line['P and ID'] == command['P and ID']][0]
            networking.send_actuator_command(buttonDict['Mote id'], buttonDict['Pin'], command['State'], buttonDict['Interface Type'])
        while (time.perf_counter() - timeAtBeginning) < command['Sleep time(ms)']/1000:
            if cancel or not autosequence_occuring:
                autosequence_occuring = False
                print("Launch cancelled")
                return None
            socketio.sleep(.0001)
    autosequence_occuring = False

def execute_abort_sequence(commands):
    global autosequence_occuring
    global cancel

    autosequence_occuring = False
    cancel = True

    for command in commands:
        stringState = 'on' if command['State'] == True else 'off' # on/off state used in webpages
        socketio.emit('responding_with_button_data', [command['P and ID'], stringState])
        command['Completed'] = True
        socketio.emit('abort_sequence_command_sent', command)
        # send actuator to mote #
        if command['Type'] == 'Actuator' :
            buttonDict = [config_line for config_line in actuator_list if config_line['P and ID'] == command['P and ID']][0]
            networking.send_actuator_command(buttonDict['Mote id'], buttonDict['Pin'], command['State'], buttonDict['Interface Type'])
        time.sleep(command['Sleep time(ms)']/1000)

def check_file_format(header):
    return header[0] == 'P and ID' and header[1] == 'State' and header[2] == 'Time(ms)' and header[3] == 'Comments'

def parse_and_check_files(file):
    header, commands = autosequence.parse_file(file)
    if not check_file_format(header):
        socketio.emit('file_header_error')
    elif not autosequence.check_actuators_in_sequence(commands, actuator_list):
        print ('file_actuators_error')
        socketio.emit('file_actuators_error')
    else:
        socketio.emit('valid_file_received')
        return commands

# start the app
if __name__ == '__main__':
    socketio.run(app, port=5001, debug=False)
