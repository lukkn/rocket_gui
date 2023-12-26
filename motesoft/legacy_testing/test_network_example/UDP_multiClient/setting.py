import socket
import threading
import time
import logging
import random

SERVER_IPS = ['127.0.0.1']
SERVER_PORT = [20001]

CLIENT_PORT = [20002, 20003, 20004]
CLIENT_IPS = ['127.0.0.2', '127.0.0.3', '127.0.0.4']

#ip addrses are divided into 4 octets to unique identify devices in a network
#subnet mask indicate which octet are reserved for network and rest are for hosts
#there are 3 classes for different sizes: A, B, C
# A = subnet:255.0.0.0, 16 M hosts 256 networks (government)
# B = subnet:255.255.0.0, 65K hosts 65K networks (organiztion)
# C = subnet:255.255.255.0, 256 hosts 16M networks (home)
# public addresses are unique and public and can be used over internet
# private addresse are not uqniue and reusable (cannot be used over internet)
# public ip is found in google 
# ifoonfig provides private ()

#lo0 is loopback interface
#en0 is ethernet ow became wifi
#fw0 is firewire network interface
#stf0 is ipv6 to ipv3 tunnel interface
#gif0 is generic tunneling interface
#awdl0 is apple wireless direct link

#ip address, keep ip address static even when removed from network
#set up ip address:https://www.arduino.cc/en/Reference/EthernetIPAddress