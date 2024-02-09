from ast import arg
import imp
from labjack import ljm
from gi.repository import GLib
from threading import Thread
import time

import networking

lj_handles = {}

def init_lj(id):
    #handle = ljm.openS("T4", "Ethernet", str(networking.get_ip(id)))
    try:
        handle = ljm.openS("T4", "Ethernet", str(networking.get_ip(id)))
    except:
        print(f"Could not connect to labjack {id}")
        return -1
    return handle

def get_lj_adcs(sensors, labels):
    #iterate over all the sensors
    for sensor in sensors:
        #device is a labjack
        if int(sensor['Mote id']) >= 10:
            #single-ended
            if sensor['Interface Type'] == 'i2c ADC 1ch':
                handle = lj_handles[sensor['Mote id']]
                value = ljm.eReadName(handle, sensor["Pin"])

                value = round(value, 2)
                sensor_id = (sensor['Mote id'], sensor["Pin"])
                GLib.idle_add(
                        labels[sensor_id].set_text, str(value))
            elif sensor['Interface Type'] == 'i2c ADC 2ch':
                pins = sensor["Pin"].split('-')
                handle = lj_handles[sensor['Mote id']]
                val1 = ljm.eReadName(handle, pins[0])
                val2 = ljm.eReadName(handle, pins[1])
                value = val1 - val2

                value = round(value, 2)
                sensor_id = (sensor['Mote id'], sensor["Pin"])
                GLib.idle_add(
                        labels[sensor_id].set_text, str(value))
            else:
                print("sensor not supported on labjack")
                pass

def connect_ljs(sensors):
    global lj_handles
    lj_handles = {}

    print("connecting labjacks")
    for sensor in sensors:
        if sensor['Mote id'] not in lj_handles.keys():
            print(f"connecting LJ {sensor['Mote id']}")
            lj_handles[sensor['Mote id']] = init_lj(sensor['Mote id'])
            print(lj_handles[sensor['Mote id']])
    
def start_lj_thread(sensors, labels):
    connect_ljs(sensors)

    def lj_loop(sensors, labels):
        while True:
            try:
                get_lj_adcs(sensors, labels)
            except:
                pass
            time.sleep(0.05)

    lj_thread = Thread(target=lj_loop, args=(sensors, labels), daemon=True)
    lj_thread.start()
