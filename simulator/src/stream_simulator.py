"""
To be able to run the simulator, the python bindings for vlc are needed:
sudo pip install python-vlc
"""
import vlc
import socket
import threading
import logging
import sys


# TODO: listen on port 5502 for connection, then start to stream
class StreamSimulator(threading.Thread):
    """
    The StreamSimulator executes the following command: cvlc testfootage.mp4 --sout '#rtp{dst=127.0.0.1,port=5000,ptype-video=96,mux=ts}'
    """
    def __init__(self, footage):
        """
        :param footage: The path to the video with testfootage that will be played back by the stream simulator
        """
        self.footage = footage  # '../videos/testfootage.mp4'

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
        self.videosocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	self.ip = self.get_local_ip()

        try:
            self.videosocket.bind((self.ip, 5502))
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
            self.logger.debug("starting stream")
            options = "sout=#rtp{dst=127.0.0.1,port=5000,ptype-video=96,mux=ts}"
            media = self.Instance.media_new(self.footage, options)
            self.player.set_media(media)
            self.player.play()
        else:
            self.videosocket.close()

    def stop_thread(self):
        self.logger.debug("stopping stream simulator")
        self.quit = True
        self.player.stop()
        self.Instance.release()

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip = s.getsockname()[0]
        s.close()
        return ip
