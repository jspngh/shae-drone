import json
import socket
import struct
import os
from dronekit import connect, time
from solo import Solo
from global_classes import SIM
from navigation_classes import PathHandler, StartHandler, StopHandler, EmergencyHandler

if SIM:
    vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)
    s = Solo(vehicle=vehicle)
else:
    vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)
    s = Solo(vehicle=vehicle)

quit = False
waypoint_queue = []
unix_socket = socket.socket(socket.AF_UNIX,      # Unix Domain Socket
                            socket.SOCK_STREAM)  # TCP
try:
    os.remove("/tmp/uds_navigation")  # remove socket if it exists
except OSError:
    pass
unix_socket.bind("/tmp/uds_navigation")
unix_socket.listen(1)

while not quit:
    client, address = unix_socket.accept()
    raw = client.recv(1024)  # this might need to change in the future
    data = json.loads(raw)
    try:
        packet = json.loads(raw)  # parse the Json
        if 'Message' not in packet:  # every packet should have a Message field
            raise ValueError

        message = packet['Message']  # the message attribute tells us how to process the packet
        if (message == "path"):
            handler = PathHandler(packet, waypoint_queue=waypoint_queue)
            handler.handle_packet()
            response = struct.pack(">I", 200)
            client.send(response)
            client.close()
            quit = True  # is here for testing
        elif (message == "start"):
            handler = StartHandler(packet, s)
        elif (message == "stop"):
            handler = StopHandler(packet, s)
        elif (message == "emergency"):
            handler = EmergencyHandler(packet, s)
        else:
            raise ValueError  # if we get to this point, something went wrong

    except ValueError:
        print "handle error"

vehicle.close()
