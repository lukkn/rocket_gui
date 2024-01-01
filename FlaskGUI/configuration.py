import csv

CONFIG_FILE = '../m5_config.csv'

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
                      'SPI_ADC_2ch PGA16', 'SPI_ADC_2ch PGA32', 'SPI_ADC_2ch PGA64', 'SPI_ADC_2ch PGA128']

    # +1 because interface numbers start at 1, not 0
    return interface_list.index(interface_name) + 1



def load_config(file=CONFIG_FILE):
    actuators = []
    sensors = []
    decoded_string = file.decode('utf-8')
    lines = decoded_string.strip().split('\n')
    print("these are the lines of the config: ", lines)
    for row in csv.DictReader(lines):
        print("each row: ", row)
        if row['Sensor or Actuator'] == 'actuator':
            actuators.append(row)
        elif row['Sensor or Actuator'] == 'sensor':
            sensors.append(row)
        else:
            print('Error parsing CSV sensor or actuator column')
            print(row)
    return actuators, sensors

def load_auto_test(file_name):
    commands = []
    with open(file_name, 'r') as f:
        for row in csv.DictReader(f):
            commands.append(row)

    return commands

def load_setpoint_csv(file_name='../Autoseq/abort_redline.csv'):
    setpoints = []
    with open(file_name):
        with open(file_name, 'r') as f:
            for row in csv.DictReader(f):
                sens = list(filter(lambda a : a['P and ID'] == row['P and ID'], load_config()[1]))[0]
                sensor_id = (sens['Mote id'], sens['Pin'])

                setpoints.append({**row,**{'ID': sensor_id}})
    
    return setpoints

try:
    setpoints = load_setpoint_csv()
except:
    print("Unable to load setpoints")

