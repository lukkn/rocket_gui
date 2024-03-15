import csv
import re
import os

import networking

sensor_log_path = "logs/sensor_log_"

internal_temp = 20 # assume room temp
SCALE_INTERNAL_TEMP = True

sensor_TTL = 100 # number of packets sensor is considered alive without data

sensor_offset = {} # To keep track of taring
sensor_units = {}  # Store the units corresponding to each sensor P and ID
sensor_data_TTL = {} # Keeps track of how many more packets without data for a particular sensor before it is considered disconnected
raw_data_dict = {} # Contains raw sensor data
processed_data_dict = {} # Contains tared and unit converted data 

def initialize_sensor_info(sensor_list, config_name):

    csv_header_list = ['Timestamp (ms)']
    for sensor in sensor_list:
        sensor_offset[sensor['P and ID']] = 0
        sensor_data_TTL[sensor['P and ID']] = sensor_TTL
        sensor_units[sensor['P and ID']] = sensor["Unit"]
        csv_header_list.append(sensor["P and ID"] + "_raw")
        csv_header_list.append(sensor["P and ID"] + "_value")
        csv_header_list.append(sensor["P and ID"] + "_offset")
        raw_data_dict[sensor['P and ID']] = None
        processed_data_dict[sensor['P and ID']] = None

    # initialize sensor_log
    global sensor_log_path

    filenames = sorted(list(filter(lambda flname: "sensor_log" in flname, next(os.walk("logs"), (None, None, []))[2])), key=file_num_from_name)
    try:
        current_filenum = int(re.findall('\d+', filenames[-1])[0]) + 1
    except: 
        current_filenum = 0 

    sensor_log_path = "logs/sensor_log_" + str(current_filenum) + "_" + config_name + ".csv"
    with open(sensor_log_path, "w") as file:
        csv.writer(file).writerow(csv_header_list)
        file.flush()
        file.close()

def file_num_from_name(fname):
    return int(re.findall('\d+', fname)[0]) + 1

def get_sensor_data():
    global processed_data_dict
    return processed_data_dict

def tare(sensorID):
    sensor_offset[sensorID] = raw_data_dict[sensorID]

def untare(sensorID):
    sensor_offset[sensorID] = 0

def process_sensor_data(sensor_id, sensor_data):
    global internal_temp
    raw_value = sensor_data - sensor_offset[sensor_id]
    val_in_volts = raw_value / 1000.0
    processed_value = None

    match sensor_units[sensor_id]:
        case "PSI_S1k":
            processed_value = 250 * val_in_volts - 125
        case "PSI_H5k":
            processed_value = 1250 * 2 * val_in_volts - 625
        case "PSI_M1k":
            processed_value = (1000.0 * val_in_volts)/(0.100 * 128)
        case "PSI_M5k":
            processed_value = (5000.0 * val_in_volts)/(0.100 * 128)
        case "Degrees C":
            processed_value = (195.8363374*val_in_volts + 5.4986782) + internal_temp
        case "Volts":
            processed_value = val_in_volts
        case "C Internal":
            internal_temp = raw_value/1000 if SCALE_INTERNAL_TEMP else raw_value
        case "lbs_tank":
            processed_value = val_in_volts*1014.54 - 32.5314
        case "lbs_engine":
            processed_value = (-val_in_volts*5128.21 - 11.2821)/2
        case "alt_ft":
            processed_value = raw_value * 3.281 #m to ft. Dammit Kamer!
        case "g_force":
            processed_value = raw_value * 0.00102 # cm/s^2 to G
        case "loop_ms":
            processed_value = raw_value / 1_000
        case _ :
            pass
            print("Unexpected Unit")

    return processed_value


def log_sensor_data(timestamp, sensor_data_dict):
    data_to_log = [timestamp]
    for sensor in sensor_offset:
        raw_data = sensor_data_dict[sensor]
        processed_data = process_sensor_data(sensor_data_dict[sensor])
        # update raw and processed data in dictionaries
        raw_data_dict[sensor] = raw_data
        processed_data_dict[sensor] = processed_data
        # add data to be logged to file
        data_to_log.extend([raw_data, processed_data, sensor_offset[sensor]])
        # decrease sensor TTL
        for sensor in sensor_data_TTL:
            sensor_data_TTL[sensor] -= 1
            if sensor_data_TTL[sensor] == 0 :
                processed_data_dict[sensor] = None
                raw_data_dict[sensor] = None
                sensor_data_TTL[sensor] = sensor_TTL

    with open(sensor_log_path, "a") as file:
        csv.writer(file).writerow(data_to_log)
        file.flush()
        file.close()
