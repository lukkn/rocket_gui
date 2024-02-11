# part of the python standard library
from threading import Lock
import json
import os
import random
import time
import webbrowser
import sys
import math

import configuration
import networking

# temporarily append our library directory to sys.path so we can use eventlet. DO NOT REMOVE
sys.path.append(os.path.abspath("./python_flask_and_flaskio_and_eventlet_libraries"))

# these libraries located in the folder named: 'python_flask_and_flaskio_and_eventlet_libraries'
# dot notation is used to navigate to the next folder
from python_flask_and_flaskio_and_eventlet_libraries.flask import Flask, render_template
from python_flask_and_flaskio_and_eventlet_libraries.flask_socketio import SocketIO


# not quite sure what this does but leave it here anyway
async_mode = None

# could use used to make unique id's for webpages
sessionid = str(random.random())[2:]

# TODO: better way than using global variables, verify config file
# GLOBAL VARIABLES for sensors and actuators
actuator_list = []
sensor_list = []

# dictionary of modified states for sensors + actuators
actuator_states_and_sensor_tare_states = {}

# Global Variable that determines if stand is armed
armed = False

autosequence_header_line = []
autosequence_commands = []
completed_autosequence_commands = []
sleep_times_list = [] # generated from difference in times between commands in autosequence_commands
cancel = False # has cancel button been pressed
autosequence_occuring = False # this will be used to block most functions while autosequence is occuring
time_to_show = 0

# REMOVE BEFORE DEPLOYMENT
#actuator_list = [{'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Nitrogen engine purge', 'Pin': '0', 'P and ID': 'VPTE'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'Fuel bang-bang', 'Pin': '0', 'P and ID': 'VNTB'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Fuel tank vent', 'Pin': '1', 'P and ID': 'VFTV'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'Ox bang-bang', 'Pin': '0', 'P and ID': 'VNTO'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Ox tank fill', 'Pin': '0', 'P and ID': 'VOTF'}]
#sensor_list = [{'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '0', 'P and ID': 'PNTB', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '1', 'P and ID': 'POTB', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '2', 'P and ID': 'PNTB2', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '3', 'P and ID': 'POTB3', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '4', 'P and ID': 'PNTB4', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '5', 'P and ID': 'POTB5', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '6', 'P and ID': 'PNTB6', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '7', 'P and ID': 'POTB7', 'unit': 'bar'}]

#actuator_list = [{'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Nitrogen engine purge', 'Pin': '0', 'P and ID': 'VPTE'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'Fuel bang-bang', 'Pin': '0', 'P and ID': 'IGNTN'}]


app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread2 = None
thread3 = None
thread_lock = Lock()
thread_lock2 = Lock()
thread_lock3 = Lock()

#i am in webthocket hell
#lmao skill issue


# webbrowser.open_new('http://127.0.0.1:5000/sensors')
# webbrowser.open_new('http://127.0.0.1:5000/actuators')
# webbrowser.open_new('http://127.0.0.1:5000/pidview')
# webbrowser.open_new('http://127.0.0.1:5001/') # + sessionID here if needed


# flask routes for webpages
@app.route('/', methods=['GET']) # + sessionID here if needed
def index():
    return render_template('index.html', armed=armed)

@app.route('/autosequence', methods=['GET'])
def autosequence():
    return render_template('autosequence.html', autosequence_header_line=autosequence_header_line, autosequence_commands=autosequence_commands, completed_autosequence_commands=completed_autosequence_commands, time_to_show=time_to_show)

@app.route('/pidview', methods=['GET'])
def pidview():
    return render_template('pidview.html', actuator_list=actuator_list, sensor_list=sensor_list, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states)

@app.route('/sensors', methods=['GET'])
def sensors():
    return render_template('sensors.html', sensor_list=sensor_list, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states)

@app.route('/actuators', methods=['GET'])
def actuators():
    return render_template('actuators.html', actuator_list=actuator_list, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states)


# methods to listen for client events
@socketio.on('uploadConfigFile')
def loadConfigFile(CSVFileAndFileContents):
    CSVFile = CSVFileAndFileContents[0]
    fileContents = CSVFileAndFileContents[1]
    if CSVFile == 'csvFile1':
        global sensor_list
        global actuator_list
        #print(fileContents)
        actuator_list, sensor_list = configuration.load_config(fileContents)
        socketio.emit('sensor_and_actuator_config_uploaded')

