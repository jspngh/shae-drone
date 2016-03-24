import os
import json
import struct
import socket
import logging
import sys
from threading import RLock
from dronekit import connect, time
from solo import Solo
from global_classes import SIM, logging_level, MessageCodes, WayPointQueue
from navigation_handler import NavigationHandler
from settings_handler import SettingsHandler
from status_handler import StatusHandler
import sys
sys.path.append('../')
from simulator.vehicle_simulator import VehicleSimulator

# set up logging
control_logger = logging.getLogger("Control Module")
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
handler.setLevel(logging_level)
control_logger.addHandler(handler)
control_logger.setLevel(logging_level)

if SIM:
    vehicle_simulator = VehicleSimulator()
    vehicle = vehicle_simulator.get_vehicle()
    s = Solo(vehicle=vehicle)
else:
    vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)
    s = Solo(vehicle=vehicle)

quit = False
waypoint_queue = WayPointQueue()  # in this queue, the waypoints the drone has to visit will come
unix_socket = socket.socket(socket.AF_UNIX,      # Unix Domain Socket
                            socket.SOCK_STREAM)  # TCP
try:
    os.remove("/tmp/uds_control")  # remove socket if it exists
except OSError:
    pass
unix_socket.bind("/tmp/uds_control")
unix_socket.listen(2)

nav_thread = NavigationHandler.NavigationThread(1, solo=s, waypoint_queue=waypoint_queue)
control_logger.debug("Starting Navigation Thread")
nav_thread.start()

while not quit:
    client, address = unix_socket.accept()
    try:
        length = client.recv(4)
        if length is None:
            control_logger.info("Length is None")
            raise ValueError
        buffersize = struct.unpack(">I", length)[0]
        raw = client.recv(buffersize)
        packet = json.loads(raw)  # parse the Json we received
        if 'MessageType' not in packet:  # every packet should have a MessageType field
            control_logger.info("every packet should have a MessageType field")
            raise ValueError
        if 'Message' not in packet:  # every packet should have a Message field
            control_logger.info("every packet should have a Message field")
            raise ValueError

        message_type = packet['MessageType']  # the 'message type' attribute tells us to which class of packet this packet belongs
        message = packet['Message']           # the 'message' attribute tells what packet it is, within it's class
        if (message_type == "navigation"):
            control_logger.info("received a navigation request")
            nav_handler = NavigationHandler(packet, message, s, waypoint_queue)
            nav_handler.handle_packet()
            client.send(struct.pack(">I", MessageCodes.ACK))
        elif (message_type == "status"):
            control_logger.info("received a status request")
            stat_handler = StatusHandler(packet, message, s, waypoint_queue)
            response = stat_handler.handle_packet()
            if response is None:
                client.send(struct.pack(">I", MessageCodes.ERR))  # something went wrong
            else:
                client.send(struct.pack(">I", MessageCodes.STATUS_RESPONSE))
                client.send(struct.pack(">I", len(response)))
                client.send(response)
        elif (message_type == "settings"):
            control_logger.info("received a settings request")
            sett_handler = SettingsHandler(packet, message, s)
            response = sett_handler.handle_packet()
            # if we got a response, that means we need to start sending heartbeats
            if response is not None and isinstance(response, tuple):
                control_logger.info("Settings configuration")
                client.send(struct.pack(">I", MessageCodes.START_HEARTBEAT))
                client.send(struct.pack(">I", len(response[0])))
                client.send(response[0])
                client.send(struct.pack(">I", len(response[1])))
                client.send(response[1])
            else:
                control_logger.info("Returning ack")
                client.send(struct.pack(">I", MessageCodes.ACK))
        else:
            raise ValueError

    except ValueError:
        # TODO: handle error
        control_logger.info("We might have a little problem")
        client.send(struct.pack(">I", MessageCodes.ERR))
