import os
import json
import socket
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
unix_socket = socket.socket(socket.AF_UNIX,      # Unix Domain Socket
                            socket.SOCK_STREAM)  # TCP
try:
    os.remove("/tmp/uds_control")  # remove socket if it exists
except OSError:
    pass
unix_socket.bind("/tmp/uds_control")
unix_socket.listen(1)

while not quit:
    client, address = unix_socket.accept()
    raw = client.recv(1024)  # TODO: request the length first, to be able to send messages of arbitrary length
    try:
        packet = json.loads(raw)  # parse the Json we received
        if 'MessageType' not in packet:  # every packet should have a MessageType field
            raise ValueError
        if 'Message' not in packet:  # every packet should have a Message field
            raise ValueError

        message_type = packet['MessageType']  # the 'message type' attribute tells us to which class of packet this packet belongs
        message = packet['Message']           # the 'message' attribute tells what packet it is, within it's class
        if (message_type == "navigation"):
        elif (message_type == "status"):
        elif (message_type == "settings"):
        else:
            raise ValueError
    except ValueError:
        print "handle error"
