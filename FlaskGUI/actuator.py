actuator_acks = {}
actuator_states = {}

def log_actuator_ack(p_and_id, binary_state):
    global actuator_acks
    actuator_acks[p_and_id] = True

    state = "On" if binary_state == 1 else "Off" if binary_state == 0 else None
    actuator_states[p_and_id] = state

def initialize_actuator_states(actuator_list):
    global actuator_states
    global actuator_acks

    for actuator in actuator_list:
        actuator_states[actuator['P and ID']] = 'Off'
        actuator_acks[actuator['P and ID']] = False

def get_actuator_states():
    return actuator_states

def get_actuator_acks():
    return actuator_acks