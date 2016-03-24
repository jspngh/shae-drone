import socket
import json
import struct
import time
import sys
sys.path.append('../onboard/')
from global_classes import Location, WayPoint, WayPointEncoder

HOST = "10.1.1.10"
PORT = 6330

waypoints = []
# for i in range(0, 4):
tmp_loc_1 = Location(latitude=51.022721, longitude=3.709819)
tmp_loc_2 = Location(latitude=51.022480, longitude=3.709903)
tmp_loc_3 = Location(latitude=51.022788, longitude=3.710054)
waypoints.append(WayPoint(location=tmp_loc_1, order=1))
waypoints.append(WayPoint(location=tmp_loc_2, order=2))
waypoints.append(WayPoint(location=tmp_loc_3, order=3))
path_message = {'MessageType': 'navigation', 'Message': 'path', 'Path': waypoints}
json_path_message = json.dumps(path_message, cls=WayPointEncoder)

start_message = {'MessageType': 'navigation', 'Message': 'start'}
json_start_message = json.dumps(start_message)

config_message = {'MessageType': 'settings', 'Message': 'workstation_config', 'Configuration': {'IpAddress': '127.0.0.1', 'Port': '5555'}}
json_config_message = json.dumps(config_message)

emergency_message = {'MessageType': 'navigation', 'Message': 'emergency'}
json_em_message = json.dumps(emergency_message)

dronetype_message = {'MessageType': 'status', 'Message': [{'Key': 'drone_type'}]}
json_dt_message = json.dumps(dronetype_message)


sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_STREAM)  # TCP
# Connect to server and send data
sock.connect((HOST, PORT))
sock.send(json_start_message)
print "message sent"
data = sock.recv(4)
ack = struct.unpack(">I", data)[0]
print ack
time.sleep(4)

# sock = socket.socket(socket.AF_INET,  # Internet
#                      socket.SOCK_STREAM)  # TCP
# # Connect to server and send data
# sock.connect((HOST, PORT))
# sock.send(json_config_message)
# print "message sent"
# data = sock.recv(4)
# ack = struct.unpack(">I", data)[0]
# print ack
# time.sleep(4)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_STREAM)  # TCP
sock.connect((HOST, PORT))
sock.send(json_path_message)
print "message sent"
data = sock.recv(4)
ack = struct.unpack(">I", data)[0]
print ack
sock.close()
time.sleep(120)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_STREAM)  # TCP
sock.connect((HOST, PORT))
sock.send(json_em_message)
data = sock.recv(4)
ack = struct.unpack(">I", data)[0]
print ack
sock.close()
