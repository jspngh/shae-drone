import sys
import time
import json
import signal
import struct
import socket
import getopt
import logging
import threading
from logging import Logger

from global_classes import MessageCodes


class Server():
    def __init__(self, logger, SIM):
        """
        :type logger: Logger
        :type SIM: bool
        """
        self.logger = logger

        if SIM:
            self.HOST = "localhost"
        else:
            self.HOST = "10.1.1.10"
        self.PORT = 6330
        self.quit = False

        self.serversocket = socket.socket(socket.AF_INET,      # Internet
                                          socket.SOCK_STREAM)  # TCP
        self.serversocket.bind((self.HOST, self.PORT))
        self.serversocket.listen(1)  # become a server socket, only 1 connection allowed

        self.heartbeat_thread = HeartBeatThread(0)

        # handle signals to exit gracefully
        signal.signal(signal.SIGINT, self.sigint_handler)

    def sigint_handler(self, signal, frame):
        self.quit = True
        self.logger.debug("exiting the process")

    def run(self):
        while not self.quit:
            client, address = self.serversocket.accept()
            length = client.recv(4)
            if length is not None:
                buffersize = struct.unpack(">I", length)[0]
            raw = client.recv(buffersize)
            self.logger.info("Server received a message:")
            self.logger.info(raw)
            control_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            control_thread = ControlThread(1, raw, control_socket=control_socket, client_socket=client, heartbeat_thread=self.heartbeat_thread)
            control_thread.start()


class ControlThread (threading.Thread):
    def __init__(self, threadID, data, control_socket, client_socket, heartbeat_thread):
        """
        :type control_socket: Socket
        :type client_socket: Socket
        :type heartbeat_thread: HeartBeatThread
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.data = data
        self.control_socket = control_socket
        self.client_socket = client_socket

        self.heartbeat_thread = heartbeat_thread

    def run(self):
        self.control_socket.connect("/tmp/uds_control")
        self.control_socket.send(struct.pack(">I", len(self.data)))
        self.control_socket.send(self.data)

        raw_response = self.control_socket.recv(4)
        status_code = struct.unpack(">I", raw_response)[0]

        response_message = None

        if status_code == MessageCodes.ACK or status_code == MessageCodes.ERR:  # let the client know if request succeeded or failed
            response_message = bytearray(raw_response)

        if status_code == MessageCodes.STATUS_RESPONSE:  # send the response to the client
            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            response = self.control_socket.recv(response_length)
            response_length = bytearray(raw_length)
            response_message = response_length + response

        if status_code == MessageCodes.START_HEARTBEAT:
            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            host = self.control_socket.recv(response_length)

            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            ip = self.control_socket.recv(response_length)
            ip = int(ip)

            self.heartbeat_thread.configure(ip, host)
            self.heartbeat_thread.start()

            response_message = struct.pack(">I", MessageCodes.ACK)

        # Send response message if it exists
        if response_message is not None:
            self.client_socket.send(response_message)

        self.control_socket.close()
        self.client_socket.close()


class HeartBeatThread (threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.quit = False
        self.workstation_ip = None
        self.workstation_port = None
        self.workstation_socket = socket.socket(socket.AF_INET,      # Internet
                                                socket.SOCK_STREAM)  # TCP

    def run(self):
        if self.workstation_ip is None or self.workstation_port is None:
            return
        print self.workstation_ip
        print self.workstation_port
        self.workstation_socket.connect((self.workstation_ip, self.workstation_port,))
        while not self.quit:
            control_socket = socket.socket(socket.AF_UNIX,      # Unix Domain Socket
                                           socket.SOCK_STREAM)  # TCP
            success = True
            try:
                control_socket.connect("/tmp/uds_control")
                hb_req = {'MessageType': 'status', 'Message': 'heartbeat'}
                hb_req_message = json.dumps(hb_req)
                control_socket.send(hb_req_message)

                raw_response = control_socket.recv(4)
                status_code = struct.unpack(">I", raw_response)[0]

                if status_code == MessageCodes.STATUS_RESPONSE:  # send the heartbeat to the client
                    raw_length = control_socket.recv(4)
                    response_length = struct.unpack(">I", raw_length)[0]
                    response = control_socket.recv(response_length)
                    response_length = bytearray(raw_length)
                    self.workstation_socket.send(response_length + response)
                # close the connection
                control_socket.close()
            except socket.error:
                success = False

            if success:
                # sleep 500ms before requesting another heartbeat
                time.sleep(0.5)

    def configure(self, ip, port):
        self.workstation_ip = ip
        self.workstation_port = port

    def stop_thread(self):
        self.quit = False


def print_help():
    print 'Usage: server.py -s -l <logging_level> -t <logging_type> -f <outputfile>'
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
    server_logger = logging.getLogger("Server")
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s in \'%(name)s\': %(message)s', datefmt='%m-%d %H:%M:%S')
    if log_type == 'console':
        handler = logging.StreamHandler(stream=sys.stdout)
    elif log_type == 'file' and log_file is not None:
        handler = logging.FileHandler(filename=log_file)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    server_logger.addHandler(handler)
    server_logger.setLevel(log_level)
    server_logger.debug("test")

    # set up server
    server = Server(logger=server_logger, SIM=is_simulation)
    server.run()
