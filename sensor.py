import csv
from datetime import datetime

import networking

sensor_log_path = "logs/sensor_log_"

internal_temp = 20 # assume room temp
SCALE_INTERNAL_TEMP = True

sensor_offset = {}
sensor_units = {}

def initialize_sensor_info(sensor_list):

    csv_header_list = ['Timestamp (ms)']
    for sensor in sensor_list:
        sensor_offset[sensor['P and ID']] = 0
        sensor_units[sensor['P and ID']] = sensor["Unit"]
        csv_header_list.append(sensor["P and ID"] + "_raw")
        csv_header_list.append(sensor["P and ID"] + "_value")
        csv_header_list.append(sensor["P and ID"] + "_offset")

    # initialize sensor_log
    global sensor_log_path
    dt_string = datetime.now().strftime("%d%m%Y_%H%M%S")
    sensor_log_path += dt_string + ".csv"
    with open(sensor_log_path, "w") as file:
        csv.writer(file).writerow(csv_header_list)
        file.flush()
        file.close()


def get_sensor_data():
    sensor_data_dict = networking.get_sensor_data()
    processed_data_dict = {}
    for sensor in sensor_data_dict:
        processed_data_dict[sensor] = sensor_data_dict[sensor] - sensor_offset[sensor]
    return processed_data_dict


def tare(sensorID):
    sensor_offset[sensorID] = networking.get_sensor_data()[sensorID]


def untare(sensorID):
    sensor_offset[sensorID] = 0

def process_sensor_dict(sensor_data_dict):
    processed_dict = {}
    global internal_temp

    for sensor in sensor_data_dict:
        raw_value = sensor_data_dict[sensor] - sensor_offset[sensor]
        val_in_volts = raw_value / 1000.0

        match sensor_units[sensor]:
            case "PSI_S1k":
                raw_value = 250 * val_in_volts - 125
            case "PSI_H5k":
                raw_value = 1250 * 2 * val_in_volts - 625
            case "PSI_M1k":
                raw_value = (1000.0 * val_in_volts)/(0.100 * 128)
            case "PSI_M5k":
                raw_value = (5000.0 * val_in_volts)/(0.100 * 128)
            case "Degrees C":
                raw_value = (195.8363374*val_in_volts + 5.4986782) + internal_temp
            case "Volts":
                raw_value = val_in_volts
            case "C Internal":
                internal_temp = raw_value/1000 if SCALE_INTERNAL_TEMP else raw_value
            case "lbs_tank":
                raw_value = val_in_volts*1014.54 - 32.5314
            case "lbs_engine":
                raw_value = (-val_in_volts*5128.21 - 11.2821)/2
            case "alt_ft":
                raw_value = raw_value * 3.281 #m to ft. Dammit Kamer!
            case "g_force":
                raw_value = raw_value * 0.00102 # cm/s^2 to G
            case _ :
                pass
                #print("Unexpected Unit")
        
        processed_dict[sensor] = raw_value

    return processed_dict


def log_sensor_data(timestamp, sensor_data_dict):

    processed_data_dict = process_sensor_dict(sensor_data_dict)
    data_to_log = [timestamp]

    for sensor in sensor_offset:
        try:
            data_to_log.extend([sensor_data_dict[sensor], processed_data_dict[sensor], sensor_offset[sensor]])
        except: 
            data_to_log.extend([None, None, None])

    with open(sensor_log_path, "a") as file:
        csv.writer(file).writerow(data_to_log)
        file.flush()
        file.close()
