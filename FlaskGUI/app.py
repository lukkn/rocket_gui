from flask import Flask, render_template
from flask_socketio import SocketIO
from threading import Lock
import json
import os
import random
import time
import csv
import webbrowser

async_mode = None
sessionid = str(random.random())[2:]

# GLOBAL VARIABLES
actuator_buttons = []
sensor_list = []

actuator_states_and_sensor_tare_states = {}
armed = False

# REMOVE BEFORE DEPLOYMENT
actuator_buttons = [{'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Nitrogen engine purge', 'Pin': '0', 'P and ID': 'VPTE'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'Fuel bang-bang', 'Pin': '0', 'P and ID': 'VNTB'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Fuel tank vent', 'Pin': '1', 'P and ID': 'VFTV'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'Binary GPIO', 'Human Name': 'Ox bang-bang', 'Pin': '0', 'P and ID': 'VNTO'}, {'Mote id': '1', 'Sensor or Actuator': 'actuator', 'Interface Type': 'servoPWM', 'Human Name': 'Ox tank fill', 'Pin': '0', 'P and ID': 'VOTF'}]
sensor_list = [{'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '0', 'P and ID': 'PNTB', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '1', 'P and ID': 'POTB', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '2', 'P and ID': 'PNTB2', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '3', 'P and ID': 'POTB3', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '4', 'P and ID': 'PNTB4', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '5', 'P and ID': 'POTB5', 'unit': 'bar'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Nitrogen storage bottle pressure', 'Pin': '6', 'P and ID': 'PNTB6', 'unit': 'C'}, {'Mote id': '2', 'Sensor or Actuator': 'sensor', 'Interface Type': 'i2c ADC 1ch', 'Human Name': 'Ox storage bottle pressure', 'Pin': '7', 'P and ID': 'POTB7', 'unit': 'bar'}]


app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app, async_mode=async_mode)
#TODO: what should thread equal, same with async_mode at top of page
thread = None
thread2 = None
thread_lock = Lock()
thread_lock2 = Lock()

#i am in webthocket hell


# webbrowser.open_new('http://127.0.0.1:5000/sensors')
# webbrowser.open_new('http://127.0.0.1:5000/actuators')
# webbrowser.open_new('http://127.0.0.1:5000/pidview')
webbrowser.open_new('http://127.0.0.1:5000/' + sessionid)

@app.route('/' + sessionid, methods=['GET'])
def index():
    return render_template('index.html', armed=armed)

# TODO: better way than using global variables, verify config
@app.route('/autosequence')
def autosequence():
    return render_template('autosequence.html')

    
@app.route('/pidview', methods=['GET'])
def pidview():
    return render_template('pidview.html', actuator_buttons=actuator_buttons, sensor_list=sensor_list, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states)

@app.route('/sensors', methods=['GET'])
def sensors():
    return render_template('sensors.html', sensor_list=sensor_list, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states)


@app.route('/actuators', methods=['GET'])
def actuators():
    return render_template('actuators.html', actuator_buttons=actuator_buttons, actuator_states_and_sensor_tare_states=actuator_states_and_sensor_tare_states)



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

@socketio.on('received_actuator_button_press')
def handle_actuator_button_press(buttonID, state, current_time):
    if armed:
        print('received actuator button press: ', buttonID, state, 'Delay:',(time.time_ns() // 1_000_000) - current_time)
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

        sensors_and_data[0][1] = random.random()*10
        
        # testing shows we get data at 3khz with random, 6khz with a predetermined constant; ex: 1
        # with open("sensor_data_log", mode='a', newline='') as csv_file:
        #     csv_writer = csv.writer(csv_file)
        #     csv_writer.writerow(sensors_and_data)

        # print("sensor is reading:", sensors_and_data[0][1])
        socketio.emit('sensor_data', [sensors_and_data, time.time_ns() // 1000000])

def ping_thread():
    while True:
        socketio.sleep(1)
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

if __name__ == '__main__':
    socketio.run(app)
