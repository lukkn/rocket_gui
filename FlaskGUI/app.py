# part of the python standard library
from threading import Lock
import json
import os
import random
import time
import webbrowser
import sys

# configuration file tim wrote
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

autosequence_commands = []
sleep_times_list = [] # generated from difference in times between commands in autosequence_commands
cancel = False # has cancel button been pressed
autosequence_occuring = False # this will be used to block most functions while autosequence is occuring

# REMOVE BEFORE DEPLOYMENT
#actuator_list = [{'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Nitrogen engine purge', 'Pin': '0', 'P and ID': 'VPTE'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'Fuel bang-bang', 'Pin': '0', 'P and ID': 'VNTB'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Fuel tank vent', 'Pin': '1', 'P and ID': 'VFTV'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'Ox bang-bang', 'Pin': '0', 'P and ID': 'VNTO'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Ox tank fill', 'Pin': '0', 'P and ID': 'VOTF'}]
#sensor_list = [{'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '0', 'P and ID': 'PNTB', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '1', 'P and ID': 'POTB', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '2', 'P and ID': 'PNTB2', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '3', 'P and ID': 'POTB3', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '4', 'P and ID': 'PNTB4', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '5', 'P and ID': 'POTB5', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '6', 'P and ID': 'PNTB6', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '7', 'P and ID': 'POTB7', 'unit': 'bar'}]

actuator_list = [{'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Nitrogen engine purge', 'Pin': '0', 'P and ID': 'VPTE'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'Fuel bang-bang', 'Pin': '0', 'P and ID': 'IGNTN'}]


app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread2 = None
thread_lock = Lock()
thread_lock2 = Lock()

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
    global autosequence_commands
    autosequence_commands = []
    return render_template('autosequence.html')
    
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
        sensor_list, actuator_list = configuration.load_config(fileContents)
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
    if armed or (buttonID not in [actuator['P and ID'] for actuator in actuator_list]): # if disarmed then only allow button presses for sensors
        print('received button press: ', buttonID, state, 'Delay:',(time.time_ns() // 1_000_000) - current_time)
        actuator_states_and_sensor_tare_states[buttonID] = state
        socketio.emit('responding_with_button_data', [buttonID, state])
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

@socketio.on('autosequence')
def handle_autoseqeunce(file):
    print("Received file") 
    global autosequence_commands
    global sleep_times_list
    # returns a list of lists, each sublist containing a line from the config file
    #TODO: look into this parsing, is it robust?
    autosequence_commands = [line.split(",")[:-1] for line in file.decode("utf-8").splitlines()][1:]
    sleep_times_list = [abs(int(autosequence_commands[i][2]) - int(autosequence_commands[i+1][2])) for i in range(len(autosequence_commands)-1)] + [0] # 0 on the end so we dont go out of range and instead delay for 0 seconds after autoseq is finished
    print("differences =", sleep_times_list)
    print("autoseq commands =", autosequence_commands)


@socketio.on('launch_request')
def handle_launch_request():
    global autosequence_occuring
    if autosequence_occuring:
        print("Autosequence is already running")
    else:
        print("Received launch request")

        autosequence_occuring = True

        global cancel 
        cancel = False  

        # check for config file
        if not autosequence_commands:
            socketio.emit('no_config')
        else:
            send_launch_request_to_mote() # Networking function ### i think we should move this a few lines down and have it be just an actuator press
            sleep_list_iterator = 0 # iterate over a list of times to sleep, starting at index 0
            for command in autosequence_commands:
                buttonID = command[0]
                booleanState = command[1] # true false convention used in autoseq file. This is a string as .csv files are parsed as strings
                stringState = 'on' if booleanState == 'True' else 'off' # on/off state used in webpages
                time = command[2] # not used in app.py; sent to autosequence.html to create rowID, used in case we toggle an actuator :: True, False, True :: then rows would be identical
                socketio.emit('responding_with_button_data', [buttonID, stringState])
                socketio.emit('command', [buttonID, booleanState, time])
                # send actuator to mote #
                if (cancel):
                    print("Launch cancelled")
                    break
                socketio.sleep(sleep_times_list[sleep_list_iterator]/1000) # socketio.sleep() expects seconds as input
                sleep_list_iterator += 1
        autosequence_occuring = False


@socketio.on('connect_request')
def handle_connect_request():
    print("Received connect request to MoTE")
    networking.send_config_to_mote(sensor_list, actuator_list) # Networking function
            

@socketio.on('abort_request')
def handle_abort_request(abort_sequence_file):
    print("Received abort request") 
    networking.send_abort_request_to_mote() #Networking function

@socketio.on('cancel_request')
def handle_cancel_request():
    print("Received cancel request") 
    global autosequence_commands
    autosequence_commands = []
    networking.send_cancel_request_to_mote()
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