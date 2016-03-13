import socket
import json
import struct
import time
from global_classes import Location, WayPoint, WayPointEncoder


HOST = "localhost"
PORT = 6330

waypoints = []
# for i in range(0, 4):
tmp_loc_1 = Location(latitude=50.991725, longitude=3.746529)
tmp_loc_2 = Location(latitude=50.992111, longitude=3.748447)
tmp_loc_3 = Location(latitude=50.990707, longitude=3.751409)
waypoints.append(WayPoint(location=tmp_loc_1, order=1))
waypoints.append(WayPoint(location=tmp_loc_2, order=2))
waypoints.append(WayPoint(location=tmp_loc_3, order=3))
path_message = {'MessageType': 'navigation', 'Message': 'path', 'Path': waypoints}
json_path_message = json.dumps(path_message, cls=WayPointEncoder)
start_message = {'MessageType': 'navigation', 'Message': 'start'}
json_start_message = json.dumps(start_message)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_STREAM)  # TCP

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.send(json_start_message)
    time.sleep(2)
    print "message sent"
    data = sock.recv(1024)
    print struct.unpack(">I", data)[0]

    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_STREAM)  # TCP
    sock.connect((HOST, PORT))
    sock.send(json_path_message)
    print "message sent"
    data = sock.recv(1024)
    print struct.unpack(">I", data)[0]

finally:
    sock.close()
