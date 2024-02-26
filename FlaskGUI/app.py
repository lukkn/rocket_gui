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
import autosequence
import sensor

# temporarily append our library directory to sys.path so we can use eventlet. DO NOT REMOVE
#sys.path.append(os.path.abspath("./python_flask_and_flaskio_and_eventlet_libraries"))

# these libraries located in the folder named: 'python_flask_and_flaskio_and_eventlet_libraries'
# dot notation is used to navigate to the next folder
#from python_flask_and_flaskio_and_eventlet_libraries.flask import Flask, render_template
#from python_flask_and_flaskio_and_eventlet_libraries.flask_socketio import SocketIO

from flask import Flask, render_template
from flask_socketio import SocketIO


# Socket IO config
async_mode = None

# could use used to make unique id's for webpages
sessionid = str(random.random())[2:]

# TODO: better way than using global variables, verify config file
# GLOBAL VARIABLES for sensors and actuators
#actuator_list = [{'Mote id': '3', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'VNMO', 'Pin': '5', 'P and ID': 'VNMO', 'unit': '', 'min': '', 'max': '', 'window': ''}, {'Mote id': '3', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'VNMF', 'Pin': '6', 'P and ID': 'VNMF', 'unit': '', 'min': '', 'max': '', 'window': ''}, {'Mote id': '3', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'VPTF', 'Pin': '7', 'P and ID': 'VPTF', 'unit': '', 'min': '', 'max': '', 'window': ''}, {'Mote id': '3', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'IGNTN', 'Pin': '8', 'P and ID': 'IGNTN', 'unit': '', 'min': '', 'max': '', 'window': ''}, {'Mote id': '2', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'VNTO', 'Pin': '5', 'P and ID': 'VNTO', 'unit': '', 'min': '', 'max': '', 'window': ''}, {'Mote id': '2', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'VNTF', 'Pin': '6', 'P and ID': 'VNTF', 'unit': '', 'min': '', 'max': '', 'window': ''}, {'Mote id': '2', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'VQDA', 'Pin': '7', 'P and ID': 'VQDA', 'unit': '', 'min': '', 'max': '', 'window': ''}, {'Mote id': '2', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'VNOF', 'Pin': '8', 'P and ID': 'VNOF', 'unit': '', 'min': '', 'max': '', 'window': ''}]
#sensor_list = [{'Mote id': '3', 'Sensor or Actuator': 'sensor', 'Interface Type': 'SPI_ADC_2ch PGA128', 'Human Name': 'PNTB', 'Pin': '0', 'P and ID': 'PNTB', 'unit': 'PSI_M5K', 'min': '0', 'max': '5000', 'window': '0'}, {'Mote id': '3', 'Sensor or Actuator': 'sensor', 'Interface Type': 'SPI_ADC_2ch PGA128', 'Human Name': 'PNPC', 'Pin': '1', 'P and ID': 'PNPC', 'unit': 'PSI_M1K', 'min': '0', 'max': '1000', 'window': '0'}, {'Mote id': '3', 'Sensor or Actuator': 'sensor', 'Interface Type': 'SPI_ADC_2ch PGA128', 'Human Name': 'POTB', 'Pin': '2', 'P and ID': 'POTB', 'unit': 'PSI_M1K', 'min': '0', 'max': '1000', 'window': '0'}]
actuator_list = []
sensor_list = []

mote_ping = []
config_file_name = None

# dictionary of modified states for sensors + actuators
actuator_states_and_sensor_tare_states = {}
actuator_states_from_mote = {}

# Global Variable that determines if stand is armed
armed = False

# Autosequence
autosequence_file_name = None
autosequence_commands = []
cancel = False # has cancel button been pressed
autosequence_occuring = False # this will be used to block most functions while autosequence is occuring
time_to_show = 0

# Abort sequence
abort_sequence_file_name = None
abort_sequence_commands = []

app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app, async_mode=async_mode)

