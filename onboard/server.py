import threading
import socket
import json
import struct
from global_classes import SIM

import sys
sys.path.append('../')
from simulator.server_simulator import ServerSimulator

class ControlThread (threading.Thread):
    def __init__(self, threadID, data, control_socket, client_socket):
        """
        :type control_socket: socket
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.data = data
        self.control_socket = control_socket
        self.client_socket = client_socket

    def run(self):
        self.control_socket.connect("/tmp/uds_control")
        self.control_socket.send(self.data)
        raw_response = self.control_socket.recv(1024)
        self.control_socket.close()
        status_code = struct.unpack(">I", raw_response)[0]
        if status_code == 200:
            response = bytearray(raw_response)
            self.client_socket.send(response)
            self.client_socket.close()


class Server(object):
    def __init__(self):
        print 'testtest'
        # HOST = "10.1.1.10"
#        print 'firsttest'
#        self.HOST = "localhost"
#        self.PORT = 6332
#        self.quit = False

#        self.serversocket = socket.socket(socket.AF_INET,  # Internet
#                             socket.SOCK_STREAM)  # TCP
#        self.serversocket.bind((self.HOST, self.PORT))
#        self.serversocket.listen(1)  # become a server socket, only 1 connection allowed

#        print 'test'        
#        self.listen()

    # Method is needed for overriding in ServerSimulator
    def handle_raw(self, raw):
        return None

    def listen(self):
        print 'start listening'
        while not self.quit:
            client, address = self.serversocket.accept()
            raw = client.recv(1024)  # buffer size is 1024 bytes
            self.handle_raw(raw)
            control_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            control_thread = ControlThread(1, raw, control_socket=control_socket, client_socket=client)
            print "starting control_thread"
            control_thread.start()
