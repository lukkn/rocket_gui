import csv
import re
import os
import ast
import time

sensor_log_path = "logs/sensor_log_"

internal_temp = 20 # assume room temp
SCALE_INTERNAL_TEMP = False

sensor_TTL = 100 # number of polls sensor is considered alive without data (20 polls = 1 second)

sensor_offset = {} # To keep track of taring
sensor_units = {}  # Store the units corresponding to each sensor P and ID
sensor_data_TTL = {} # Keeps track of how many more polls can be without new data for a sensor before it is considered disconnected
raw_data_dict = {} # Contains raw sensor data
processed_data_dict = {} # Contains tared and unit converted data 
config_file_name = None

def initialize_sensor_info(sensor_list, config_name): 
    global config_file_name
    config_file_name = config_name
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

    sensor_offset_from_csv = {}
    try: 
        with open('./static/sensor_offset_' + config_file_name + '.csv', mode='r', newline='') as file:
            csv_reader = csv.reader(file)
            csv_dict = next(csv_reader, None)[0] # reads first row, before any comma outside double quotes
            sensor_offset_from_csv = ast.literal_eval(csv_dict) # parses string dict to a python dict, preserving data types
        for key in sensor_offset_from_csv: # update sensor_offset with offsets from the csv if they exist in sensor_offset, meaning in our current config
            if key in sensor_offset:
                sensor_offset[key] = sensor_offset_from_csv[key]
    except:
        print ("no offset file found")

    # initialize sensor_log
    global sensor_log_path
    global folder_path 
    

    if not os.path.exists("logs"): 
        print("directory for logs created! ")
        os.mkdir("logs")
    
    folder_name = time.strftime("%Y-%m-%d") + "_" + config_name 
    folder_path = os.path.join("logs",folder_name)

    if not os.path.exists(folder_path): 
        print(f"Creating {folder_name}")
        os.mkdir(folder_path)




    filenames = sorted(
        list(filter(lambda flname: re.search(r'sensors_\d+\.csv', flname), 
        next(os.walk(folder_path), (None, None, []))[2])),
        key=lambda flname: int(re.search(r'\d+', flname).group())
    )

    try:
        current_filenum = int(re.findall(r'\d+', filenames[-1])[0]) + 1 # r makes python interpret \ as a regular character instead of an escape character
    except: 
        current_filenum = 1

    sensor_filename = f"sensors_{current_filenum}.csv"
    sensor_log_path = os.path.join(folder_path, sensor_filename)
    print(sensor_log_path)
    with open(sensor_log_path, "w", newline="") as file:
        writer = csv.writer(file) 
        writer.writerow(csv_header_list)
        file.flush()
        file.close()

def file_num_from_name(fname):
    try:
        return int(re.findall(r'\d+', fname)[0]) + 1 # r makes python interpret \ as a regular character instead of an escape character
    except:
        return 0

def get_sensor_data():
    global processed_data_dict
    global raw_data_dict
    # decrease sensor TTL
    for sensor in sensor_data_TTL:
        if sensor_data_TTL[sensor] > 0 :
            sensor_data_TTL[sensor] -= 1
        else:
            processed_data_dict[sensor] = None
            raw_data_dict[sensor] = None
    return processed_data_dict

def tare(sensor_id):
    if sensor_offset[sensor_id] == 0:
        sensor_offset[sensor_id] = processed_data_dict[sensor_id]
        writeTare_Untare()

def untare(sensor_id):
    sensor_offset[sensor_id] = 0
    writeTare_Untare()

def writeTare_Untare():
    global config_file_name
    with open('./static/sensor_offset_' + config_file_name + '.csv', mode='w', newline='') as file: # clears file on open
        writer = csv.writer(file)
        writer.writerow([sensor_offset])

load_cell_filter = 0

def process_sensor_data(sensor_id, sensor_data):
    global internal_temp
    val_in_volts = sensor_data / 1e6
    processed_value = None

    match sensor_units[sensor_id]:
        case "Volts":
            processed_value = val_in_volts
        case "PSI_S1k":
            processed_value = 250 * val_in_volts - 125
        case "PSI_H5k":
            processed_value = 1250 * val_in_volts - 625
        case "PSI_M1k":
            processed_value = (1000.0 * val_in_volts)/(0.100 * 128)
        case "PSI_M5k":
            processed_value = (5000.0 * val_in_volts)/(0.100 * 128)
        case "Degrees C":
            processed_value = (195.8363374*val_in_volts + 5.4986782) + internal_temp
        case "Volts":
            processed_value = val_in_volts
        case "C Internal":
            internal_temp = sensor_data/1000 if SCALE_INTERNAL_TEMP else sensor_data
            processed_value = internal_temp
        case "lbs_tank":
            processed_value = val_in_volts*1014.54 - 32.5314
        case "lbs_engine":
            processed_value = (-val_in_volts*5128.21 - 11.2821)/2
        case "alt_ft":
            processed_value = sensor_data * 3.281 #m to ft. Dammit Kamer!
        case "alt_hpa":
            processed_value = sensor_data / 1000 # dpa to hpa
        case "alt_C":
            processed_value = sensor_data / 1000 # to degrees C
        case "g_force":
            processed_value = sensor_data * 0.00102 # cm/s^2 to G
        case "loop_ms":
            processed_value = sensor_data / 1_000
        case "Rail_Voltage":
            processed_value = val_in_volts * 23 * 1000
        case "Lora_Data":
            processed_value = sensor_data
        case "lbm_10k":
            global load_cell_filter
            processed_value = -5116.72 * val_in_volts + 59.7549
            load_cell_filter = processed_value * 0.1 + load_cell_filter * 0.9
            processed_value = load_cell_filter
        case _ :
            pass
            print("Unexpected Unit")

    return processed_value - sensor_offset[sensor_id]


def log_sensor_data(timestamp, sensor_data_dict):
    data_to_log = [timestamp]
    for sensor in sensor_offset:
        try:
            raw_data = sensor_data_dict[sensor]
            processed_data = process_sensor_data(sensor, sensor_data_dict[sensor]) 
            sensor_data_TTL[sensor] = sensor_TTL
            # update raw and processed data in dictionaries
            raw_data_dict[sensor] = raw_data
            processed_data_dict[sensor] = processed_data
            # add data to be logged to file
            data_to_log.extend([raw_data, processed_data, sensor_offset[sensor]])
        except: 
            data_to_log.extend([None, None, None])
    with open(sensor_log_path, "a") as file:
        csv.writer(file).writerow(data_to_log)
        file.flush()
        file.close()
