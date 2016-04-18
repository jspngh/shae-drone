import os
import sys
import time
import json
import signal
import struct
import socket
import getopt
import logging
import threading

from global_classes import MessageCodes, logformat, dateformat


class Server():
    def __init__(self, logger, SIM):
        """
        :type logger: logging.Logger
        :type SIM: bool
        """
        self.SIM = SIM
        self.logger = logger
        self.heartbeat_thread = None

        # Drone specific fields
        if SIM:
            self.HOST = "127.0.0.1"
        else:
            self.HOST = "10.1.1.10"

        self.PORT = 6330
        self.quit = False

        self.serversocket = socket.socket(socket.AF_INET,      # Internet
                                          socket.SOCK_STREAM)  # TCP
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.heartbeat_thread = None
        self.broadcast_thread = None
        try:
            self.serversocket.bind((self.HOST, self.PORT))
            self.serversocket.listen(1)  # become a server socket, only 1 connection allowed

            self.heartbeat_thread = HeartBeatThread(self.logger)
            self.broadcast_thread = BroadcastThread(self.logger, self.SIM, self.PORT)

            # handle signals to exit gracefully
            signal.signal(signal.SIGTERM, self.signal_handler)
            signal.signal(signal.SIGINT, self.signal_handler)
        except socket.error, msg:
            self.logger.debug("Could not bind to port: {0}, quitting".format(msg))
            self.close()

    def signal_handler(self, signal, frame):
        self.close()
        self.logger.debug("exiting the process")

    def run(self):
        self.broadcast_thread.start()
        while not self.quit:
            try:
                client, address = self.serversocket.accept()
                self.broadcast_thread.stop_thread()
                length = client.recv(4)
                if length is not None:
                    buffersize = struct.unpack(">I", length)[0]
                raw = client.recv(buffersize)
                self.logger.info("Server received a message:")
                self.logger.info(raw)
                control_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                control_thread = ControlThread(raw, control_socket=control_socket, client_socket=client,
                                               heartbeat_thread=self.heartbeat_thread, logger=self.logger)
                control_thread.start()
            except socket.error, msg:
                self.logger.debug("Error in server: {0}, quitting".format(msg))
                self.close()

    def close(self):
        self.quit = True
        self.logger.debug("Stopping the server")
        if self.heartbeat_thread is not None:
            self.heartbeat_thread.stop_thread()
        if self.broadcast_thread is not None:
            self.broadcast_thread.stop_thread()


class ControlThread (threading.Thread):
    def __init__(self, data, control_socket, client_socket, heartbeat_thread, logger):
        """
        :type control_socket: Socket
        :type client_socket: Socket
        :type heartbeat_thread: HeartBeatThread
        :type logger: logging.Logger
        """
        threading.Thread.__init__(self)
        self.data = data
        self.control_socket = control_socket
        self.client_socket = client_socket

        self.heartbeat_thread = heartbeat_thread
        self.logger = logger

    def run(self):
        self.logger.debug("running controlthread")
        self.control_socket.connect("/tmp/uds_control")
        self.control_socket.send(struct.pack(">I", len(self.data)))
        self.control_socket.send(self.data)

        raw_response = self.control_socket.recv(4)
        self.logger.debug("got a response in controlthread")
        status_code = struct.unpack(">I", raw_response)[0]
        self.logger.debug("response has statuscode {0}".format(status_code))
        if status_code == MessageCodes.ACK or status_code == MessageCodes.ERR:  # let the client know if request succeeded or failed
            response = bytearray(raw_response)
            try:
                self.client_socket.send(struct.pack(">H", status_code))
            except socket.error, msg:
                self.logger.debug("Error in server thread: {0}".format(msg))

        if status_code == MessageCodes.STATUS_RESPONSE:  # send the response to the client
            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            response = self.control_socket.recv(response_length)
            try:
                self.client_socket.send(struct.pack(">H", status_code))
                self.client_socket.send(struct.pack(">H", response_length + 4))
                self.client_socket.send(bytearray(raw_length) + response)
            except socket.error, msg:
                self.logger.debug("Error in server thread: {0}".format(msg))

        if status_code == MessageCodes.START_HEARTBEAT:
            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            host = self.control_socket.recv(response_length)

            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            port = self.control_socket.recv(response_length)
            port = int(port)

            self.heartbeat_thread.configure(host, port)
            self.heartbeat_thread.start()
            try:
                self.client_socket.send(struct.pack(">H", MessageCodes.ACK))
            except socket.error, msg:
                self.logger.debug("Error in server thread: {0}".format(msg))

        self.control_socket.close()
        self.client_socket.close()


