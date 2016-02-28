import socket
import json
from json import JSONEncoder


class Location():
    def __init__(self, x_coordinate=0.0, y_coordinate=0.0):
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate


class LocationEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Location):
            res = {'class': 'Location'}
            res.update(o.__dict__)
            return res

IP = "10.1.1.10"
PORT = 6330
MESSAGE = Location(51.4, 3.1)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_STREAM)  # TCP

json_message = json.dumps(MESSAGE, cls=LocationEncoder)
print json_message

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(json_message)

finally:
    sock.close()
