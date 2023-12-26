import subprocess
from datetime import datetime

now = datetime.now()
#Commands to be entered on the raspberry pi to start the flowmeter from operations console
# https://phab.burpg.space/w/6._software/labjack_and_raspberrypi/?v=5

date = now.strftime("%Y-%m-%d %H:%M:%S")
cmd_set = [f'sudo date -s "{date}"',f'python3 flowmeter_stream_and_write.py > output{now}','exit']
ssh_cmd = ['ssh', 'pi@flowmeter.local']

try:            
    ssh_session = subprocess.Popen(ssh_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    #Writing command by command
    for cmd in cmd_set:
        ssh_session.stdin.write(cmd.encode())
        ssh_session.stdin.write(b'\n')
    ssh_session.stdin.close()
	
    for line in ssh_session.stdout:
    	l = line.decode().rstrip()
    	print(l)

    for line in ssh_session.stderr:
    	err = line.decode().rstrip()
    	print(err)


    ssh_session.wait()

except subprocess.TimeoutExpired:
                print("SSH connection timed out.")
