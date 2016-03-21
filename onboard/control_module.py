import os
import json
import struct
import socket
import logging
import sys
from threading import RLock
from dronekit import connect, time
from solo import Solo
from global_classes import SIM, logging_level
from navigation_handler import NavigationHandler
from settings_handler import SettingsHandler
from status_handler import StatusHandler

# set up logging
control_logger = logging.getLogger("Control Module")
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
handler.setLevel(logging_level)
control_logger.addHandler(handler)
control_logger.setLevel(logging_level)

if SIM:
    vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)
    s = Solo(vehicle=vehicle)
else:
    vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)
    s = Solo(vehicle=vehicle)

quit = False
waypoint_queue = []  # in this queue, the waypoints the drone has to visit will come
lock = RLock()  # this lock will be used when accessing the waypoint_queue
unix_socket = socket.socket(socket.AF_UNIX,      # Unix Domain Socket
                            socket.SOCK_STREAM)  # TCP
try:
    os.remove("/tmp/uds_control")  # remove socket if it exists
except OSError:
    pass
unix_socket.bind("/tmp/uds_control")
unix_socket.listen(1)

nav_thread = NavigationHandler.NavigationThread(1, solo=s, waypoint_queue=waypoint_queue, lock=lock, quit=quit)
nav_thread.start()

control_logger.debug("asking for resolution")
resp = s.get_camera_resolution()
print "camera resolution: {0}".format(resp)
control_logger.debug("after asking for resolution")

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
            control_logger.info("received a navigation request")
            nav_handler = NavigationHandler(packet, message, s, waypoint_queue, lock)
            nav_handler.handle_packet()
            client.send(struct.pack(">I", 200))
        elif (message_type == "status"):
            control_logger.info("received a status request")
            stat_handler = StatusHandler(packet, message, s)
            response = stat_handler.handle_packet()
            if response is None:
                client.send(struct.pack(">I", 500))  # something went wrong
            else:
                client.send(struct.pack(">I", 300))
                client.send(struct.pack(">I", len(response)))
                client.send(response)
        elif (message_type == "settings"):
            control_logger.info("received a settings request")
            sett_handler = SettingsHandler(packet, message, s)
            sett_handler.handle_packet()
            client.send(struct.pack(">I", 200))
        else:
            raise ValueError

    except ValueError:
        # TODO: handle error
        client.send(struct.pack(">I", 500))
