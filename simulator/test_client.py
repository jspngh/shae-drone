import socket
import json
import struct

HOST = "127.0.0.1"
PORT = 6330

path_message = {'MessageType': 'control', 'Message': 'path'}
json_message = json.dumps(path_message)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_STREAM)  # TCP

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.send(json_message)
    print "message sent"
    data = sock.recv(1024)
    print data
#    print struct.unpack(">I", data)[0]

finally:
    sock.close()
