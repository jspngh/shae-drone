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
    os.remove("/tmp/uds_settings")  # remove socket if it exists
except OSError:
    pass
unix_socket.bind("/tmp/uds_settings")
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
        if not isinstance(message, list):  # if it is not a list, something went wrong
            raise ValueError

        for setting_request in message:
            if (setting_request['Key'] == "speed"):
                value = setting_request['Value']
                print "handle"
            elif (setting_request['Key'] == "height"):
                value = setting_request['Value']
                print "handle"
            elif (setting_request['Key'] == "camera_angle"):
                value = setting_request['Value']
                print "handle"
            elif (setting_request['Key'] == "fps"):
                value = setting_request['Value']
                print "handle"
            elif (setting_request['Key'] == "resolution"):
                value = setting_request['Value']
                print "handle"
            else:
                raise ValueError

    except ValueError:
        print "handle error"
