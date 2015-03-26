# Introduction #

The XIG comes configured by default with a variety of features enabled. To reduce its memory footprint, especially on the ConnectPort X2, you can disable unused services in the configuration file. This may prevent rejected connections, especially in heavy use situations.


# Details #

The XIG comes with a Python configuration file named "xig\_config.py".  Near the beginning of the file you'll find a section called "Session Types".  In this section you can comment out different services, using the # sign to disable them.

For example, if you are only using the HTTP service you could disable the others like this:

```
    session_types = [
        "http",               # HTTP (fetch web pages)
        #"dc_data",         # Device Cloud Data support (upload XBee data->Device Cloud)
        #"dc_rci",          # Device Cloud RCI (send data from Device Cloud to an XBee)
        #"udp",               # UDP URL destination support
        #"io_sample",          # XBee I/O Samples to HTTP
        #"osc",               # Send data to Open Sound Control server
    ]
```

Save the file, upload to your Digi ConnectPort X gateway, reboot and restart the XIG to have your changes take effect!