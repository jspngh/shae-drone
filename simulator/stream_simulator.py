import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gtk
from gi.repository import Gst as gst


class StreamSimulator:
    def start(self):

        # Initialization GStreamer
        GObject.threads_init()
        gst.init(None)

        # Create pipeline
        pipeline = gst.Pipeline()

        # Create elements for pipeline
        source = gst.ElementFactory.make('filesrc', None)
        demux = gst.ElementFactory.make('qtdemux', None)
        queue = gst.ElementFactory.make('queue', None)
        pay = gst.ElementFactory.make('rtpmp4vpay', None)
        address = gst.ElementFactory.make('udpsink', None)

	if (not source or
		not demux or
		not queue or
		not pay or
		not address):
		print 'Niet'
		exit(-1)

        # Add properties to elements
        source.set_property('location', 'test_footage1.mp4')
        demux.set_property('name', 'd')
        address.set_property('host', '127.0.0.1')
        address.set_property('port', 5000)

        # Add elements to pipeline
        pipeline.add(source)
        pipeline.add(demux)
        pipeline.add(queue)
        pipeline.add(pay)
        pipeline.add(address)

        # Link elelemts together
        source.link(demux)
        demux.link(queue)
        queue.link(pay)
        pay.link(address)

        # Set pipeline to PLAYING state
        pipeline.set_state(gst.State.PLAYING)

        # Wait until error or EOS
        bus = pipeline.get_bus()
        msg = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MessageType.ERROR | gst.MessageType.EOS)
        err, debug = msg.parse_error()
	print err
	print debug

        # Free resources.
        pipeline.set_state(gst.State.NULL)

ss = StreamSimulator()
ss.start()
