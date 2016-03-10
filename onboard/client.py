import socket
import json
import struct
from global_classes import Location, WayPoint, WayPointEncoder


HOST = "10.1.1.10"
PORT = 6330

waypoints = []
# for i in range(0, 4):
tmp_loc = Location(latitude=51.022622, longitude=3.709873)
waypoints.append(WayPoint(location=tmp_loc, order=3))
path_message = {'MessageType': 'control', 'Message': 'path', 'Path': waypoints}
json_message = json.dumps(path_message, cls=WayPointEncoder)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_STREAM)  # TCP

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.send(json_message)
    print "message sent"
    data = sock.recv(1024)
    print struct.unpack(">I", data)[0]

finally:
    sock.close()
