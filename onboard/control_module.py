import os
import sys
import json
import signal
import struct
import socket
import getopt
import logging
from logging import Logger
from threading import RLock
from dronekit import connect, time

from solo import Solo
from navigation_handler import NavigationHandler
from settings_handler import SettingsHandler
from status_handler import StatusHandler
from global_classes import MessageCodes, WayPointQueue


class ControlModule():
    def __init__(self, logger, log_level, SIM):
        """
        :type logger: Logger
        :type SIM: bool
        """
        self.logger = logger
        self.log_level = log_level
        self.quit = False

        if SIM:
            self.vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)
            self.solo = Solo(vehicle=self.vehicle)
        else:
            self.vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)
            self.solo = Solo(vehicle=self.vehicle)

        # handle signals to exit gracefully
        signal.signal(signal.SIGINT, self.sigint_handler)

        self.waypoint_queue = WayPointQueue()  # in this queue, the waypoints the drone has to visit will come
        self.unix_socket = socket.socket(socket.AF_UNIX,      # Unix Domain Socket
                                         socket.SOCK_STREAM)  # TCP
        try:
            os.remove("/tmp/uds_control")  # remove socket if it exists
        except OSError:
            pass
        self.unix_socket.bind("/tmp/uds_control")
        self.unix_socket.listen(2)

        self.nav_thread = NavigationHandler.NavigationThread(1, solo=self.solo, waypoint_queue=self.waypoint_queue, logging_level=self.log_level)
        self.logger.debug("Starting Navigation Thread")
        self.nav_thread.start()

    def sigint_handler(self, signal, frame):
        self.quit = True
        self.logger.debug("exiting the process")

    def run(self):
        while not self.quit:
            client, address = self.unix_socket.accept()
            try:
                length = client.recv(4)
                if length is None:
                    self.logger.info("Length is None")
                    raise ValueError
                buffersize = struct.unpack(">I", length)[0]
                raw = client.recv(buffersize)
                packet = json.loads(raw)  # parse the Json we received
                if 'MessageType' not in packet:  # every packet should have a MessageType field
                    self.logger.info("every packet should have a MessageType field")
                    raise ValueError
                if 'Message' not in packet:  # every packet should have a Message field
                    self.logger.info("every packet should have a Message field")
                    raise ValueError

                message_type = packet['MessageType']  # the 'message type' attribute tells us to which class of packet this packet belongs
                message = packet['Message']           # the 'message' attribute tells what packet it is, within it's class
                if (message_type == "navigation"):
                    self.logger.info("received a navigation request")
                    nav_handler = NavigationHandler(packet, message, self.solo, self.waypoint_queue, logging_level=self.log_level)
                    nav_handler.handle_packet()
                    client.send(struct.pack(">I", MessageCodes.ACK))
                elif (message_type == "status"):
                    self.logger.info("received a status request")
                    stat_handler = StatusHandler(packet, message, self.solo, self.waypoint_queue, logging_level=self.log_level)
                    response = stat_handler.handle_packet()
                    if response is None:
                        client.send(struct.pack(">I", MessageCodes.ERR))  # something went wrong
                    else:
                        client.send(struct.pack(">I", MessageCodes.STATUS_RESPONSE))
                        client.send(struct.pack(">I", len(response)))
                        client.send(response)
                elif (message_type == "settings"):
                    self.logger.info("received a settings request")
                    sett_handler = SettingsHandler(packet, message, self.solo, logging_level=self.log_level)
                    response = sett_handler.handle_packet()
                    # if we got a response, that means we need to start sending heartbeats
                    if response is not None and isinstance(response, tuple):
                        self.logger.info("Settings configuration")
                        client.send(struct.pack(">I", MessageCodes.START_HEARTBEAT))
                        client.send(struct.pack(">I", len(response[0])))
                        client.send(response[0])
                        client.send(struct.pack(">I", len(response[1])))
                        client.send(response[1])
                    else:
                        self.logger.info("Returning ack")
                        client.send(struct.pack(">I", MessageCodes.ACK))
                else:
                    raise ValueError

            except ValueError:
                # TODO: handle error
                self.logger.info("We might have a little problem")
                client.send(struct.pack(">I", MessageCodes.ERR))


def print_help():
    print 'Usage: control_module.py -s -l <logging_level> -t <logging_type> -f <outputfile>'
    print 'Options:'
    print '  -l --level: \t\t Specify the logging level\n' \
          '\t\t\t The available options are \'debug\', \'info\', \'warning\' and \'critical\'\n' \
          '\t\t\t This defaults to \'critical\''
    print '  -t --type: \t\t Specify the logging type, available options are:\n' \
          '\t\t\t   \'console\', which prints the logs to the console, this is the default\n' \
          '\t\t\t   \'file\', which prints the logs to a file, a filename needs to be specified'
    print '  -f --file: \t\t Specify the name of the logfile'
    print '  -s --simulate: \t\t Indicate that a simulated vehicle is used'
    print '  -h --help: \t\t Display this information'


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
        print_help()
        sys.exit(-1)
    for opt, arg in opts:
        if opt in ("-l", "--level"):
            if arg == 'debug':
                log_level = logging.DEBUG
            elif arg == 'info':
                log_level = logging.INFO
            elif arg == 'warning':
                log_level = logging.WARNING
            elif arg == 'critical':
                log_level = logging.CRITICAL
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
            print_help()
            sys.exit(0)

    # set up logging
    control_logger = logging.getLogger("Control Module")
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s in \'%(name)s\': %(message)s', datefmt='%m-%d %H:%M:%S')
    if log_type == 'console':
        handler = logging.StreamHandler(stream=sys.stdout)
    elif log_type == 'file' and log_file is not None:
        handler = logging.FileHandler(filename=log_file)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    control_logger.addHandler(handler)
    control_logger.setLevel(log_level)

    # set up control module
    control_module = ControlModule(control_logger, log_level, is_simulation)
