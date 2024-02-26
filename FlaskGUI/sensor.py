import networking

internal_temp = 20 # assume room temp
SCALE_INTERNAL_TEMP = False

sensor_offset = {}
sensor_units = {}
sensor_mote = {}

def initialize_sensor_info(sensor_list):
    for sensor in sensor_list:
        sensor_offset[sensor['P and ID']] = 0
        sensor_units[sensor['P and ID']] = sensor["Unit"]
        sensor_mote[sensor['P and ID']] = sensor['Mote id']

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
    for sensor, value in sensor_data_dict:

        # convert adc to volts
        val_in_volts = (value-2147483648)/4096000

        match sensor['Unit']:
            case "PSI_1K":
                if sensor_mote[sensor] == '2': # if mote 2
                    value = 250 * val_in_volts - 125
                else:
                    value = 2* 250 * val_in_volts - 125

            case "PSI_5k":
                value = 1250 * 2 * val_in_volts - 625
            case "Degrees C":
                value = (195.8363374*val_in_volts + 5.4986782) + internal_temp
            case "Volts":
                value = val_in_volts
            case "C Internal":
                internal_temp = value/1000 if SCALE_INTERNAL_TEMP else value
            case "lbs_tank":
                value = val_in_volts*1014.54 - 32.5314
            case "lbs_engine":
                value = (-val_in_volts*5128.21 - 11.2821)/2
            case _ :
                print("Unexpected Unit")
    return sensor_data_dict
