from dronekit import connect, time
from solo import Solo
import json
import socket
import os

vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)
s = Solo(vehicle=vehicle)
unix_socket = socket.socket(socket.AF_UNIX,  # Unix Domain Socket
                            socket.SOCK_STREAM)  # TCP
try:
    os.remove("/tmp/uds_status")  # remove socket if it exists
except OSError:
    pass
unix_socket.bind("/tmp/uds_status")
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
        if (message == "heartbeat"):  # the status message is a heartbeat message
            # location = s.get_location
            print "handle"
        else:                         # this is an array with the attributes that were required
            if not isinstance(message, list):  # if it is not a list, something went wrong
                raise ValueError
            for status_request in message:
                if (status_request['Key'] == "battery_level"):
                    print "handle"
                elif (status_request['Key'] == "current_location"):
                    print "handle"
                elif (status_request['Key'] == "drone_type"):
                    print "handle"
                elif (status_request['Key'] == "waypoint_reached"):
                    print "handle"
                else:
                    raise ValueError

    except ValueError:
        print "handle error"
