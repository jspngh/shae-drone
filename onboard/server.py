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
        if status_code == 200:
            response = bytearray(struct.pack(">I", 200))
            self.client_socket.send(response)
            self.client_socket.close()


class StatusThread (threading.Thread):
    def __init__(self, threadID, data, status_socket, client_socket):
        """
        :type control_socket: socket
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.data = data
        self.status_socket = status_socket
        self.client_socket = client_socket

    def run(self):
        self.status_socket.connect("/tmp/uds_status")
        self.status_socket.send(self.data)
        # recv_data = self.control_socket.recv(1024)
        self.status_socket.close()
        # self.client_socket.send(recv_data)


class SettingsThread (threading.Thread):
    def __init__(self, threadID, data, settings_socket, client_socket):
        """
        :type control_socket: socket
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.data = data
        self.settings_socket = settings_socket
        self.client_socket = client_socket

    def run(self):
        self.settings_socket.connect("/tmp/uds_settings")
        self.settings_socket.send(self.data)
        # recv_data = self.control_socket.recv(1024)
        self.settings_socket.close()
        # self.client_socket.send(recv_data)


HOST = "10.1.1.10"
PORT = 6330

serversocket = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
serversocket.bind((HOST, PORT))
serversocket.listen(1)  # become a server socket, only 1 connection allowed

while True:
    client, address = serversocket.accept()
    raw = client.recv(1024)  # buffer size is 1024 bytes
    try:
        packet = json.loads(raw)  # parse the Json we received
        if 'MessageType' not in packet:  # every packet should have a MessageType field
            raise ValueError

        message_type = packet['MessageType']  # the message type will decide which module we need to use
        if (message_type == "control"):
            control_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            control_thread = ControlThread(1, raw, control_socket=control_socket, client_socket=client)
            control_thread.start()
        elif (message_type == "status"):
            status_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            status_thread = StatusThread(1, raw, control_socket=status_socket, client_socket=client)
            status_thread.start()
        elif (message_type == "settings"):
            settings_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            settings_thread = SettingsThread(1, raw, control_socket=settings_socket, client_socket=client)
            settings_thread.start()
        else:
            raise ValueError
    except ValueError:
        print "handle error"
