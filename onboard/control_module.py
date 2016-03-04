import json
import socket
import os
from control_classes import Location, WayPoint, PathHandler, StartHandler, StopHandler, EmergencyHandler
from dronekit import connect, time
from solo import Solo

vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)
s = Solo(vehicle=vehicle)
waypoint_queue = []
unix_socket = socket.socket(socket.AF_UNIX,  # Unix Domain Socket
                            socket.SOCK_STREAM)  # TCP
try:
    os.remove("/tmp/uds_control")  # remove socket if it exists
except OSError:
    pass
unix_socket.bind("/tmp/uds_control")
unix_socket.listen(1)

while True:
    client, address = unix_socket.accept()
    raw = client.recv(1024)  # this might need to change in the future
    data = json.loads(raw)
    try:
        packet = json.loads(raw)  # parse the Json
        if 'Message' not in packet:  # every packet should have a Message field
            raise ValueError

        message = packet['Message']  # the message attribute tells us how to process the packet
        if (message == "path"):
            handler = PathHandler(packet)
        elif (message == "start"):
            handler = StartHandler(packet)
        elif (message == "stop"):
            handler = StopHandler(packet)
        elif (message == "emergency"):
            handler = EmergencyHandler(packet)
        else:
            raise ValueError  # if we get to this point, something went wrong

        handler.handle_packet()

    except ValueError:
        print "handle error"
