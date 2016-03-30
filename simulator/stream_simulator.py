"""
To be able to run the simulator, you need to install the python bindings for vlc:
sudo pip install python-vlc
"""
import vlc
import time
import socket
import threading


# TODO: listen on port 5502 for connection, then start to stream
class StreamSimulator(threading.Thread):
    """
    The StreamSimulator executes the following command: cvlc testfootage.mp4 --sout '#rtp{dst=127.0.0.1,port=5000,ptype-video=96,mux=ts}'
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()
        self.videosocket = socket.socket(socket.AF_INET,      # Internet
                                         socket.SOCK_STREAM)  # TCP
        self.videosocket.bind(("127.0.0.1", 5502))
        self.videosocket.listen(1)

    def run(self):
        # first wait for a connection, then start streaming
        client, address = self.videosocket.accept()
        footage = 'testfootage.mp4'
        options = "sout=#rtp{dst=127.0.0.1,port=5000,ptype-video=96,mux=ts}"
        media = self.Instance.media_new(footage, options)
        self.player.set_media(media)
        self.player.play()

        # 5 is the 'stopped' state, 6 is the 'ended' state
        while (self.player.get_state() != 6 and self.player.get_state() != 5):
            time.sleep(1)

    def stop_thread(self):
        self.quit = True
