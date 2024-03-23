import csv
import os

CONFIG_FILE = 'FlaskGUI/m5_config.csv'

def get_interface_type_number(interface_name):
    if interface_name == 'servoPWM_12V':
        print("12 Volt Servo")
        return 5
    if interface_name == 'Bang-Bang':
        return 41
    if interface_name == 'FireX':
        return 42
    if interface_name == 'Heartbeat':
        return 43
    if interface_name == 'Clear_Config':
        return 44
    if interface_name == "Start_Log":
        return 45
    interface_list = ['Teensy ADC', 'i2c ADC 1ch', 'i2c ADC 2ch',
                      'FlowMeterCounter', 'servoPWM', 'Binary GPIO',
                      'i2c ADC 2ch PGA2', 'i2c ADC 2ch PGA4', 'i2c ADC 2ch PGA8',
                      'i2c ADC 2ch PGA16', 'i2c ADC 2ch PGA32', 'i2c ADC 2ch PGA64',
                      'i2c ADC 2ch PGA128', 'ADC Internal Temp', 'SPI_ADC_1ch', 
                      'SPI_ADC_2ch', 'SPI_ADC_2ch PGA2', 'SPI_ADC_2ch PGA4', 'SPI_ADC_2ch PGA8', 
                      'SPI_ADC_2ch PGA16', 'SPI_ADC_2ch PGA32', 'SPI_ADC_2ch PGA64', 'SPI_ADC_2ch PGA128',
                      'Icarus_ALT', 'Icarus_IMU', 'Volt_Monitor', 'Loop_Timer']

    # +1 because interface numbers start at 1, not 0
    return interface_list.index(interface_name) + 1


def check_file_header(header_list):
    example_header = ['Mote id', 'Sensor or Actuator', 'Interface Type', 'Human Name', 'Pin', 'P and ID', 'Unit', 'Unpowered State']
    return header_list == example_header

def load_config(file=CONFIG_FILE):
    actuators = []
    sensors = []
    decoded_string = file.decode('utf-8')
    lines = decoded_string.strip().split('\n')

    config_dict = csv.DictReader(lines)

    if not check_file_header(list(list(config_dict)[0].keys())):
        raise Exception("header error")

    for row in csv.DictReader(lines):
        if row['Sensor or Actuator'] == 'actuator':
            actuators.append(row)
        elif row['Sensor or Actuator'] == 'sensor':
            sensors.append(row)
        else:
            print('Error parsing CSV sensor or actuator column')
            print(row)
    return actuators, sensors


