import os
import sys
import json
import socket
import struct
import threading
import logging
from logging import Logger
from threading import RLock
from dronekit import connect, time

from solo import Solo
from global_classes import Location, WayPoint, WayPointEncoder, logformat, dateformat


class SettingsHandler():
    """
    This class will take care of packets of the 'settings' message type
    """
    def __init__(self, packet, message, solo, logging_level):
        """
        :type solo: Solo
        """
        self.packet = packet
        self.message = message
        self.solo = solo

        # set up logging
        self.settings_logger = logging.getLogger("Status Handler")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        handler = logging.StreamHandler(stream=sys.stdout)  # TODO
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.settings_logger.addHandler(handler)
        self.settings_logger.setLevel(logging_level)

    def handle_packet(self):
        try:
            if (self.message == "workstation_config"):  # set the workstation configuration and start sending heartbeats
                self.settings_logger.info("Extracting configuration")
                config = self.packet['configuration']
                ip = config['ip_address']
                port = config['port']  # keep the port as string for now
                self.settings_logger.info("IP: {0}".format(ip))
                self.settings_logger.info("Port: {0}".format(port))
                return (ip, port)
            else:                                       # this is an array with the attributes that were required
                if not isinstance(self.message, list):  # if it is not a list, something went wrong
                    self.settings_logger.warning("Message not a list")
                    raise ValueError
                for setting_request in self.message:
                    if (setting_request['key'] == "speed"):
                        value = setting_request['value']
                        self.solo.set_target_speed(value)
                        print "handle"
                    elif (setting_request['key'] == "height"):
                        value = setting_request['value']
                        self.solo.set_target_height(value)
                    elif (setting_request['key'] == "camera_angle"):
                        value = setting_request['value']
                        self.solo.set_camera_angle(value)
                    elif (setting_request['key'] == "fps"):
                        value = setting_request['value']
                        self.solo.set_camera_fps(value)
                    elif (setting_request['key'] == "resolution"):
                        value = setting_request['value']
                        self.solo.set_camera_resolution(value)
                    else:
                        raise ValueError  # if we get to this point, something went wrong

        except ValueError:
            print "handle error"
