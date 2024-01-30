import imp
import os
import csv
from random import random
import threading
import time
from threading import Thread
from configuration import load_config
import numpy as np
import re
import random

gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk, Gdk, GObject
from matplotlib.backends.backend_gtk3agg import (
    FigureCanvasGTK3Agg as FigureCanvas)
from matplotlib.figure import Figure

sensor_log_path = "../Logs/sensor_log_0.csv"
cmd_log_path = "../Logs/cmd_log_0.csv"
actuator_log_path = "../Logs/actuator_log_0.csv"

actuators, sensors = load_config()

print(len(sensors), "len sensors")
sensor_log_values_keys = []
for sensor in sensors:
    if sensor['unit'] == "Degrees C":
        sensor_log_values_keys.extend([(sensor['Mote id'], sensor['Pin']), (sensor['Mote id'], sensor['Pin'] + "V")])
    else:
        sensor_log_values_keys.append((sensor['Mote id'], sensor['Pin']))
    
sensor_log_values = dict.fromkeys(sensor_log_values_keys)

N_ROLLING_VALUES = 30
sensor_log_rolling_avg = dict.fromkeys(sensor_log_values_keys)
for k in sensor_log_values.keys():
    sensor_log_values[k] = "None"
    sensor_log_rolling_avg[k] = ["None", np.zeros(N_ROLLING_VALUES)]

def update_rolling_values(k, value):
    sensor_log_rolling_avg[k][1] = np.roll(sensor_log_rolling_avg[k][1], -1)
    sensor_log_rolling_avg[k][1][0] = value
    sensor_log_rolling_avg[k][0] = np.mean(sensor_log_rolling_avg[k][1])
    #print("updated", k)

def append_sensor_log_file(data):
    with open(sensor_log_path, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)
        f.flush()
        f.close()

def file_num_from_name(fname):
    return int(re.findall('\d+', fname)[0]) + 1

def init_sensor_log():
    print("init method called")
    filenames = sorted(list(filter(lambda flname: "sensor_log" in flname, next(os.walk("../Logs"), (None, None, []))[2])),
        key=file_num_from_name)
    try:
        #current_filenum = int(filenames[-1][-5]) + 1
        current_filenum = int(re.findall('\d+', filenames[-1])[0]) + 1
        print(filenames)
        print(f'current filenum = {current_filenum}')
    except:
        print("OY!")
        current_filenum = 0

    global sensor_log_path
    sensor_log_path = f"../Logs/sensor_log_{current_filenum}.csv"

    with open(sensor_log_path, 'w') as csvfile:
        #csv.writer(csvfile).writerow(['Time(ms)'] + [sensor['Human Name'] for sensor in sensors])
        header = ['Time(ms)']
        for sensor in sensors:
            if sensor['unit'] == "Degrees C":
                header.extend([sensor['Human Name'] + " Degrees C", sensor['Human Name'] + " Volts"])
            else:
                header.append(sensor['Human Name'])
        csv.writer(csvfile).writerow(header)
        csvfile.flush()
        csvfile.close()

def append_cmd_log_file(data):
    with open(cmd_log_path, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)
        f.flush()
        f.close()

def init_cmd_log():
    filenames = sorted(list(filter(lambda flname: "cmd_log" in flname, next(os.walk("../Logs"), (None, None, []))[2])),
        key=file_num_from_name)

    try:
        current_filenum = int(re.findall('\d+', filenames[-1])[0]) + 1
    except:
        current_filenum = 0

    global cmd_log_path
    cmd_log_path = f"../Logs/cmd_log_{current_filenum}.csv"

    with open(cmd_log_path, 'w') as csvfile:
        csv.writer(csvfile).writerow(['Time(ms)', 'MoTE', 'Pin', 'State', 'P&ID'])
        csvfile.flush()
        csvfile.close()

actuator_states = {}
for actuator in actuators:
    actuator_states[actuator['P and ID']] = False

actuator_acks = {}
for actuator in actuators:
    actuator_acks[(int(actuator['Mote id']), int(actuator['Pin']))] = False


def append_actuator_log_file(time):
    data = [time] + list(actuator_states.values())
    with open(actuator_log_path, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)
        f.flush()
        f.close()

def init_actuator_log():
    filenames = sorted(list(filter(lambda flname: "actuator_log" in flname, next(os.walk("../Logs"), (None, None, []))[2])),
        key=file_num_from_name)

    try:
        current_filenum = int(re.findall('\d+', filenames[-1])[0]) + 1
    except:
        current_filenum = 0

    global actuator_log_path
    actuator_log_path = f"../Logs/actuator_log_{current_filenum}.csv"

    with open(actuator_log_path, 'w') as csvfile:
        csv.writer(csvfile).writerow(['Time(s)'] + [actuator['P and ID'] for actuator in actuators])
        csvfile.flush()
        csvfile.close()

DEBUG_MODE = False

