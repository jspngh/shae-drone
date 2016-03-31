"""
To be able to run the simulator, you need to install the python bindings for vlc:
sudo pip install python-vlc
"""
import vlc
import time
import socket
import threading
import logging
import sys


# TODO: listen on port 5502 for connection, then start to stream
class StreamSimulator(threading.Thread):
    """
    The StreamSimulator executes the following command: cvlc testfootage.mp4 --sout '#rtp{dst=127.0.0.1,port=5000,ptype-video=96,mux=ts}'
    """
    def __init__(self):
        self.logger = logging.getLogger("StreamSimulator")
        formatter = logging.Formatter('[%(levelname)s] %(asctime)s in \'%(name)s\': %(message)s', datefmt='%m-%d %H:%M:%S')
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        threading.Thread.__init__(self)
        self.Instance = vlc.Instance('--input-repeat=-1')  # loop the testfootage
        self.player = self.Instance.media_player_new()
        self.videosocket = socket.socket(socket.AF_INET,      # Internet
                                         socket.SOCK_STREAM)  # TCP
        try:
            self.videosocket.bind(("127.0.0.1", 5502))
            self.videosocket.settimeout(2.5)
            self.videosocket.listen(1)
            self.quit = False

        except socket.error, msg:
            self.logger.debug("Could not bind to port: {0}, quitting".format(msg))
            self.quit = True

    def run(self):
        # first wait for a connection, then start streaming
        connected = False
        while not (connected or self.quit):
            try:
                client, address = self.videosocket.accept()
                connected = True
            except socket.timeout:
                pass

        if not self.quit:
            self.logger.debug("Starting stream")
            footage = '../videos/testfootage.mp4'
            options = "sout=#rtp{dst=127.0.0.1,port=5000,ptype-video=96,mux=ts}"
            media = self.Instance.media_new(footage, options)
            self.player.set_media(media)
            self.player.play()

    def stop_thread(self):
        self.logger.debug("Stopping streamsimulator")
        self.quit = True
        self.player.stop()
        self.Instance.release()
