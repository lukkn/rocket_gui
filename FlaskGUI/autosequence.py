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