data = None
points = [[None for j in range(len(sensors))] for i in range(max([int(s['window']) for s in sensors]) + 1)]
bgs = [None for _ in range(max([int(s['window']) for s in sensors]) + 1)]

log_time_interval_s = 0.1
def update_graph(graphs, sensor_value_gtk_labels, sensor_value_gtk_toggle, m_interval=10):
    global data
    if data is None:
        data = np.zeros((len(sensors), int(m_interval/log_time_interval_s)))
        print(f'len(data) = {len(data[0])}')

    for n, g in enumerate(graphs):
        canvas, ax, fig = g
        if DEBUG_MODE:
            sensor_values = [random.random() for i in range(len(sensors))]
        else:
            try:
                sensor_values = [sensor_value_gtk_labels[(sensor['Mote id'], sensor['Pin'])].get_text() for sensor in sensors]
            except:
                return True
        sensor_toggles = [sensor_value_gtk_toggle[(sensor['Mote id'], sensor['Pin'])].get_active() for sensor in sensors]
        #print(sensor_toggles)
        #ax.clear()
        x = np.arange(-m_interval, 0, log_time_interval_s)
        #print(sensor_values)
        for i, val in enumerate(sensor_values):
            if val != 'loading...' and val != "NO CONNECTION" and sensor_toggles[i] and sensors[i]['window'] == str(n):
                data[i] = np.roll(data[i], -1)
                data[i][-1] = float(val)
                #ax.plot(x, data[i], label=sensors[i]['Human Name'])
                if points[n][i] == None:
                    points[n][i], = ax.plot(x, data[i], label=sensors[i]['Human Name'], animated=True)
                    bgs[n] = fig.canvas.copy_from_bbox(ax.get_figure().bbox)
                else:
                    points[n][i].set_ydata(data[i])
        canvas.restore_region(bgs[n])
        for i in range(len(sensor_values)):
            ax.draw_artist(points[n][i])
        canvas.blit(ax.clipbox)
        #if 'loading...' not in sensor_values and not (True not in sensor_value_gtk_toggle):
        #    ax.legend(loc='upper left')
        #time.sleep(log_time_interval_s)

    return True
    
SENSOR_RATE_HZ = 10
class GraphWindow(Gtk.ScrolledWindow):
    def __init__(self, num, sensor_gtk_labels, sensor_gtk_toggles):
        Gtk.ScrolledWindow.__init__(self)

        self.num = num
        self.num_sensors = len([s for s in sensors if s['window'] == str(self.num)])
        self.sensor_gtk_labels = sensor_gtk_labels
        self.sensor_gtk_toggles = sensor_gtk_toggles

        self.background = None
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot()
        #self.ax.set_yticks(np.arange())

        self.add_with_viewport(self.canvas)

        self.data = np.zeros((len(sensors), SENSOR_RATE_HZ))
        self.plots = [None for i in range(len(sensors))]

        for i, sensor in enumerate(sensors):
            if sensor['window'] == str(num):
                plot_temp, = self.ax.plot(np.arange(-10, 0, 10/SENSOR_RATE_HZ), self.data[i], label=sensors[i]['Human Name'], animated=True)
                self.plots[i] = plot_temp

        self.ax.legend(loc='upper left')

        self.canvas.mpl_connect("draw_event", self.on_draw)
        GObject.timeout_add(1000/SENSOR_RATE_HZ, self.update_graph)

    def update_graph(self):
        #aquire data
        if not DEBUG_MODE:
            sensor_values = [self.sensor_gtk_labels[(sensor['Mote id'], sensor['Pin'])].get_text() for sensor in sensors]
        else:
            sensor_values = [random.random() * 100 + 1000 for i in range(len(sensors))]

        #print(self.sensor_gtk_toggles)
        sensor_toggles = [self.sensor_gtk_toggles[(sensor['Mote id'], sensor['Pin'])].get_active() for sensor in sensors]
        for i, val in enumerate(sensor_values):
            if val != 'loading...' and val != "NO CONNECTION" and sensor_toggles[i] and sensors[i]['window'] == str(self.num):
                self.data[i] = np.roll(self.data[i], -1)
                self.data[i][-1] = float(val)
        #display data
        try:
            self.ax.set_ylim(
            min([float(s['min']) for s in sensors if s['window'] == str(self.num)]),
            max([float(s['max']) for s in sensors if s['window'] == str(self.num)])
            )
            for i, plot in enumerate(self.plots):
                if plot != None:
                    plot.set_ydata(self.data[i])
                    plot.set_visible(sensor_toggles[i])
            self.fig.canvas.restore_region(self.background)
            for plot in self.plots:
                if plot != None:
                    self.ax.draw_artist(plot)
            self.fig.canvas.blit(self.ax.clipbox)
        except Exception as e:
            #print(e)
            pass

        return True

    def save_bg(self):
        self.background = self.fig.canvas.copy_from_bbox(self.ax.get_figure().bbox)

    def on_draw(self, *args):
        self.save_bg()
        return False

init_sensor_log()
init_cmd_log()
init_actuator_log()