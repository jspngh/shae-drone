import threading
import socket
import json
import struct


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
        if status_code == 200 or status_code == 500:
            response = bytearray(raw_response)
            self.client_socket.send(response)
            self.client_socket.close()


# HOST = "10.1.1.10"
HOST = "localhost"
PORT = 6330
quit = False

serversocket = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
serversocket.bind((HOST, PORT))
serversocket.listen(1)  # become a server socket, only 1 connection allowed

while not quit:
    client, address = serversocket.accept()
    raw = client.recv(1024)  # buffer size is 1024 bytes
    control_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    control_thread = ControlThread(1, raw, control_socket=control_socket, client_socket=client)
    control_thread.start()
