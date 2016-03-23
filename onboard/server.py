import threading
import socket
import json
import struct
import logging
import sys
import time
from global_classes import SIM, logging_level, MessageCodes


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
        self.control_socket.send(self.data)
        raw_response = self.control_socket.recv(4)
        status_code = struct.unpack(">I", raw_response)[0]
        if status_code == MessageCodes.ACK or status_code == MessageCodes.ERR:  # let the client know if request succeeded or failed
            self.control_socket.close()
            response = bytearray(raw_response)
            self.client_socket.send(response)

        if status_code == MessageCodes.STATUS_RESPONSE:  # send the response to the client
            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            response = self.control_socket.recv(response_length)
            response_length = bytearray(raw_length)
            self.client_socket.send(response_length + response)

        if status_code == MessageCodes.START_HEARTBEAT:
            print "Got a Start HB message"
            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            host = self.control_socket.recv(response_length)
            raw_length = self.control_socket.recv(4)
            response_length = struct.unpack(">I", raw_length)[0]
            ip = self.control_socket.recv(response_length)
            ip = int(ip)
            self.heartbeat_thread.configure(ip, host)
            self.heartbeat_thread.start()
            self.client_socket.send(struct.pack(">I", MessageCodes.ACK))

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
        self.workstation_socket.connect((self.workstation_port, self.workstation_ip))
        print "Running heartbeat thread"
        while not quit:
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
        print "configuring the heartbeat thread"
        self.workstation_ip = ip
        self.workstation_port = port

    def stop_thread(self):
        self.quit = False

# set up logging
server_logger = logging.getLogger("Server")
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
handler.setLevel(logging_level)
server_logger.addHandler(handler)
server_logger.setLevel(logging_level)

if SIM:
    HOST = "localhost"
else:
    HOST = "10.1.1.10"
PORT = 6330
quit = False

serversocket = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
serversocket.bind((HOST, PORT))
serversocket.listen(1)  # become a server socket, only 1 connection allowed

heartbeat_thread = HeartBeatThread(0)

while not quit:
    client, address = serversocket.accept()
    raw = client.recv(1024)  # buffer size is 1024 bytes
    server_logger.info("server received a message")
    control_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    control_thread = ControlThread(1, raw, control_socket=control_socket, client_socket=client, heartbeat_thread=heartbeat_thread)
    control_thread.start()
