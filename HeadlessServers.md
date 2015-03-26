## Running on Headless Servers ##

To run the XIG on a Macintosh, Linux or Windows computer that does _not_ have a monitor, you will need to launch the XIG from the command line with the --no browser argument.

On Linux, follow the regular instructions, but launch the application using:
```
/usr/bin/python2.7 gui/xig_app.py --no-browser
```

On Macintosh, open a terminal window and follow the Linux instructions in their entirety, also launching the application with:
```
/usr/bin/python2.7 gui/xig_app.py --no-browser
```

On Windows, open the Command Prompt, change to the directory with xig\_app, then launch the application with:
```
xig_app --no-browser
```

Once you have the program running, you will need to administer it remotely from a web browser by going to its hostname or IP address on port 8000. The URL will be similar to one of these, using your own information of course:
```
http://192.168.1.200:8000
http://yourheadlessserver.yourdomain.com:8000
```

## Command Line Options ##

You can see all the command line options by using the `--help` argument as follows:

```
$ /usr/bin/python2.7 gui/xig_app.py -help
No handlers could be found for logger "cp4pc.xbee"
xig - XBee Internet Gateway (XIG) v1.5.0b15 starting.
usage: xig_app.py [-h] [--no-browser]

XBee Internet Gateway (XIG) with Web GUI.

optional arguments:
  -h, --help    show this help message and exit
  --no-browser  do not launch the web browser
```