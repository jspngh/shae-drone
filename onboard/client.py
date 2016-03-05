import socket
import json
from control_classes import Location, WayPoint, WayPointEncoder


# HOST = "10.1.1.10"
HOST = "localhost"
PORT = 6330
waypoints = []
for i in range(0, 4):
    tmp_loc = Location(i, i)
    waypoints.append(WayPoint(location=tmp_loc, order=i))
path_message = {'MessageType': 'control', 'Message': 'path', 'Path': waypoints}
json_message = json.dumps(path_message, cls=WayPointEncoder)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_STREAM)  # TCP

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.send(json_message)
    data = sock.recv(1024)
    print data

finally:
    sock.close()
