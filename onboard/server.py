import socket

UDP_IP = "10.1.1.10"
UDP_PORT = 5444

log = open('/etc/solo-services/shae-server/logs/log', 'w')
serversocket = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
serversocket.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = serversocket.recvfrom(1024)  # buffer size is 1024 bytes
    print "received message:", data
    log.write(data)
    log.write("\n")
    log.flush()
log.close()