sensor_thread = None
sensor_thread_lock = Lock()
connection_thread = None
connection_thread_lock = Lock()

#i am in webthocket hell
#lmao skill issue


# webbrowser.open_new('http://127.0.0.1:5000/sensors')
# webbrowser.open_new('http://127.0.0.1:5000/actuators')
# webbrowser.open_new('http://127.0.0.1:5000/pidview')
# webbrowser.open_new('http://127.0.0.1:5001/') # + sessionID here if needed


# flask routes for webpages
@app.route('/', methods=['GET']) # + sessionID here if needed
def index():
    return render_template('index.html', armed=armed, config_file_name = config_file_name, sensor_list=sensor_list, actuator_list=actuator_list)

@app.route('/autosequence', methods=['GET'])
def autosequence():
    return render_template('autosequence.html', autosequence_commands=autosequence_commands, abort_sequence_commands= abort_sequence_commands, time_to_show=time_to_show, autosequence_file_name = autosequence_file_name, abort_sequence_file_name = abort_sequence_file_name)

@app.route('/pidview', methods=['GET'])
def pidview():
    return render_template('pidview.html', actuator_list=actuator_list, sensor_list=sensor_list, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states)

@app.route('/sensors', methods=['GET'])
def sensors():
    return render_template('sensors.html', sensor_list=sensor_list, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states)

@app.route('/actuators', methods=['GET'])
def actuators():
    return render_template('actuators.html', actuator_list=actuator_list, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states, actuator_states_from_mote=actuator_states_from_mote)


# methods to listen for client events
@socketio.on('uploadConfigFile')
def loadConfigFile(CSVFileAndFileContents, fileName):
    global config_file_name
    config_file_name = fileName

    CSVFile = CSVFileAndFileContents[0]
    fileContents = CSVFileAndFileContents[1]

    if CSVFile == 'csvFile1':
        global sensor_list
        global actuator_list

        try:
            actuator_list, sensor_list = configuration.load_config(fileContents)
            socketio.emit('sensor_and_actuator_config_uploaded')
        except:
            socketio.emit("config_file_header_error")

        sensor.initialize_sensor_offset(sensor_list)

@socketio.on('connect_request')
def handle_connect_request():
    print("Attempting to send config to MoTE")
    networking.send_config_to_mote(sensor_list, actuator_list) # Networking function
    networking.start_telemetry_thread()
    global sensor_thread
    with sensor_thread_lock:
        if sensor_thread is None:
            sensor_thread = socketio.start_background_task(sensor_data_thread)
    print("started sensor data thread")
    global connection_thread
    with connection_thread_lock:
        if connection_thread is None:
            connection_thread = socketio.start_background_task(update_connection_status)
    print("started connection status thread")

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
        socketio.emit('responding_with_button_data', [buttonID, state]) # for taring we can just sync the state of the pages, no mote logic needed
        networking.updateTares(actuator_states_and_sensor_tare_states)
    elif buttonDict['Sensor or Actuator'] == 'actuator' and armed:
        print("getting ready to send actuator state to mote. the current value of actuator_states_from_mote is:", actuator_states_from_mote)
        actuator_states_and_sensor_tare_states[buttonID] = state
        actuator_states_from_mote[buttonID] = 'unacknoweleged'
        socketio.emit('responding_with_button_data_from_mote', [buttonID, "unacknoweleged"])
        socketio.emit('responding_with_button_data', [buttonID, state])
        networking.send_actuator_command(buttonDict['Mote id'], buttonDict['Pin'], state_bool, buttonDict['Interface Type'])
    else:
        print("stand is disarmed!!! " + buttonID + " was not set to " + state)


