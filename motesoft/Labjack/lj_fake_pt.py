from labjack import ljm

PIN = "DAC0"
USE_1K = True

def volts_to_psi_1k(val):
    #P51-1000-S-B-136-4.5V
    #0-1000 psi, 0.5-4.5v
    return 250 * val - 125

def psi_to_volts_1k(val):
    return (val + 125)/250

def volts_to_psi_5k(val):
    #MLH05KPSL06A
    #0-5000 psi, 0.5-4.5v
    return 1250 * 2 * val - 625

def psi_to_volts_5k(val):
    return (val + 625)/(1250)

handle = ljm.openS("T4", "ANY", "ANY")  # T4 device, Any connection, Any identifier

info = ljm.getHandleInfo(handle)
print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

#initialize to 0
ljm.eWriteName(handle, PIN, 0)
print("\nSet %s state : %f" % (PIN, 0))

#main loop
if __name__ == "__main__":
    while True:
        print("Pressure PSI: ", end='')

        pressure = float(input())
        volts = 0
        if USE_1K:
            volts = psi_to_volts_1k(pressure)
        else:
            volts = psi_to_volts_5k(pressure)

        ljm.eWriteName(handle, PIN, volts)
        print("\nSet %s state : %f" % (PIN, volts))

