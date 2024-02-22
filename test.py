import subprocess

def ping_host(ip_address):
    try:
        # Ping the IP address with specified timeout
        subprocess.run(["ping", "-w", str(10), ip_address], check=True)
        print(f"{ip_address} is reachable.")
    except subprocess.CalledProcessError:
        print(f"{ip_address} is unreachable.")

ping_host("192.168.1.103")


print(subprocess.run(["ping", "-w", str(10), "192.168.1.103"]))