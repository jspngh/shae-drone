import socket
import json

HOST = "10.1.1.10"
PORT = 6330

# log = open('/etc/solo-services/shae-server/logs/log', 'w')
serversocket = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
serversocket.bind((HOST, PORT))
serversocket.listen(1)  # become a server socket, only 1 connection allowed


while True:
    client, address = serversocket.accept()
    raw = client.recv(1024)  # buffer size is 1024 bytes
    data = json.loads(raw)
    print "received message:", data
    # log.write(data)
    # log.write("\n")
    # log.flush()

    msg_class = data['class']
    if (msg_class == "Location"):
        fc_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        fc_socket.connect("/tmp/flight_control")
        fc_socket.send(raw)
# log.close()
