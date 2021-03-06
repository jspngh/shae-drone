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

from global_classes import MessageCodes, logformat, dateformat, print_help


## @ingroup Onboard
# @brief Onboard server that will communicate with the workstation
#
# The server will first wait until the control module is ready
# Then start sending hello message until an answer is received
# It will then continuously listen for requests
# And create a ControlThread per request to handle the request
class Server():
    def __init__(self, logger, SIM):
        """
        Initiate the server

        Args:
            logger: logging.Logger instance
            SIM: boolean, is this is a simulation or not
        """
        ## boolean, is this is a simulation or not
        self.SIM = SIM
        ## logger instance
        self.logger = logger

        # Drone specific fields
        if SIM:
            ## the IP address of the drone
            self.HOST = "127.0.0.1"
        else:
            ## the IP address of the drone
            self.HOST = "10.1.1.10"

        ## the port on which the drone will listen to requests
        self.PORT = 6330
        ## boolean to indicate whether to stop the server or not
        self.quit = False

        self.serversocket = socket.socket(socket.AF_INET,      # Internet
                                          socket.SOCK_STREAM)  # TCP
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        ## handle signals to exit gracefully
        signal.signal(signal.SIGTERM, self.signal_handler)
        ## handle signals to exit gracefully
        signal.signal(signal.SIGINT, self.signal_handler)

        # Initiate to None in order to be able to compare to None later
        ## HeartBeatThread instance
        self.heartbeat_thread = None
        ## BroadcastThread instance
        self.broadcast_thread = None
        try:
            self.serversocket.bind((self.HOST, self.PORT))
            self.serversocket.listen(1)  # become a server socket, only 1 connection allowed

            self.serversocket.settimeout(2.0)

            self.heartbeat_thread = HeartBeatThread(self.logger)
            self.broadcast_thread = BroadcastThread(self.logger, self.HOST, self.SIM, self.PORT)
        except socket.error, msg:
            self.logger.debug("Could not bind to port: {0}, quitting".format(msg))
            self.close()

    ## Intercept the signal that we should quit, so we can do it cleanly
    def signal_handler(self, signal, frame):
        self.close()
        self.logger.debug("exiting the process")

    ## Run the server and create a ControlThread when receiving a request
    def run(self):
        self.broadcast_thread.start()
        while not self.quit:
            try:
                # self.logger.debug("Waiting for connection in server")
                client, address = self.serversocket.accept()
                self.broadcast_thread.stop_thread()
                length = client.recv(4)
                if length is not None:
                    buffersize = struct.unpack(">I", length)[0]
                raw = client.recv(buffersize)
                self.logger.info("the server received a message")
                self.logger.debug(raw)
                control_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                control_thread = ControlThread(raw, control_socket=control_socket, client_socket=client,
                                               heartbeat_thread=self.heartbeat_thread, logger=self.logger)
                control_thread.start()
            except socket.error:
                # self.logger.debug("No connection was made")
                pass
        self.serversocket.close()

    def close(self):
        self.quit = True
        self.logger.info("the server is exiting")
        if self.heartbeat_thread is not None:
            self.heartbeat_thread.stop_thread()
        if self.broadcast_thread is not None:
            self.broadcast_thread.stop_thread()


## @ingroup Onboard
# @brief This thread handles one request from the workstation and sends a response back to the workstation
#
# It is created by the Server class and passes the data to the control module
# Then it waits for a response and sends it to the workstation
class ControlThread (threading.Thread):
    def __init__(self, data, control_socket, client_socket, heartbeat_thread, logger):
        """
        Initiate the thread

        Args:
            data: the message to send to the control module
            control_socket: Socket
            client_socket: Socket
            heartbeat_thread: HeartBeatThread instance
            logger: logging.Logger instance
        """
        threading.Thread.__init__(self)
        ## The request from the workstation
        self.data = data
        ## Socket to the control module
        self.control_socket = control_socket
        ## Socket to the workstation
        self.client_socket = client_socket
        ## HeartBeatThread instance
        self.heartbeat_thread = heartbeat_thread
        ## logger instance
        self.logger = logger

    def run(self):
        self.logger.info("running a control-thread to process a message")
        self.control_socket.connect("/tmp/uds_control")
        self.control_socket.send(struct.pack(">I", len(self.data)))
        self.control_socket.send(self.data)

        raw_response = self.control_socket.recv(4)
        status_code = struct.unpack(">I", raw_response)[0]
        self.logger.info("the message was processed")
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

        self.logger.debug("closing controlthread")
        self.control_socket.close()
        self.client_socket.close()


## @ingroup Onboard
# @brief This thread sends regular heartbeats to the workstation containing information about the drone
#
# It is initiated by a ControlThread after a specific message with the settings of the workstation has been received
# The heartbeats contain information like location of the drone and battery status
class HeartBeatThread (threading.Thread):
    def __init__(self, logger):
        """
        Initiate the thread

        Args:
            logger: logging.Logger instance
        """
        threading.Thread.__init__(self)
        ## boolean to indicate whether to stop the thread or not
        self.quit = False
        ## the IP address of the workstation
        self.workstation_ip = None
        ## the port where the workstation listens for heartbeats
        self.workstation_port = None
        ## logger instance
        self.logger = logger

    def run(self):
        if self.workstation_ip is None or self.workstation_port is None:
            return

        self.logger.debug("heartbeat IP address: {0}".format(self.workstation_ip))
        self.logger.debug("heartbeat port: {0}".format(self.workstation_port))
        self.logger.info("hearbeats are being sent to the workstation")

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
                        self.logger.debug("could not connect to the workstation")
                        self.stop_thread()

                # close the connection
                control_socket.close()
                workstation_socket.close()
            except socket.error, msg:
                self.logger.debug("socket error: {0}".format(msg))

            # sleep 500ms before requesting another heartbeat
            time.sleep(1)

    ## method to configure the heartbeat thread with workstation information
    def configure(self, host, port):
        self.workstation_ip = host
        self.workstation_port = port

    ## stop sending heartbeats
    def stop_thread(self):
        self.logger.info("stopping the heartbeat-thread")
        self.quit = True


