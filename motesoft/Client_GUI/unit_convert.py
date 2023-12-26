import configuration

internal_temp = 20 #assume room temp
tares = {}

actuators, sensors = configuration.load_config()

for sensor in sensors:
    sensor_id = (sensor['Mote id'], sensor['Pin'])
    tares[sensor_id] = 0

def tare(button, *data):
    sensor_id = data[0]
    try:
        sensor_value = float(data[1][sensor_id].get_text())
    except:
        return
    tares[sensor_id] = -sensor_value
    print(f"tared sensor {data[0]}")

def untare(button, *data):
    print(f"Reset tare on sensor {data[0]}")
    tares[data[0]] = 0

def unit_handler(val, sensor_id):
    #sensor id is (board number, pin number)
    if int(sensor_id[1]) == 14:
        return val/1000
    if int(sensor_id[1]) >= 64:
        return adc_to_volts(val)
    return val

#convert ADC units to volts or other volt-converted units
def adc_handler(val, sensor_id):
    val = adc_to_volts(val)
    return val;

def adc_to_volts(val):
    return (val-2147483648)/4096000

#convert volt to specific units

def volts_to_psi5k(val):
    #MLH05KPSL06A
    #0-5000 psi, 0.5-4.5v
    return 1250 * 2 * val - 625;

def volts_to_psi1k(val, double=True):
    #P51-1000-S-B-136-4.5V
    #0-1000 psi, 0.5-4.5v
    if double:
        return 2 * 250 * val - 125
    else:
        return 250 * val - 125

def volts_to_degC(val):
    return 195.8363374*val + 5.4986782

def volts_to_lbs_tank(val):
    #return val/0.0008
    return val*1014.54 - 32.5314

def volts_to_lbs_engine(val):
    return (-val*5128.21 - 11.2821)/2

