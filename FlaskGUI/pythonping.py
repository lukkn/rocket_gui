import sys
import string
sys.path.append('./python_flask_and_flaskio_and_eventlet_libraries')
from pythonping import ping


MoteIP, Time = str(ping('192.168.1.101', count=1, timeout=0.1)).split(',')

print (MoteIP, Time)