## @ingroup Onboard
# @brief This thread broadcasts 'hello' messages until a response has been received
#
# This thread first waits for the ControlModule
# The ControlModule can either successfully start of fail to start
# In case of success, 'hello' messages will be sent, in the other case 'fail' messages will be sent
class BroadcastThread(threading.Thread):
    def __init__(self, logger, drone_ip, SIM, commandPort):
        """
        Initiate the thread

        Args:
            logger: logging.Logger instance
            drone_ip: the IP address of the drone_ip
            SIM: boolean, is this is a simulation or not
            commandPort: on which port is the drone listening
        """
        threading.Thread.__init__(self)
        ## boolean, is this is a simulation or not
        self.SIM = SIM
        ## logger instance
        self.logger = logger
        ## the port on which the drone will listen to requests
        self.commandPort = commandPort
        ## the port with which the workstation needs to connect in order to be able to receive the stream
        self.streamPort = 5502
        ## how wide the camera of the drone is able to see
        self.visionWidth = 0.0001
        ## the port on which the workstation listens for 'hello' messages
        self.helloPort = 4849
        ## the IP address of the drone
        self.HOST = drone_ip

        # Drone specific fields
        if SIM:
            ## the IP address of the controller of the drone
            self.controllerIp = self.HOST
            ## the address to broadcast the 'hello' message to
            self.broadcast_address = self.HOST
            ## how the workstation should receive the stream from the drone
            self.streamFile = "rtp://127.0.0.1:5000"
        else:
            ## the IP address of the controller of the drone
            self.controllerIp = "10.1.1.1"
            ## the address to broadcast the 'hello' message to
            self.broadcast_address = "10.1.1.255"
            ## how the workstation should receive the stream from the drone
            self.streamFile = "sololink.sdp"

        ## boolean to indicate whether to stop the thread or not
        self.quit = False

    ## wait for the control module, then start broadcasting the correct message
    def run(self):
        rdy = self.wait_for_control_module()
        if rdy:
            self.broadcast_hello_message()
        else:
            self.broadcast_fail_message()
        return

    ## wait until the control module is ready
    #
    # When the control module is ready, it will change the modification time of a file.
    # Here we poll these files until one is modified.
    def wait_for_control_module(self):
        home_dir = os.path.expanduser('~')
        cm_rdy = os.path.join(home_dir, '.shae', 'cm_ready')
        cm_fail = os.path.join(home_dir, '.shae', 'cm_fail')
        while not (os.path.exists(cm_rdy) or os.path.exists(cm_fail)):
            time.sleep(2)

        while not self.quit:
            curr_time = time.time()
            if os.path.exists(cm_rdy):
                cm_rdy_mod_time = os.path.getmtime(cm_rdy)
                if (curr_time - cm_rdy_mod_time < 5):
                    self.logger.info("the control module is now ready")
                    return True
            if os.path.exists(cm_fail):
                cm_fail_mod_time = os.path.getmtime(cm_fail)
                if (curr_time - cm_fail_mod_time < 5):
                    self.logger.info("the control module has failed to start up properly")
                    return False
            time.sleep(2)

    ## start broadcasting hello messages
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

        self.logger.info("hello messages are being sent to the workstation")
        while not self.quit:
            bcsocket.sendto(hello_json, (self.broadcast_address, self.helloPort))
            self.logger.debug("broadcasting hello to " + str(self.broadcast_address) + ":" + str(self.helloPort))
            try:
                raw_response, address = bcsocket.recvfrom(1024)
                response = json.loads(raw_response)
                if 'message_type' in response:
                    if response['message_type'] == 'hello':
                        self.quit = True
                        self.logger.debug("reply received, stopping broadcast")
            except socket.timeout:
                pass

    ## start broadcasting fail messages
    def broadcast_fail_message(self):
        fail = {"message_type": "fail",
                "ip_drone": self.HOST,
                "ip_controller": self.controllerIp,
                "port_stream": self.streamPort,
                "port_commands": self.commandPort,
                "stream_file": self.streamFile,
                "vision_width": self.visionWidth}
        fail_json = json.dumps(fail)

        bcsocket = socket.socket(socket.AF_INET,        # Internet
                                 socket.SOCK_DGRAM)     # UDP
        bcsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bcsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bcsocket.settimeout(10)
        bcsocket.bind(('', 0))  # OS will select available port
        while not self.quit:
            bcsocket.sendto(fail_json, (self.broadcast_address, self.helloPort))
            self.logger.debug("broadcasting fail message to " + str(self.broadcast_address) + ":" + str(self.helloPort))
            try:
                raw_response, address = bcsocket.recvfrom(1024)
                response = json.loads(raw_response)
                if 'message_type' in response:
                    if response['message_type'] == 'hello':
                        self.quit = True
                        self.logger.debug("reply received, stopping broadcast")
            except socket.timeout:
                pass

    ## stop the broadcast thread
    def stop_thread(self):
        if not self.quit:
            self.logger.info("stopping the broadcast-thread")
            self.quit = True


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
        print_help('server.py')
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
            print_help('server.py')
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