@socketio.on('actuator_button_coordinates')
def actuator_button_coordinates(get_request_or_coordinate_data):
    # if pidview.html is requesting the coordinates stored in the .json
    if get_request_or_coordinate_data == 'getCoordinates':
        #emit coordinates'test': 'testval'
        with open(os.path.dirname(os.path.abspath(__file__)) + '/static/coordinates.json', 'r') as file:
            coordinates = json.load(file)
            print("pidview.html is requesting coordinates from .json")
        socketio.emit('get_actuator_button_location_config', coordinates)
    else: # pidview.html is sending new button coordinates for saving
        with open(os.path.dirname(os.path.abspath(__file__)) + '/static/coordinates.json', 'w') as file:
            json.dump(get_request_or_coordinate_data, file)
            print("button coordinates saved to .json file")


@socketio.on('autosequenceFile_uploaded')
def handle_autoseqeunce(file, fileName):
    global autosequence_file_name
    global autosequence_commands
    global time_to_show
    try:
        autosequence_commands = parse_and_check_files(file)
        time_to_show = int(int(autosequence_commands[0]['Time(ms)'])/1000)
        autosequence_file_name = fileName
    except:
        print("an autosequence file error occured")


@socketio.on('abortSequenceFile_uploaded')
def handle_abort_sequence(file, fileName):
    global abort_sequence_file_name
    global abort_sequence_commands
    try:
        abort_sequence_commands = parse_and_check_files(file)
        abort_sequence_file_name = fileName
    except:
        print("an abort sequence file error occured")


@socketio.on('launch_request')
def handle_launch_request():
    global autosequence_commands
    if autosequence_occuring:
        return None
    elif not autosequence_commands:
        socketio.emit('no_autosequence')
        return None
    elif not abort_sequence_commands:
        socketio.emit('no_abort_sequence')
    else:
        socketio.emit('autosequence_started')
        execute_autosequence(autosequence_commands)


@socketio.on('start_timer')
def broadcast_time():
    socketio.emit('start_timer_ack')
    global time_to_show
    print('timer started')
    while True:
        timeAtBeginning = time.perf_counter()
        socketio.emit('current_time', time_to_show)
        while (time.perf_counter() - timeAtBeginning) < 1:
            if cancel or not autosequence_occuring:
                print("timer stopped, thread ended")
                return None
            socketio.sleep(.01)
        time_to_show += 1


@socketio.on('abort_request')
def handle_abort_request():
    global autosequence_occuring
    print("Received abort request")
    networking.send_abort_request_to_mote() # Networking function
    if (autosequence_occuring):
        execute_abort_sequence(abort_sequence_commands)
    else:
        socketio.emit('no_autosequence_running')

@socketio.on('cancel_request')
def handle_cancel_request():
    global time_to_show
    global autosequence_occuring
    print("Received cancel request at",time_to_show,"seconds")
    if (autosequence_occuring):
        global cancel
        cancel = True
    else:
        socketio.emit('no_autosequence_running')


@socketio.on('guion')
def guion():
    print('guion was triggered')

@socketio.on('tare')
def handle_tare(sensorID, bool):
    if bool: 
        sensor.tare(sensorID)
    else:
        sensor.untare(sensorID)
    

# Home page functions
def update_connection_status():
    global mote_ping
    while True:
        mote_ping = networking.get_mote_ping()
        socketio.emit('mote_ping', mote_ping)
        socketio.sleep(1)


# Sensor page functions
def sensor_data_thread():
    socketio.sleep(1)
    while True:
        socketio.sleep(1/20)
        sensors_and_data = sensor.get_sensor_data()
        # timestamp = time.time_ns() // 1000000
        socketio.emit('sensor_data', sensors_and_data)


# Actuator functions
def actuator_ack(p_and_id, state):
    #socketio.sleep(1)
    global actuator_states_from_mote
    print("what is seen inside actuator_ack:", actuator_states_from_mote)
    actuator_states_from_mote[p_and_id] = "ackefajldfaj;dlf"
    print(actuator_states_from_mote[p_and_id])
    print([p_and_id, state])
    socketio.emit('responding_with_button_data_from_mote', [p_and_id, state])
    print("actuator ack recd in app.py", p_and_id, state)
    return actuator_states_from_mote

# Autosequence page functions

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