class HeartBeatThread (threading.Thread):
    def __init__(self, logger):
        """
        :type logger: logging.Logger
        """
        threading.Thread.__init__(self)
        self.quit = False
        self.workstation_ip = None
        self.workstation_port = None
        self.logger = logger

    def run(self):
        if self.workstation_ip is None or self.workstation_port is None:
            return

        self.logger.debug(self.workstation_ip)
        self.logger.debug(self.workstation_port)

        while not self.quit:
            workstation_socket = socket.socket(socket.AF_INET,      # Internet
                                               socket.SOCK_STREAM)  # TCP

            control_socket = socket.socket(socket.AF_UNIX,      # Unix Domain Socket
                                           socket.SOCK_STREAM)  # TCP
            try:
                control_socket.connect("/tmp/uds_control")
                hb_req = {'message_type': 'status', 'message': 'heartbeat'}
                hb_req_message = json.dumps(hb_req)
                control_socket.send(struct.pack(">I", len(hb_req_message)) + hb_req_message)

                raw_response = control_socket.recv(4)
                status_code = struct.unpack(">I", raw_response)[0]

                if status_code == MessageCodes.STATUS_RESPONSE:  # send the heartbeat to the client
                    raw_length = control_socket.recv(4)
                    response_length = struct.unpack(">I", raw_length)[0]
                    response = control_socket.recv(response_length)
                    response_length = bytearray(raw_length)
                    self.logger.debug("heartbeat: {0}".format(response))

                    try:
                        workstation_socket.connect((self.workstation_ip, self.workstation_port))
                        workstation_socket.send(struct.pack(">H", len(response) + 4))
                        workstation_socket.send(response_length + response)
                    except socket.error:
                        self.logger.debug("Could not connect to the workstation")
                        self.stop_thread()

                # close the connection
                control_socket.close()
                workstation_socket.close()
            except socket.error, msg:
                self.logger.debug("Socket error: {0}".format(msg))

            # sleep 500ms before requesting another heartbeat
            time.sleep(1)  # time.sleep(0.5)

    def configure(self, host, port):
        self.workstation_ip = host
        self.workstation_port = port

    def stop_thread(self):
        self.logger.debug("Stopping heartbeat thread")
        self.quit = True


class BroadcastThread(threading.Thread):
    def __init__(self, logger, SIM, commandPort):
        """
        :type logger: logging.Logger
        """
        threading.Thread.__init__(self)
        self.SIM = SIM
        self.logger = logger
        self.commandPort = commandPort
        self.streamPort = 5502
        self.visionWidth = 0.0001
        self.helloPort = 4849
        # Drone specific fields
        if SIM:
            self.HOST = "127.0.0.1"
            self.controllerIp = "127.0.0.1"
            self.broadcast_address = "127.0.0.1"
            self.streamFile = "rtp://127.0.0.1:5000"
        else:
            self.HOST = "10.1.1.10"
            self.controllerIp = "10.1.1.1"
            self.broadcast_address = "10.1.1.255"
            self.streamFile = "sololink.sdp"
        self.quit = False

    def run(self):
        self.wait_for_control_module()
        self.broadcast_hello_message()
        return

    def wait_for_control_module(self):
        home_dir = os.path.expanduser('~')
        cm_rdy = os.path.join(home_dir, '.shae', 'cm_ready')
        while not os.path.exists(cm_rdy):
            time.sleep(2)
        cm_mod_time = os.path.getmtime(cm_rdy)
        curr_time = time.time()
        while(curr_time - cm_mod_time > 10):
            time.sleep(2)
            cm_mod_time = os.path.getmtime(cm_rdy)
            curr_time = time.time()

        self.logger.debug("Control module is now ready")

    def broadcast_hello_message(self):
        hello = {"message_type": "hello",
                 "ip_drone": self.HOST,
                 "ip_controller": self.controllerIp,
                 "port_stream": self.streamPort,
                 "port_commands": self.commandPort,
                 "stream_file": self.streamFile,
                 "vision_width": self.visionWidth}
        hello_json = json.dumps(hello)

        bcsocket = socket.socket(socket.AF_INET,        # Internet
                                 socket.SOCK_DGRAM)     # UDP
        bcsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bcsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bcsocket.settimeout(10)
        bcsocket.bind(('', 0))  # OS will select available port
        while not self.quit:
            bcsocket.sendto(hello_json, (self.broadcast_address, self.helloPort))
            self.logger.debug("Broadcasting hello")
            try:
                raw_response, address = bcsocket.recvfrom(1024)
                response = json.loads(raw_response)
                if 'message_type' in response:
                    if response['message_type'] == 'hello':
                        self.quit = True
                        self.logger.debug("Reply received, stopping broadcast")
            except socket.timeout:
                pass

    def stop_thread(self):
        self.logger.debug("Stopping broadcast thread")
        self.quit = True


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
            print_help()
            sys.exit(0)

    # set up logging
    server_logger = logging.getLogger("Server")
    formatter = logging.Formatter(logformat, datefmt=dateformat)
    if log_type == 'console':
        handler = logging.StreamHandler(stream=sys.stdout)
    elif log_type == 'file' and log_file is not None:
        handler = logging.FileHandler(filename=log_file)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    server_logger.addHandler(handler)
    server_logger.setLevel(log_level)

    # set up server
    server = Server(logger=server_logger, SIM=is_simulation)
    server.run()
