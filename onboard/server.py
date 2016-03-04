import socket
import json

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
            control_socket.connect("/tmp/uds_control")
            control_socket.send(raw)
            control_socket.close()
        elif (message_type == "status"):
            status_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            status_socket.connect("/tmp/uds_status")
            status_socket.send(raw)
            status_socket.close()
        elif (message_type == "settings"):
            settings_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            settings_socket.connect("/tmp/uds_settings")
            settings_socket.send(raw)
            settings_socket.close()
        else:
            raise ValueError
    except ValueError:
        print "handle error"
    finally:
        client.close()
