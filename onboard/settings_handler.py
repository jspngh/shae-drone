import os
import json
import socket
import struct
import threading
from threading import RLock
from dronekit import connect, time
from solo import Solo, Location, WayPoint, WayPointEncoder


class SettingsHandler():
    """
    This class will take care of packets of the 'settings' message type
    """
    def __init__(self, packet, message, solo):
        """
        :type solo: Solo
        """
        self.packet = packet
        self.message = message
        self.solo = solo

    def handle_packet(self):
        try:
            if not isinstance(self.message, list):  # if it is not a list, something went wrong
                raise ValueError
            for setting_request in self.message:
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
                    raise ValueError  # if we get to this point, something went wrong

        except ValueError:
            print "handle error"
