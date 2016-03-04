import socket
import json
from json import JSONEncoder
from control_module import WayPoint, Location


class LocationEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Location):
            res = {'class': 'Location'}
            res.update(o.__dict__)
            return res

HOST = "10.1.1.10"
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
