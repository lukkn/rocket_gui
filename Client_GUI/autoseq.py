import imp
import gui_class
import networking
import configuration

import threading
from threading import Thread, Timer, Lock

import time
from gi.repository import GLib

#autoseq_threads is a LIST of TUPLES
#each TUPLE contains two lists, one of MoTE numbers it affects, the other is a list of timers
#e.g. [([1,2], [<Thread#1>, <Thread#2>]), ([2], [<Thread#42>, <Thread#99>]), ...]
global autoseq_threads
autoseq_threads = [None, None, None, None]

abort_mutex = Lock()
kill_countdown = False

def run_test_sequence(button, idx, actuators, path_key, is_abort=False):
    global autoseq_threads

    if autoseq_threads[idx] != None:
        print("cannot run autoseq that is already running")
        return

    #buffer = gui_class.autoseq_output_text[idx].get_buffer()
    #GLib.idle_add(buffer.delete, buffer.get_iter_at_line(0), buffer.get_iter_at_line(buffer.get_line_count()))

    commands = configuration.load_auto_test(gui_class.auto_test_csv_paths[path_key])
    act_cmds = []

    thread_list = []
    mote_list = []

    for cmd in commands:
        if cmd['P and ID'] == "NULL" or "STATE_" in cmd['P and ID']:
            act_cmds.append(cmd)
            continue
        #find the entry in the list of actuators with the matching P&ID
        act = list(filter(lambda a : a['P and ID'] == cmd['P and ID'], actuators))[0]
        print(act)
        #merge act and cmd into one dictionary. Equivalent of a set union, act U cmd
        act_cmds.append({**act, **cmd})

    times = [int(d['Time(ms)']) for d in act_cmds]
    min_time = min(times)
    max_time = max(times)

    if min_time < 0:
        offset = abs(min_time)
    else:
        offset = 0

    def countdown_thread_func():
        current_count = -offset
        global kill_countdown

        while True:
            #print("TICK")
            if current_count >= 0:
                GLib.idle_add(gui_class.countdown_label[idx].set_text, f'\tT+{int(current_count/1000)}', priority=GLib.PRIORITY_HIGH_IDLE)
                print(f'T+{int(current_count/1000)}')
            else:
                GLib.idle_add(gui_class.countdown_label[idx].set_text, f'\tT{int(current_count/1000)}', priority=GLib.PRIORITY_HIGH_IDLE)
                print(f'T{int(current_count/1000)}')

            if current_count > max_time or autoseq_threads[idx] == None or (kill_countdown and is_abort==False):
                if kill_countdown:
                    print("Countdown force killed")
                    GLib.idle_add(gui_class.countdown_label[idx].set_text, '\tABORTED')
                    kill_countdown = False
                else:
                    GLib.idle_add(gui_class.countdown_label[idx].set_text, '\tDONE')
                    autoseq_threads[idx] = None

                time.sleep(1)

                if button is not None:
                    GLib.idle_add(button.set_sensitive, True)
                if is_abort:
                    abort_mutex.release()
                    print("Release Abort Mutex")
                break
            
            current_count += 1000
            time.sleep(1)

    global countdown_thread
    countdown_thread = Thread(target=countdown_thread_func, daemon=True)
    thread_list.append(countdown_thread)

    def send_cmd(mote_id, pin, state, interface, comments, pandid):
            if pandid == "NULL":
                buffer = gui_class.autoseq_output_text[idx].get_buffer()
                newtext = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True) + f"\n{comments}. (Setting {pandid} on NONE to NONE)."
                GLib.idle_add(buffer.set_text, newtext, priority=GLib.PRIORITY_HIGH_IDLE)
                return

            networking.send_actuator_command(mote_id, pin, state,interface_type=interface)
            if state:
                GLib.idle_add(gui_class.actuator_switches[mote_id][pin][2].set_text, "Last Sent Command: ON".rjust(35," "))
            else:
                GLib.idle_add(gui_class.actuator_switches[mote_id][pin][2].set_text, "Last Sent Command: OFF".rjust(35," "))
            
            buffer = gui_class.autoseq_output_text[idx].get_buffer()
            newtext = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True) + f"\n{comments}. (Setting {pandid} on {pin} to {state})."
            GLib.idle_add(buffer.set_text, newtext, priority=GLib.PRIORITY_HIGH_IDLE)

    DEFAULT_STATE = "STATE_IDLE"
    def set_autoseq_state(state, comments):
        autoseq_threads[idx] = (mote_list, thread_list, state)

        buffer = gui_class.autoseq_output_text[idx].get_buffer()
        newtext = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True) + f"\nEntering state = {state}; {comments}"
        GLib.idle_add(buffer.set_text, newtext, priority=GLib.PRIORITY_HIGH_IDLE)

        print(f"Setting state {state}")

    for dct in act_cmds:
        if dct['P and ID'] == "NULL":
            temp_timer = Timer((int(dct['Time(ms)']) + offset)/1000,send_cmd, (
                None,
                None,
                None,
                None,
                dct['Comments'],
                dct['P and ID']
            ))
        
        elif "STATE_" in dct['P and ID']:
            temp_timer = Timer((int(dct['Time(ms)']) + offset)/1000,set_autoseq_state, (
                dct['P and ID'],
                dct['Comments']
            ))
        else:
            temp_timer = Timer((int(dct['Time(ms)']) + offset)/1000,send_cmd, (
                int(dct['Mote id']),
                int(dct['Pin']),
                eval(dct['State']),
                dct["Interface Type"],
                dct['Comments'],
                dct['P and ID']
            ))
        thread_list.append(temp_timer)
        thread_list[-1].start()
        if dct['P and ID'] != "NULL" and "STATE_" not in dct['P and ID'] and int(dct['Mote id']) not in mote_list:
            mote_list.append(int(dct['Mote id']))
        
    try:
        current_state = autoseq_threads[idx][2]
    except:
        current_state = DEFAULT_STATE
    
    autoseq_threads[idx] = (mote_list, thread_list, current_state)

    if button is not None:
        GLib.idle_add(button.set_sensitive, False)
    countdown_thread.start()

#temp
def pause_autoseq(idx):
    pass

def abort_autoseq(button, idx, actuators, abort_type="NONE"):
    global kill_countdown

    if abort_type == "ABORT":
        print("running abort sequnce!")
    elif abort_type == "DUMP":
        print("running dump sequnce!")

    if abort_mutex.locked():
        print("Unable to abort, abort sequence already in progress")
        return
    abort_mutex.acquire()
    
    print("ABORT!")
    if autoseq_threads[idx] is None:
        print("Unable to abort, no sequence running")
        abort_mutex.release()
        return

    for t in autoseq_threads[idx][1][1:]:
        t.cancel()
    kill_countdown = True
    autoseq_threads[idx] = None

    buffer = gui_class.autoseq_output_text[idx].get_buffer()
    newtext = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True) + "\nABORT"
    GLib.idle_add(buffer.set_text, newtext, priority=GLib.PRIORITY_HIGH_IDLE)

    if abort_type == "ABORT":
        run_test_sequence(button, idx, actuators, "ABORT", is_abort=True)
    elif abort_type == "DUMP":
        run_test_sequence(button, idx, actuators, "DUMP", is_abort=True)
    else:
        abort_mutex.release()

    #autoseq_threads[idx][1][0].join()
    
    
