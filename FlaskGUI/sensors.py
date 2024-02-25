import networking

sensor_offset = {}

def initialize_sensor_offset(sensor_list):
    for sensor in sensor_list:
        sensor_offset[sensor['P and ID']] = 0


def get_sensor_data():
    sensor_data_dict = networking.get_sensor_data()
    tared_data = []
    for sensor in sensor_data_dict: 
        sensor_data_dict[sensor] = sensor_data_dict[sensor] - sensor_offset[sensor]
    return tared_data
 
def tare(sensorID):
    sensor_offset[sensorID] = networking.get_sensor_data()[sensorID]

 
def untare(sensorID):
    sensor_offset[sensorID] = 0