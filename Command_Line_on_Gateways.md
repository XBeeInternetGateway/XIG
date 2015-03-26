## Command Line Interface on ConnectPort/XBee Gateway ##

You can launch the XIG from a ConnectPort or XBee Gateway's command line to see an interactive log.
  1. Make sure XIG is not launching automatically (uncheck the automatic launch box in the web interface or Device Cloud interface and reboot the gateway).
  1. Then, for ConnectPort devices use telnet, and for X2e/XBee Gateway devices use ssh to connect to the gateway and launch the XIG by using  the following command at the command prompt:

```
python xig.py
```

You will see a detailed log with all the interactions. Be sure to re-enable automatic launching when you are done, or XIG will stop running at the next reboot!