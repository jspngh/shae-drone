import socket 
import json

def send_response(client, type):
    client.send('Response: Message with type "' + type + '" is correctly received!')
    client.close()

HOST = "127.0.0.1"
PORT = 6330
quit = False

serversocket = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
serversocket.bind((HOST, PORT))
serversocket.listen(1)  # become a server socket, only 1 connection allowed

while not quit:
    client, address = serversocket.accept()
    raw = client.recv(1024)  # buffer size is 1024 bytes
    print 'message received'

    try:
        packet = json.loads(raw)  # parse the Json we received
        if 'MessageType' not in packet:  # every packet should have a MessageType field
            raise ValueError

        message_type = packet['MessageType']  # the message type will decide which module we need to use
	send_response(client, message_type)

    except ValueError:
        print "handle error"
