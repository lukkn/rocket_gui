import os
import time
from datetime import datetime
from labjack import ljm

# Open first found LabJack
handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")

info = ljm.getHandleInfo(handle)
print("Opened a LabJack with Device type: %i, Connection type: %i,\n" \
"Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" % \
(info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

# Setup and call eReadName to read from a AIN on the LabJack.
name = "AIN0"

#Create file and location of file
#Make sure to specify the preferred name and path of this file
file = open('/home/data_log.csv', 'a')

# Check if the file is empty and write the header if it is
if os.stat('/home/data_log.csv').st_size == 0:
    file.write("Time, Sensor Name, Sensor Reading \n")

while True:
    result = ljm.eReadName(handle, name)
    now = datetime.now()
    file.write(str(now) + "," + str(name) + "," + str(result) + "\n")
    file.flush()
    time.sleep(5)

# Close handle and file
file.close()
ljm.close(handle)
