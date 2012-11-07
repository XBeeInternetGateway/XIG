"""\
    XIG Configuration File

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
        "idigi_data",         # iDigi Data support (upload XBee data->iDigi)
        "idigi_rci",          # iDigi RCI (send data from iDigi to an XBee)
        #"udp",               # UDP URL destination support
        #"io_sample",          # XBee I/O Samples to HTTP
        #"osc",               # Send data to Open Sound Control server
    ]
    
    ## HTTP
    
    # No configuration options at this time.
    

    ## iDigi Data
    idigi_data_max_rate_sec = 30    # maximum upload rate to iDigi in seconds
    idigi_data_max_q_len = 512      # maximum number of samples to save before uploading
    idigi_data_no_errors = False    # maximum number of samples to save before uploading
    
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
    # 
    # You can also set io_sample_destination_url to a dictionary.  If you
    # use a dictionary there must be a key-value pair with a key named
    # "default" and a default.  The other keys may be XBee 64-bit hardware
    # addresses in the ConnectPort format "[00:11:22:33:44:55:66:77]!"
    # mapping to specific URLs.
    #
    # io_sample_destination_url = {
    #     "default": "http://xbee-data.appspot.com/io_sample",
    #     "[00:13:a2:00:40:30:ff:07]!": "http://my.home.com/rx_io_data",
    #     "[00:13:a2:00:40:4a:b9:e5]!": "http//some.otherplace.com/xbee_receive",
    # }

    
    ## Open Sound Control
    
    # A list of server strings of the form "server:port" for all OSC data
    # to be send to:
    osc_targets = [
        # "10.1.1.1:21234
    ]

    ## Global Configuration Variables
    
    # You shouldn't need to change anything in this section unless
    # you know what you've been doing or you've been instructed to
    # do so.
 
    # Should we send the helpfile for all unknown commands or
    # simply ignore them?
    global_always_send_help = True

    # Controls how long must buffers in the system may reach before
    # they are trimmed.  This setting also happens to control the
    # maximum length of a URL or XIG command.
    global_max_buf_size = 256
    
    # Controls how many sessions are allowed to queue up for a
    # single XBee destination.  Normally XBees only request a single
    # session at a time but automatic services may queue up several
    # session requests, such as the I/O service.
    global_max_dest_session_q_len = 8
    
    # How often (in seconds) to call the garbage collector:
    global_gc_interval = 60

    # Log-levels for various sub systems:
    log_level_global = "info"
    log_level_io_kernel = "debug"
     
    # Controls which UDP port number to receive requests
    xbee_udp_port = 5649
   
