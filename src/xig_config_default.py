"""\
    Modify the contents of the below XigConfig object in order to
    change the configuration of the Xig.  Each option is
    commented as to what it does.
"""

class XigConfig(object):
    # Enable/disable session types; disable sessions by commenting
    # them out.  Disabling sessions may be advantageous if you
    # find you are running out of memory on your ConnectPort.
    #
    # The "xig" session is always available.  It is required by
    # the system.
    #
    session_types = [
        "http",
        "idigi_rci",
        "io_sample",
    ]
    
    # When an I/O sample is received for an XBee address below,
    # An HTTP GET will be called on the given URL with the
    # following string added to the end:
    #
    # ?addr=[00:13:A2:00:4F:38:1B:7E]!&AD0=710&AD1=1...
    io_sample_destination_url = "http://xbee-data.appspot.com/io_sample"
