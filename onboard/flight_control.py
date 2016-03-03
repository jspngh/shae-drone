from dronekit import connect, time
from solo import Solo
import json
import socket
import os


class Location():
    def __init__(self, x_coordinate=0.0, y_coordinate=0.0):
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate

unix_socket = socket.socket(socket.AF_UNIX,  # Unix Domain Socket
                            socket.SOCK_STREAM)  # TCP
try:
    os.remove("/tmp/flight_control")  # remove socket if it exists
except OSError:
    pass
unix_socket.bind("/tmp/flight_control")
unix_socket.listen(1)

log = open('/home/root/shae/logs/log', 'w')

vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)

s = Solo(vehicle=vehicle)

while True:
    client, address = unix_socket.accept()
    raw = client.recv(1024)
    data = json.loads(raw)
    msg_class = data['class']
    if (msg_class == "Location"):
        x_coordinate = float(data['x_coordinate'])
        y_coordinate = float(data['y_coordinate'])
        loc = Location(x_coordinate, y_coordinate)
        s.arm()
        s.takeoff()
        time.sleep(1)
        s.land()
        # log.write(str(loc.x_coordinate))
