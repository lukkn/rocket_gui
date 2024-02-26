import networking
import csv

sensor_log_path = "FlaskGUI/logs/sensor_log_0.csv"

internal_temp = 20 # assume room temp
SCALE_INTERNAL_TEMP = False

sensor_offset = {}
sensor_units = {}
sensor_mote = {}

def initialize_sensor_info(sensor_list):
    header = ["Timestamp"]

    for sensor in sensor_list:
        sensor_offset[sensor['P and ID']] = 0
        sensor_units[sensor['P and ID']] = sensor["Unit"]
        sensor_mote[sensor['P and ID']] = sensor['Mote id']
        header.append(sensor["P and ID"])

    # initialize sensor_log
    with open(sensor_log_path, "w") as file:
        csv.writer(file).writerow(header)
        file.flush()
        file.close()


def get_sensor_data():
    sensor_data_dict = unit_convert(networking.get_sensor_data())
    for sensor in sensor_data_dict:
        sensor_data_dict[sensor] = sensor_data_dict[sensor] - sensor_offset[sensor]
    return sensor_data_dict

def tare(sensorID):
    sensor_offset[sensorID] = networking.get_sensor_data()[sensorID]


def untare(sensorID):
    sensor_offset[sensorID] = 0


def unit_convert(sensor_data_dict):
    for sensor in sensor_data_dict:

        # convert adc to volts
        raw_value = sensor_data_dict[sensor]
        val_in_volts = (raw_value-2147483648)/4096000

        match sensor_units[sensor]:
            case "PSI_1K":
                if sensor_mote[sensor] == '2': # if mote 2
                    raw_value = 250 * val_in_volts - 125
                else:
                    raw_value = 2* 250 * val_in_volts - 125

            case "PSI_5k":
                raw_value = 1250 * 2 * val_in_volts - 625
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
            case _ :
                print("Unexpected Unit")
    return sensor_data_dict


def log_sensor_data(timestamp, sensor_data_dict):

    data_to_log = {}
    data_to_log['Timestamp'] = timestamp
    unit_converted_data = unit_convert(sensor_data_dict)

    for sensor in sensor_offset:
        if sensor in sensor_data_dict:
            data_to_log[sensor] = str([sensor_data_dict[sensor], unit_converted_data[sensor], sensor_offset[sensor]])
        else: 
            data_to_log [sensor] = None

    with open(sensor_log_path, "a") as file:
        writer = csv.DictWriter(file, data_to_log.keys())
        writer.writerow(data_to_log)
        file.flush()
        file.close()
