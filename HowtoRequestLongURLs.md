# Introduction #

The XIG come configured by default to only allow URL requests up to a fixed length.  If you wish to change this limitation, see below.


# Details #

The XIG comes with a Python configuration file named "xig\_config.py".  Near the bottom of the file you'll find a section called "Global Configuration Variables".  In this section there is a variable named "global\_max\_buf\_size."  This variable controls a number of internal XIG behaviors including the maximum length of URLs that the XIG will process.

If you wanted to increase the URL length limit to 512 characters, here is what the updated section to xig\_config.py would look like:

```
    # Controls how long must buffers in the system may reach before
    # they are trimmed.  This setting also happens to control the
    # maximum length of a URL or XIG command.
    global_max_buf_size = 512
```

Save the file, upload to your Digi ConnectPort X gateway, reboot and restart the XIG to have your change take effect!