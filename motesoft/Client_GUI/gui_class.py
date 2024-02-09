from cProfile import label
from ctypes import alignment
from faulthandler import disable
import threading

from matplotlib.pyplot import autoscale
import networking
import sensor_logging
import os

# gi.require_version("Gtk", "3.0") must be before from gi.repository import Gtk
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GObject

import datetime
from threading import Thread, Timer
import time
import configuration
import sensor_logging
import autoseq
import hts_labjack
import unit_convert

from matplotlib.backends.backend_gtk3agg import (
    FigureCanvasGTK3Agg as FigureCanvas)
from matplotlib.figure import Figure
import numpy as np

class Handler:
    def __init__(self, sensors, actuators, builder):
        self.sensors = sensors
        self.actuators = actuators
        self.builder = builder
        self.is_armed = False

        GLib.threads_init()
        lock = threading.Lock()

        self.sensor_value_gtk_labels = {}
        self.sensor_value_gtk_slider = {}
        self.sensor_value_gtk_toggle = {}

        global actuator_switches
        actuator_switches = {1:{}, 2:{}, 3:{}, 4:{}}

        global setpoint_toggle_button   
        setpoint_toggle_button = Gtk.Switch()

        NUM_SENSOR_WINDOWS = max([int(s['window']) for s in sensors]) + 1
        #NUM_SENSOR_WINDOWS = 1

        # set up sensor window
        self.sensor_windows = [Gtk.Window(title=f"Sensors {i}", default_width=1000, default_height=600) for i in range(1, NUM_SENSOR_WINDOWS + 1)]
        self.graph_windows = [Gtk.Window(title=f"Sensors {i} Graph", default_width=1000, default_height=600) for i in range(1, NUM_SENSOR_WINDOWS + 1)]
        
        for i in range(NUM_SENSOR_WINDOWS):
            self.sensor_windows[i].props.deletable=False
        
        for i, sensor_window in enumerate(self.sensor_windows):

            list_box = Gtk.ListBox()

            sensor_grid = Gtk.FlowBox()
            #sensor_grid.set_max_children_per_line(3)

            for sensor in [s for s in sensors if s['window'] == str(i)]:
                row = Gtk.FlowBoxChild()
                row_box = Gtk.Box()
                row_box.add(Gtk.Label(
                    label=sensor['Human Name'], xalign=0, selectable=True, ypad=10, can_focus=False, expand=True))
                sensor_id = (sensor['Mote id'], sensor['Pin'])

                self.sensor_value_gtk_labels[sensor_id] = Gtk.Label(
                    label='loading...', xalign=0, selectable=True, ypad=10, can_focus=False)
                
                row_box.add(self.sensor_value_gtk_labels[sensor_id])

                #load cell pound force
                #pressure transducer psi
                #thermocouple celcius
                row_box.add(Gtk.Label(label=sensor['unit'], xalign=0, selectable=True,
                            ypad=10, can_focus=False, width_request=60, margin_start=5))

                tare_button = Gtk.Button(label="Tare", xalign=-10)
                tare_button.connect("clicked", unit_convert.tare, sensor_id, self.sensor_value_gtk_labels)
                untare_button = Gtk.Button(label="Untare", xalign=-10)
                untare_button.connect("clicked", unit_convert.untare, sensor_id, self.sensor_value_gtk_labels)

                row_box.add(tare_button)
                row_box.add(untare_button)
                
                check_box = Gtk.CheckButton()
                check_box.set_active(True)
                self.sensor_value_gtk_toggle[sensor_id] = check_box
                row_box.add(check_box)

                slider = Gtk.ProgressBar()
                slider.set_text(f"{sensor['min']}\t\t\t\t\t\t{sensor['max']}")
                slider.set_show_text(True)
                self.sensor_value_gtk_slider[sensor_id] = (slider, sensor['min'], sensor['max'])
                row_box.add(slider)

                row.add(row_box)
                sensor_grid.add(row)

            list_box.add(sensor_grid)
            
            viewport = Gtk.Viewport()
            viewport.add(list_box)

            scrolledwindow = Gtk.ScrolledWindow()
            scrolledwindow.add(viewport)
        
            sensor_window.add(scrolledwindow)

        for n, graph_window in enumerate(self.graph_windows):
            graph = sensor_logging.GraphWindow(n, self.sensor_value_gtk_labels, self.sensor_value_gtk_toggle)
            graph_window.add(graph)
        
        #sensor_logging.graph_sensor_data(fig, canvas, sensor_value_gtk_labels, sensor_value_gtk_toggle, lock, interval=1)
        #GObject.timeout_add(100, sensor_logging.update_graph, self.graphs, self.sensor_value_gtk_labels, self.sensor_value_gtk_toggle, m_interval=1)

        networking.start_telemetry_thread(self.sensor_value_gtk_labels, self.sensor_value_gtk_slider)

        timeout_thread = Thread(target=networking.mote_timeout, args=[self.sensor_value_gtk_labels], daemon=True)
        timeout_thread.start()

        #labjack thread
        #WARNING Disable all labjack functionality until needed
        #hts_labjack.start_lj_thread(sensors, self.sensor_value_gtk_labels)
       
        # set up fireX
        self.fireX_window = Gtk.Window(
            title="fireX", default_width=600, default_height=600)
        self.fireX_window.props.deletable=False
        list_box = Gtk.ListBox()

        viewport = Gtk.Viewport()
        viewport.add(list_box)
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.add(viewport)
        self.fireX_window.add(scrolledwindow)

        def toggle_firex_valve(self, state):
            #update fireX value info here
            print(state)
            networking.send_actuator_command(3, 22, not state, interface_type='Binary GPIO')

        #you can also do this as an actuator "command", just add it to 
        def send_fireX_status(self, state):
            print(state)
            for i in range(1, 4):
                networking.send_actuator_command(i, 0, state, interface_type='FireX')

        def fireX_burst(self):
            toggle_firex_valve(self, True)
            #open fireX value now
            #close fireX value in t seconds
            timer = Timer(10, toggle_firex_valve, (self, False))
            timer.start()

        row = Gtk.ListBoxRow()
        row_box = Gtk.Box()
        
        fireX_burst_label = Gtk.Label(xalign=0, selectable=True, ypad=10, can_focus=False, expand=True,
                                label='AutoFireX Burst')
        fireX_burst_button = Gtk.Button(label='Fire')
        fireX_burst_button.connect('clicked', fireX_burst)
        row_box.add(fireX_burst_label)
        row_box.add(fireX_burst_button)
        row.add(row_box)
        list_box.add(row)

    
        row = Gtk.ListBoxRow()
        row_box = Gtk.Box()

        global fireX_status_light
        fireX_status_light = Gtk.Image().new()
        fireX_status_light.set_from_icon_name('gtk-no', 0)
        
        hotfire_label = Gtk.Label(xalign=0, selectable=True, ypad=10, can_focus=False, expand=True,
                                label='Toggle Hotfire Mode')
        hotfire_on_button = Gtk.Button(label='ON')
        hotfire_on_button.connect('clicked', send_fireX_status, True)
        hotfire_off_button = Gtk.Button(label='OFF')
        hotfire_off_button.connect('clicked', send_fireX_status, False)
        row_box.add(hotfire_label)
        row_box.add(fireX_status_light)
        row_box.add(hotfire_on_button)
        row_box.add(hotfire_off_button)
        row.add(row_box)
        list_box.add(row)

        row = Gtk.ListBoxRow()
        row_box = Gtk.Box()

        firex_toggle_label = Gtk.Label(xalign=0, selectable=True, ypad=10, can_focus=False, expand=True,
                                label='Manual FireX')
        firex_toggle_on_button = Gtk.Button(label='ON')
        firex_toggle_on_button.connect('clicked', toggle_firex_valve, True)
        firex_toggle_off_button = Gtk.Button(label='OFF')
        firex_toggle_off_button.connect('clicked', toggle_firex_valve, False)
        row_box.add(firex_toggle_label)
        row_box.add(firex_toggle_on_button)
        row_box.add(firex_toggle_off_button)
        row.add(row_box)
        list_box.add(row)

        # set up actuator window
        self.actuator_window = Gtk.Window(
            title="Actuators", default_width=600, default_height=600)
        self.actuator_window.props.deletable = False
        list_box = Gtk.ListBox()
        for actuator in actuators:
            row = Gtk.ListBoxRow()
            row_box = Gtk.Box()
            row_box.add(Gtk.Label(
                label=actuator['Human Name'], xalign=0, selectable=True, ypad=10, can_focus=False, expand=True))
            
            last_sent_label = Gtk.Label(label="Last Send Command: NONE".rjust(30, " "))
            ack_light = Gtk.Image().new()
            ack_light.set_from_icon_name('gtk-no', 1)

            enable_button = Gtk.Button(label="ON")
            enable_button.connect('clicked', self.send_bool, True, last_sent_label,
                           (actuator['Mote id'], actuator['Pin'], actuator['Interface Type']))

            disable_button = Gtk.Button(label="OFF")
            disable_button.connect('clicked', self.send_bool, False, last_sent_label,
                           (actuator['Mote id'], actuator['Pin'], actuator['Interface Type']))
            
            actuator_switches[int(actuator['Mote id'])][int(actuator['Pin'])] = (enable_button, disable_button, last_sent_label, ack_light)

            row_box.add(ack_light)
            row_box.add(enable_button)
            row_box.add(disable_button)
            row_box.add(last_sent_label)
            row.add(row_box)
            list_box.add(row)

        viewport = Gtk.Viewport()
        viewport.add(list_box)
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.add(viewport)
        self.actuator_window.add(scrolledwindow)
        
        #Actuator test script code
        self.actuator_script_window = Gtk.Window(title="Actuator Scripts", default_width=600, default_height=600)
        self.actuator_script_window.props.deletable=False
        list_box = Gtk.ListBox()

        global auto_test_csv_paths
        auto_test_csv_paths = {0:"", 1:"", 2:"", 3:"", 'ABORT':"../Autoseq/abort.csv", 'DUMP':'../Autoseq/dump.csv', 'SETPOINT':"../Autoseq/abort_redline.csv"}
        #File chooser to upload CSV for rocket commands
        global countdown_label
        countdown_label = []
        global autoseq_output_text
        autoseq_output_text = []
        self.autoseq_switches = []

        #abort sequence chooseer
        abort_file_chooser_row = Gtk.ListBoxRow()
        abort_file_chooser_row_box = Gtk.Box()

        abort_chosen_file_label = Gtk.Label(label=f"Abort Autosequence: {auto_test_csv_paths['ABORT']}")
        abort_file_chooser_button = Gtk.Button(label="ABORT FILE")
        abort_file_chooser_button.connect('clicked', self.choose_file, "ABORT", abort_chosen_file_label)

        abort_file_chooser_row_box.add(abort_file_chooser_button)
        abort_file_chooser_row_box.add(abort_chosen_file_label)
        abort_file_chooser_row.add(abort_file_chooser_row_box)
        list_box.add(abort_file_chooser_row)

        #dump sequence file chooser
        dump_file_chooser_row = Gtk.ListBoxRow()
        dump_file_chooser_row_box = Gtk.Box()

        dump_file_chooser_row = Gtk.ListBoxRow()
        dump_file_chooser_row_box = Gtk.Box()

        dump_chosen_file_label = Gtk.Label(label=f"Dump Autosequence: {auto_test_csv_paths['DUMP']}")
        dump_file_chooser_button = Gtk.Button(label="DUMP FILE")
        dump_file_chooser_button.connect('clicked', self.choose_file, "DUMP", abort_chosen_file_label)

        dump_file_chooser_row_box.add(dump_file_chooser_button)
        dump_file_chooser_row_box.add(dump_chosen_file_label)
        dump_file_chooser_row.add(dump_file_chooser_row_box)
        list_box.add(dump_file_chooser_row)

        #setpoint sequence chooser
        setpoint_file_chooser_row = Gtk.ListBoxRow()
        setpoint_file_chooser_row_box = Gtk.Box()

        setpoint_chosen_file_label = Gtk.Label(label=f"Redlines: {auto_test_csv_paths['SETPOINT']}")
        setpoint_file_chooser_button = Gtk.Button(label="REDLINE FILE")
        setpoint_file_chooser_button.connect('clicked', self.choose_setpoints, "SETPOINT", setpoint_chosen_file_label)
        
        setpoint_file_chooser_row_box.add(setpoint_file_chooser_button)
        setpoint_file_chooser_row_box.add(setpoint_toggle_button)
        setpoint_file_chooser_row_box.add(setpoint_chosen_file_label)
        
        setpoint_file_chooser_row.add(setpoint_file_chooser_row_box)
        list_box.add(setpoint_file_chooser_row)

        #blank row
        list_box.add(Gtk.Label(""))

        n = 4
        for i in range(n):
            #autosequence file
            file_chooser_row = Gtk.ListBoxRow()
            file_chooser_row_box = Gtk.Box()

            chosen_file_label = Gtk.Label(label=f"Autosequence: {auto_test_csv_paths[0]}")
            file_chooser_button = Gtk.Button(label="Choose Test CSV File")
            file_chooser_button.connect('clicked', self.choose_file, i, chosen_file_label)

            file_chooser_row_box.add(file_chooser_button)
            file_chooser_row_box.add(chosen_file_label)
            file_chooser_row.add(file_chooser_row_box)
            list_box.add(file_chooser_row)

            #button to actually run the test sequence
            test_init_row = Gtk.ListBoxRow()
            test_init_row_box = Gtk.Box()

            test_init_button = Gtk.Button(label="RUN TEST SEQUENCE")

            test_init_button.connect(
                'clicked', 
                autoseq.run_test_sequence, 
                i, 
                self.actuators,
                i)

            countdown_label.append(Gtk.Label(label="\tT+0"))
            self.autoseq_switches.append(test_init_button)
            
            test_init_row_box.add(test_init_button)
            #test_init_row_box.add(abort_button)
            test_init_row_box.add(countdown_label[i])
            test_init_row.add(test_init_row_box)
            list_box.add(test_init_row)

            abort_row = Gtk.ListBoxRow()
            abort_row_box = Gtk.Box()

            abort_button = Gtk.Button(label="ABORT")
            abort_button.connect(
                'clicked', 
                autoseq.abort_autoseq, 
                i,
                self.actuators,
                "ABORT")
            abort_row_box.add(abort_button)

            dump_button = Gtk.Button(label="DUMP")
            dump_button.connect(
                'clicked', 
                autoseq.abort_autoseq, 
                i,
                self.actuators,
                "DUMP")
            abort_row_box.add(dump_button)

            halt_button = Gtk.Button(label="HALT")
            halt_button.connect(
                'clicked', 
                autoseq.abort_autoseq,
                i,
                self.actuators,
                "HALT")
            abort_row_box.add(halt_button)


            abort_row.add(abort_row_box)
            list_box.add(abort_row)

            output_row = Gtk.ListBoxRow()
            output_row_box = Gtk.Box()
            
            autoseq_output_text.append(Gtk.TextView())
            
            output_row_box.add(autoseq_output_text[i])
            output_row.add(output_row_box)
            list_box.add(output_row)

            viewport = Gtk.Viewport()
            viewport.add(list_box)
            scrolledwindow = Gtk.ScrolledWindow()
            scrolledwindow.add(viewport)
            self.actuator_script_window.add(scrolledwindow)

            
        #disarm by default
        self.arm(False)
        # thread to update the time on the gui
        #update_time_thread = Thread(target=self.update_gui_labels, daemon=True)
        #update_time_thread.start()

        GObject.timeout_add(300, self.update_gui_labels)

        #GObject.timeout_add(100, sensor_logging.update_graph, self.graphs, self.sensor_value_gtk_labels, self.sensor_value_gtk_toggle, m_interval=1)

    #File choosing dialog. Copied from GTK docs.
    def choose_file(self, button, i, file_label=None):
        print("OPEN FILE!!")

        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=None, action=Gtk.FileChooserAction.OPEN
        )

        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            auto_test_csv_paths[i] = dialog.get_filename()
            if file_label != None:
                file_label.set_text(f"File Chosen: {os.path.basename(auto_test_csv_paths[i])}")
       
        dialog.destroy()

    def choose_setpoints(self, button, i, file_label=None):
        self.choose_file(button, i, file_label=file_label)
        configuration.setpoints = configuration.load_setpoint_csv(file_name=auto_test_csv_paths["SETPOINT"])
        print("New Setpoint File", configuration.setpoints)

    def LoadSensorsWindow(self, button):
        for w in self.sensor_windows:
            w.show_all()
        for g in self.graph_windows:
            g.show_all()

    def LoadActuatorssWindow(self, button):
        self.actuator_window.show_all()

    def LoadFireXWindow(self, button):
        self.fireX_window.show_all()
    
    def ActuatorScriptMenu(self, button):
        self.actuator_script_window.show_all()
    
    def ConnectMote(self, button):
        print("connect button pressed")
        networking.send_config_to_mote(self.sensors)
        #hts_labjack.connect_ljs(self.sensors)

    def ToggleBangBang_Fuel(self, button, state):
        print(f"Setting Bang-Bang Fuel to {state}")
        networking.send_actuator_command(3, 0, state, interface_type='Bang-Bang')

    def ToggleBangBang_Ox(self, button, state):
        print(f"Setting Bang-Bang Ox to {state}")
        networking.send_actuator_command(3, 1, state, interface_type='Bang-Bang')
    
    def send_bool(self, widget, state, label, address=None):
        if not self.is_armed:
            return
        mote_id = int(address[0])
        pin_num = int(address[1])
        actuator_type = address[2]
        #state = not widget.get_state()  # for some reason GTK switch backwards
        networking.send_actuator_command(mote_id, pin_num, state, interface_type=actuator_type)
        if state == True:
            label.set_text("Last Sent Command: ON".rjust(35," "))
        elif state == False:
            label.set_text("Last Sent Command: OFF".rjust(35," "))
        else:
            print("If you are seeing this message, STATE is neither true nor false. This is bad.")

    def toggleArm(self, button):
        if self.builder.get_object('arm_status_icon').get_icon_name().icon_name == 'changes-prevent-symbolic':
            self.builder.get_object('arm_status_icon').set_from_icon_name(
                'changes-allow-symbolic', size=30)
            self.builder.get_object('arm_button_icon').set_from_icon_name(
                'changes-allow-symbolic', size=51)
            self.builder.get_object('arm_button_label').set_text('DISARMED')
            self.arm(False)
        elif self.builder.get_object('arm_status_icon').get_icon_name().icon_name == 'changes-allow-symbolic':
            self.builder.get_object('arm_status_icon').set_from_icon_name(
                'changes-prevent-symbolic', size=30)
            self.builder.get_object('arm_button_icon').set_from_icon_name(
                'changes-prevent-symbolic', size=51)
            self.builder.get_object('arm_button_label').set_text('ARMED')
            self.arm(True)
        else:
            print('Error')

    #TRUE to ARM, FALSE to DISARM
    def arm(self, state):
        self.is_armed = state
        for mote, dct in actuator_switches.items():
            for pin, switches in dct.items():
                if (state and networking.get_mote_status(mote)) or not state or mote == 'AutoSeq':
                    for s in switches:
                        s.set_sensitive(state)
        
        for switch in self.autoseq_switches:
            switch.set_sensitive(state)

        self.builder.get_object('bangbang_fuel_switch').set_sensitive(state)
        self.builder.get_object('bangbang_ox_switch').set_sensitive(state)
    
    #status light 
    def display_bangbang(self, state, fuel_sys):
        if state:
            self.builder.get_object(f'bangbang_status_{fuel_sys}').set_from_icon_name('gtk-yes',size=0)
        else:
            self.builder.get_object(f'bangbang_status_{fuel_sys}').set_from_icon_name('gtk-no',size=0)
        pass

    def display_firex(self, state):
        #print(f"display fireX status, state = {state}")
        if state:
            self.builder.get_object(f'fireX_status').set_from_icon_name('gtk-yes',size=0)
            fireX_status_light.set_from_icon_name('gtk-yes',size=0)
        else:
            self.builder.get_object(f'fireX_status').set_from_icon_name('gtk-no',size=0)
            fireX_status_light.set_from_icon_name('gtk-no',size=0)
        pass

    def stat_light(self, state, num):
        if state:
            self.builder.get_object(f'mote{num}_status').set_from_icon_name('gtk-yes',size=0)
        else:
            self.builder.get_object(f'mote{num}_status').set_from_icon_name('gtk-no',size=0)


    def update_gui_labels(self):
        #print(time.time(), "thread!")
        now = datetime.datetime.now()
        time_str = str(now.hour) + ':' + str(now.minute) + ':' + str(now.second)
        self.builder.get_object('time_label').set_text(time_str)

        #update MoTE connection status
        for i in range(len(networking.mote_status)):
            self.stat_light(networking.mote_status[i], i+1)

        #print(networking.bangbang_status)
        self.display_bangbang(networking.bangbang_status[0], 'fuel')
        self.display_bangbang(networking.bangbang_status[1], 'ox')

        self.display_firex(networking.firex_status)

        for s in sensor_logging.sensor_log_values.keys():
            if sensor_logging.sensor_log_values[s] != "None" and s[1][-1] != 'V':
                self.sensor_value_gtk_labels[s].set_text(str(sensor_logging.sensor_log_values[s]))
                self.sensor_value_gtk_slider[s][0].set_fraction(
                    (float(sensor_logging.sensor_log_values[s]) - float(self.sensor_value_gtk_slider[s][1]))/(float(self.sensor_value_gtk_slider[s][2]) - float(self.sensor_value_gtk_slider[s][1]))
                )

        for i in range(1, 4):
            for act in actuator_switches[i].keys():
                #print(sensor_logging.actuator_acks)
                if sensor_logging.actuator_acks[(i, act)]:
                    actuator_switches[i][act][3].set_from_icon_name('gtk-yes', 1)
                else:
                    actuator_switches[i][act][3].set_from_icon_name('gtk-no', 1)
        
        #print('mote 1 ping', networking.mote_ping)
        ping_arr = networking.mote_ping
        self.builder.get_object("mote_ping_val").set_text(f"MoTE 1: {ping_arr[0]} ms\nMoTE 2: {ping_arr[1]} ms\nMoTE 3: {ping_arr[2]} ms ")

        return True