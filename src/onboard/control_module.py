import os
import sys
import json
import signal
import struct
import socket
import getopt
import logging
import dronekit
from dronekit_solo import SoloVehicle

from solo import Solo
from navigation_handler import NavigationHandler, NavigationThread
from settings_handler import SettingsHandler
from status_handler import StatusHandler
from global_classes import MessageCodes, WayPointQueue, logformat, dateformat, print_help


## @ingroup Onboard
# @brief The ControlModule class.
#
# The control module is responsible for handling requests from the workstation
# It interacts with the drone via dronekit
# There are 3 types of requests that should be handled:
# Navigation messages will be handled by a NavigationHandler
# Status messages will be handled by a StatusHandler
# Settings messages will be handled by a SettingsHandler
class ControlModule():
    def __init__(self, logger, log_level, SIM, log_type='console', filename=''):
        """
        Initiate the control module

        Args:
            logger: logging.Logger instance
            log_level: the level that should be used for logging, e.g. DEBUG
            SIM: boolean, is this is a simulation or not
            log_type: log to stdout ('console') or to a file ('file')
            filename: the name of the file if log_type is 'file'
        """
        ## logger instance
        self.logger = logger
        ## log_level: the level that should be used for logging
        self.log_level = log_level
        ## boolean to indicate whether to stop the server or not
        self.quit = False
        ## keep track if we are connected with DroneKit
        connection_succeeded = False
        ## how many time have we tried connecting with DroneKit
        attemps = 1
        while not connection_succeeded:
            try:
                if SIM:
                    self.vehicle = dronekit.connect('tcp:127.0.0.1:5760', wait_ready=True, heartbeat_timeout=-1)
                    self.solo = Solo(vehicle=self.vehicle, logging_level=log_level)
                    connection_succeeded = True
                else:
                    self.vehicle = dronekit.connect('udpin:0.0.0.0:14550', wait_ready=False, vehicle_class=SoloVehicle, source_system=255, use_native=True, heartbeat_timeout=-1)
                    self.solo = Solo(vehicle=self.vehicle, logging_level=log_level, log_type=log_type, filename=filename)
                    connection_succeeded = True
            except dronekit.APIException, msg:
                attemps -= 1
                if attemps == 0:
                    self.logger.error("connecting to dronekit failed")
                    self.logger.error(msg)
                    self.signal_fail()
                    exit(1)
                self.logger.debug("re-attempting to connect to dronekit")

        # handle signals to exit gracefully
        signal.signal(signal.SIGTERM, self.signal_handler)
        # handle signals to exit gracefully
        signal.signal(signal.SIGINT, self.signal_handler)

        # Initiate to None in order to be able to compare to None later
        ## NavigationThread instance
        self.nav_thread = None
        ## NavigationHandler instance
        self.nav_handler = None
        ## StatusHandler instance
        self.stat_handler = None
        ## SettingsHandler instance
        self.setting_handler = None
        ## WayPointQueue instance. Here the waypoints the drone has to visit will come
        self.waypoint_queue = WayPointQueue()
        ## socket that will listen to connections from the Server
        self.unix_socket = socket.socket(socket.AF_UNIX,      # Unix Domain Socket
                                         socket.SOCK_STREAM)  # TCP
        try:
            os.remove("/tmp/uds_control")  # remove socket if it exists
        except OSError:
            pass
        try:
            self.unix_socket.bind("/tmp/uds_control")
            self.unix_socket.listen(2)
            self.unix_socket.settimeout(2.0)

            self.nav_thread = NavigationThread(solo=self.solo, waypoint_queue=self.waypoint_queue, logging_level=self.log_level, log_type=log_type, filename=filename)
            self.nav_handler = NavigationHandler(self.solo, self.waypoint_queue, self.nav_thread, logging_level=self.log_level, log_type=log_type, filename=filename)
            self.stat_handler = StatusHandler(self.solo, self.waypoint_queue, logging_level=self.log_level, log_type=log_type, filename=filename)
            self.setting_handler = SettingsHandler(self.solo, logging_level=self.log_level, log_type=log_type, filename=filename)

            self.logger.info("starting the navigation thread")
            self.nav_thread.start()
        except socket.error, msg:
            self.logger.debug("could not bind to port: {0}, quitting".format(msg))
            self.close()

        self.signal_ready()

    ## Intercept the signal that we should quit, so we can do it cleanly
    def signal_handler(self, signal, frame):
        self.close()
        self.logger.debug("exiting the process")

    ## Run the ControlModule and pass the request to the correct handler
    def run(self):
        while not self.quit:
            try:
                client, address = self.unix_socket.accept()
                length = client.recv(4)
                if length is None:
                    self.logger.info("Length is None")
                    raise ValueError
                buffersize = struct.unpack(">I", length)[0]
                raw = client.recv(buffersize)
                packet = json.loads(raw)  # parse the Json we received
                if 'message_type' not in packet:  # every packet should have a MessageType field
                    self.logger.error("every packet should have a message_type field")
                    raise ValueError("Packet has no message_type field")
                if 'message' not in packet:  # every packet should have a Message field
                    self.logger.error("every packet should have a message field")
                    raise ValueError("Packet has no message field")

                message_type = packet['message_type']  # the 'message type' attribute tells us to which class of packet this packet belongs
                message = packet['message']           # the 'message' attribute tells what packet it is, within it's class
                if (message_type == "navigation"):
                    self.logger.info("received a navigation request")
                    self.nav_handler.handle_packet(packet, message)
                    client.send(struct.pack(">I", MessageCodes.ACK))
                elif (message_type == "status"):
                    self.logger.info("received a status request")
                    response = self.stat_handler.handle_packet(packet, message)
                    if response is None:
                        client.send(struct.pack(">I", MessageCodes.ERR))  # something went wrong
                    else:
                        client.send(struct.pack(">I", MessageCodes.STATUS_RESPONSE))
                        client.send(struct.pack(">I", len(response)))
                        client.send(response)
                elif (message_type == "settings"):
                    self.logger.info("received a settings request")
                    response = self.setting_handler.handle_packet(packet, message)
                    # if we got a response, that means we need to start sending heartbeats
                    if response is not None and isinstance(response, tuple):
                        self.logger.info("settings heartbeat configuration")
                        client.send(struct.pack(">I", MessageCodes.START_HEARTBEAT))
                        client.send(struct.pack(">I", len(response[0])))
                        client.send(response[0])
                        client.send(struct.pack(">I", len(response[1])))
                        client.send(response[1])
                    else:
                        self.logger.debug("returning ack")
                        client.send(struct.pack(">I", MessageCodes.ACK))
                else:
                    raise ValueError

            except socket.error, msg:
                pass

            except ValueError, msg:
                self.logger.debug("value error was raised: {0}".format(msg))
                client.send(struct.pack(">I", MessageCodes.ERR))

        self.unix_socket.close()

    ## close the control module and the navigation thread
    def close(self):
        if not self.quit:
            self.logger.info("the control module is exiting")
            self.quit = True
            if self.nav_thread is not None:
                self.nav_thread.stop_thread()
            self.logger.debug("closing dronekit vehicle")
            self.vehicle.close()

    ## signal the server that we are ready to receive requests
    def signal_ready(self):
        home_dir = os.path.expanduser('~')
        if not os.path.exists(os.path.join(home_dir, '.shae')):
            os.mkdir(os.path.join(home_dir, '.shae'))
        cm_rdy = os.path.join(home_dir, '.shae', 'cm_ready')
        with open(cm_rdy, 'a'):
            os.utime(cm_rdy, None)

    ## signal the server that initiation failed
    def signal_fail(self):
        home_dir = os.path.expanduser('~')
        if not os.path.exists(os.path.join(home_dir, '.shae')):
            os.mkdir(os.path.join(home_dir, '.shae'))
        cm_fail = os.path.join(home_dir, '.shae', 'cm_fail')
        with open(cm_fail, 'a'):
            os.utime(cm_fail, None)


