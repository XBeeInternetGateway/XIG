"""\
    Modify the contents of the below XigConfig object in order to
    change the configuration of the Xig.  Each option is
    commented as to what it does.
"""

class XigConfig(object):
    
    ## Session Types
    
    # Enable/disable session types; disable sessions by commenting
    # them out.  Disabling sessions may be advantageous if you
    # find you are running out of memory on your ConnectPort.
    #
    # The "xig" session is always available.  It is required by
    # the system.
    #
    session_types = [
        "http",               # HTTP (fetch web pages)
        "idigi_rci",          # iDigi RCI (send data from iDigi to an XBee)
        "udp",               # UDP URL destination support
        #"io_sample",          # XBee I/O Samples to HTTP
        #"osc",               # Send data to Open Sound Control server
    ]
    
    
    ## HTTP
    
    # No configuration options at this time.
    
    
    ## iDigi RCI
    
    # No configuration options at this time.
    

    ## UDP URL destination support
    
    # No configuration options at this time
    
    
    ## XBee I/O Sample HTTP Indications
    
    # When an I/O sample is received for an XBee address below,
    # An HTTP GET will be called on the given URL with the
    # following string added to the end:
    #
    # ?addr=[00:13:A2:00:4F:38:1B:7E]!&AD0=710&AD1=1...
    #io_sample_destination_url = "http://xbee-data.appspot.com/io_sample"

    
    ## Open Sound Control
    
    # A list of server strings of the form "server:port" for all OSC data
    # to be send to:
    osc_targets = [
        # "10.1.1.1:21234
    ]