@socketio.on('armOrDisarmRequest')
def armDisarm():
    global armed
    if armed:
        armed = False
    elif not armed:
        armed = True
    else:
        print('client requested a non-boolean state')
    socketio.emit('armOrDisarmResponse', armed)
    print('variable armed is now: ', armed)

@socketio.on('received_button_press')
def handle_button_press(buttonID, state, current_time):

    # lookup rest of parameters for buttonID in either sensors or actuators
    # TODO: IMPORTANT; enforce uniqueness in 'P and ID' for all lines in config file
    buttonDict = [config_line for config_line in (actuator_list + sensor_list) if config_line['P and ID'] == buttonID][0] # index 0 because list comprehension returns a list containing 1 dictionary

    state_bool = True if state == "on" else False if state == "off" else None

    if state_bool is None:
        print(f"Invalid state {state}, no command sent")
        return

    print('received button press: ', buttonID, state, 'Delay:',(time.time_ns() // 1_000_000) - current_time)
    if buttonDict['Sensor or Actuator'] == 'sensor':
        actuator_states_and_sensor_tare_states[buttonID] = state
        socketio.emit('responding_with_button_data', [buttonID, state])
    elif buttonDict['Sensor or Actuator'] == 'actuator' and armed:
        actuator_states_and_sensor_tare_states[buttonID] = state
        socketio.emit('responding_with_button_data', [buttonID, state])
        networking.send_actuator_command(buttonDict['Mote id'], buttonDict['Pin'], state_bool, buttonDict['Interface Type'])
    else:
        print("stand is disarmed!!! " + buttonID + " was not set to " + state)


@socketio.on('actuator_button_coordinates')
def actuator_button_coordinates(get_request_or_coordinate_data):
    # if pidview.html is requesting the coordinates stored in the .json
    if get_request_or_coordinate_data == 'getCoordinates':
        #emit coordinates
        with open(os.path.dirname(os.path.abspath(__file__)) + '/static/coordinates.json', 'r') as file:
            coordinates = json.load(file)
            print("pidview.html is requesting coordinates from .json")
        socketio.emit('get_actuator_button_location_config', coordinates)
    else: # pidview.html is sending new button coordinates for saving
        with open(os.path.dirname(os.path.abspath(__file__)) + '/static/coordinates.json', 'w') as file:
            json.dump(get_request_or_coordinate_data, file)
            print("button coordinates saved to .json file")

@socketio.on('autosequence_uploaded')
def handle_autoseqeunce(file):
    global autosequence_header_line
    global autosequence_commands
    global sleep_times_list
    global completed_autosequence_commands
    global time_to_show

    completed_autosequence_commands = []

    file_content = [line.rstrip('\n') for line in file.decode("utf-8").splitlines() if line.strip()]
    autosequence_header_line = file_content[0].split(",")
    autosequence_commands = [line.split(",") for line in file_content[1:]]
    sleep_times_list = [abs(int(autosequence_commands[i][2]) - int(autosequence_commands[i+1][2])) for i in range(len(autosequence_commands)-1)] + [0] # 0 on the end so we dont go out of range and instead delay for 0 seconds after autoseq is finished
    time_to_show = int(int(autosequence_commands[0][2])/1000)
    #print("autoseq_commands_header =", autosequence_header_line)
    #print("differences =", sleep_times_list)
    #print("autoseq commands =", autosequence_commands)
    socketio.emit('autosequence_successfully_received_in_python')


@socketio.on('launch_request')
def handle_launch_request():
    global autosequence_occuring
    global completed_autosequence_commands
    global time_to_show
    global cancel
    if autosequence_occuring:
        print("Autosequence is already running")
        return None
    else:
        print("Received launch request")
        # check for config file
        if not autosequence_commands:
            socketio.emit('no_config')
            print("cofig not received properly")
            return None
        else:
            print("autosequence started")
            autosequence_occuring = True
            cancel = False
            completed_autosequence_commands = []
            time_to_show = int(int(autosequence_commands[0][2])/1000)
            sleep_list_iterator = 0 # iterate over a list of times to sleep, starting at index 0
            socketio.emit('autosequence_started')

            for command in autosequence_commands:
                timeAtBeginning = time.perf_counter()
                #print("timeAtBeginning", timeAtBeginning)
                buttonID = command[0]
                booleanState = command[1] # true false convention used in autoseq file. This is a string as .csv files are parsed as strings
                stringState = 'on' if booleanState == 'True' else 'off' # on/off state used in webpages
                completed_autosequence_commands += [command]

                booleanState = True if booleanState == "True" else False

                socketio.emit('responding_with_button_data', [buttonID, stringState])
                socketio.emit('command', completed_autosequence_commands)
                print("Command Sent =", command)

                # send actuator to mote #
                buttonDict = [config_line for config_line in (actuator_list + sensor_list) if config_line['P and ID'] == buttonID][0]
                networking.send_actuator_command(buttonDict['Mote id'], buttonDict['Pin'], booleanState, buttonDict['Interface Type'])

                while (time.perf_counter() - timeAtBeginning) < sleep_times_list[sleep_list_iterator]/1000:
                    if cancel or not autosequence_occuring:
                        autosequence_occuring = False
                        print("Launch cancelled")
                        return None
                    socketio.sleep(.0001)

                sleep_list_iterator += 1
                #print("loop time =", time.perf_counter() - timeAtBeginning)
            autosequence_occuring = False

@socketio.on('start_timer')
def broadcast_time():
    socketio.emit('start_timer_ack')
    global time_to_show
    while True:
        timeAtBeginning = time.perf_counter()

        socketio.emit('current_time', time_to_show)

        while (time.perf_counter() - timeAtBeginning) < 1:
            if cancel or not autosequence_occuring:
                print("timer stopped")
                return None
            socketio.sleep(.01)

        time_to_show += 1

@socketio.on('connect_request')
def handle_connect_request():
    print("Attempting to send config to MoTE")
    networking.send_config_to_mote(sensor_list, actuator_list) # Networking function
    networking.start_telemetry_thread()


@socketio.on('abort_request')
def handle_abort_request(abort_sequence_file):
    print("Received abort request")
    networking.send_abort_request_to_mote() # Networking function

@socketio.on('cancel_request')
def handle_cancel_request():
    global time_to_show
    print("Received cancel request at",time_to_show,"seconds")
    global cancel
    cancel = True


# FUNCTIONS BELOW RELATE TO GETTING SENSOR DATA IN BACKGROUND THREAD
@socketio.on('guion')
def guion():
    print('guion was triggered')
    global thread
    global thread2
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(sensor_data_thread)
    with thread_lock2:
        if thread2 is None:
            thread2 = socketio.start_background_task(ping_thread)

def sensor_data_thread():
    # if this delay is not here code fails
    socketio.sleep(1)
    while True:
        socketio.sleep(1/20)
        # sensors_and_data is a list of tuples containing (sensorID, value)
        sensors_and_data = packet_sensor_data(sensor_list)

        # test what happens with different scales

        #sensors_and_data[0][1] = random.random()*10

        # testing shows we get data at 3khz with random, 6khz with a predetermined constant; ex: 1
        # with open("sensor_data_log", mode='a', newline='') as csv_file:
        #     csv_writer = csv.writer(csv_file)
        #     csv_writer.writerow(sensors_and_data)

        # print("sensor is reading:", sensors_and_data[0][1])
        socketio.emit('sensor_data', [sensors_and_data, time.time_ns() // 1000000])

def ping_thread():
    while True:
        socketio.sleep(2)
        socketio.emit("ping", time.time_ns() // 1000000)
        #print('ping', time.time())

# Dummy data function, this function should FETCH data from udp packet
def packet_sensor_data(sensor_list):
    a = []
    for sensor in sensor_list:
        a.append([sensor['P and ID'], round(random.random(), 5)])
    return a

count = 0
def packet_sensor_data2(sensor_list):
    global count
    a = []
    for sensor in sensor_list:
        a.append((sensor['P and ID'], count))
    count+=1
    return a


# start the app
if __name__ == '__main__':
    socketio.run(app, port=5001, debug=False)