if __name__ == '__main__':
    # parse the command line arguments
    log_level = logging.CRITICAL
    log_type = 'console'
    log_file = None
    is_simulation = False
    try:
        argv = sys.argv[1:]  # only keep the actual arguments
        opts, args = getopt.getopt(argv, "l:t:f:sh", ["level=", "type=", "file=", "simulate", "help"])
    except getopt.GetoptError:
        print_help('control_module.py')
        sys.exit(-1)
    for opt, arg in opts:
        if opt in ("-l", "--level"):
            switch = {
                'debug': logging.DEBUG,
                'info': logging.INFO,
                'warning': logging.WARNING,
                'critical': logging.CRITICAL,
            }

            if arg in switch:
                log_level = switch.get(arg)
            else:
                print_help()
                sys.exit(-1)

        elif opt in ("-t", "--type"):
            if arg == 'file':
                log_type = 'file'
        elif opt in ("-f", "--file"):
            log_file = arg
        elif opt in ("-s", "--simulate"):
            is_simulation = True
        elif opt in ("-h", "--help"):
            print_help('control_module.py')
            sys.exit(0)

    # set up logging
    control_logger = logging.getLogger("Control Module")
    formatter = logging.Formatter(logformat, datefmt=dateformat)
    if log_type == 'console':
        handler = logging.StreamHandler(stream=sys.stdout)
    elif log_type == 'file' and log_file is not None:
        handler = logging.FileHandler(filename=log_file)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    control_logger.addHandler(handler)
    control_logger.setLevel(log_level)

    # set up control module
    control_module = ControlModule(control_logger, log_level, is_simulation, log_type, log_file)
    control_module.run()
