import sys
import logging

from solo import Solo
from global_classes import logformat, dateformat


## @ingroup Onboard
# @brief This class will take care of packets of the 'settings' message type
class SettingsHandler():
    def __init__(self, solo, logging_level, log_type='console', filename=''):
        """
        Initiate the handler

        Args:
            solo: Solo instance
            logging_level: the level that should be used for logging, e.g. DEBUG
            log_type: log to stdout ('console') or to a file ('file')
            filename: the name of the file if log_type is 'file'
        """
        ## The entire request from the workstation
        self.packet = None
        ## Message component from the request
        self.message = None
        ## Solo instance
        self.solo = solo

        # set up logging
        ## logger instance
        self.settings_logger = logging.getLogger("Status Handler")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        if log_type == 'console':
            handler = logging.StreamHandler(stream=sys.stdout)
        elif log_type == 'file':
            handler = logging.FileHandler(filename=filename)
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.settings_logger.addHandler(handler)
        self.settings_logger.setLevel(logging_level)

    def handle_packet(self, packet, message):
        self.packet = packet
        self.message = message
        if (self.message == "workstation_config"):  # set the workstation configuration and start sending heartbeats
            self.settings_logger.info("the drone will be configured to send heartbeats to the workstation")
            config = self.packet['configuration']
            ip = config['ip_address']
            port = config['port']  # keep the port as string for now
            self.settings_logger.debug("parsed IP: {0}".format(ip))
            self.settings_logger.debug("parsed port: {0}".format(port))
            return (ip, port)
        else:                                       # this is an array with the attributes that were required
            if not isinstance(self.message, list):  # if it is not a list, something went wrong
                self.settings_logger.error("the message should be a list")
                raise ValueError("FormatError: list expected")
            for setting_request in self.message:
                if (setting_request['key'] == "speed"):
                    value = setting_request['value']
                    self.solo.set_target_speed(value)
                elif (setting_request['key'] == "height"):
                    value = setting_request['value']
                    self.solo.set_target_height(value)
                elif (setting_request['key'] == "distance_threshold"):
                    value = setting_request['value']
                    self.solo.set_distance_threshold(value)
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
