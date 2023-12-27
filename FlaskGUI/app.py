from flask import Flask, render_template, request, redirect, url_for, jsonify
import csv
import json
import os

# GLOBAL VARIABLES
actuator_buttons = []
sensors = []


app = Flask(__name__, static_url_path='/static')

#TODO: try except logic
def load_config(config_bytes):
    decoded_string = config_bytes.decode('utf-8')
    lines = decoded_string.strip().split('\n')
    config_list = [row for row in csv.reader(lines)]
    
    actuator_buttons = [row for row in config_list if row[1] == 'actuator']
    sensors = [row for row in config_list if row[1] == 'sensor']

    return actuator_buttons, sensors



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        buttonID = request.form.get('button')

        if buttonID == 'Button 2':
            return redirect(url_for('actuators'))

    return render_template('index.html')


# TODO: better way than using global variables, verify config
@app.route('/loadconfig', methods=['GET', 'POST'])
def loadconfig():
    global actuator_buttons, sensors
    if request.method == 'POST':
        buttonID = request.form.get('button')

        if buttonID == 'Button 1':
            config_bytes = request.files['file'].read()
            actuator_buttons, sensors = load_config(config_bytes)

    return render_template('loadconfig.html')

    
@app.route('/actuators', methods=['GET', 'POST'])
def actuators():
    if request.method == 'POST':
        data = request.get_json()
        #TODO: depending on button shape run some network functions
        print(data)
    return render_template('actuators.html', actuator_buttons=actuator_buttons)


@app.route('/update_coordinates', methods=['POST'])
def update_coordinates():
    data = request.get_json()
    coordinates = data.get('coordinates', [])
    print("Received coordinates:", coordinates)
    # You can process the coordinates here as needed
    with open(os.path.dirname(os.path.abspath(__file__)) + '/static/coordinates.json', 'r') as file:
        json.dump(coordinates, file)
    return jsonify({'message': 'Coordinates received successfully'})


@app.route('/get_coordinates', methods=['GET'])
def get_coordinates():
    # Retrieve coordinates from file
    with open(os.path.dirname(os.path.abspath(__file__)) + '/static/coordinates.json', 'r') as file:

        coordinates = json.load(file)
    return jsonify({'coordinates': coordinates})





if __name__ == '__main__':
    app.run(debug=True)
