# Introduction #

The Windows, Macintosh and Linux versions of the XIG come configured by default to connect to login.etherios.com. You can select a different server by editing the 'settings.json' file.


# Details #

New accounts will typically connect to either 'login.etherios.com' or 'login.etherios.co.uk'. The server you connect to is located in the 'settings.json' file for Macintosh, Windows and LInux versions of the XIG. On a ConnectPort, the Device Cloud server settings can be edited via the local HTML interface.

_Windows_:
Edit the address in the 'settings.json' file located in the main xig directory

_Macintosh_:
Change the address by right-clicking on the XIG app, choosing Show Package Contents, then editing the file 'Contents/Resources/settings.json'

_Linux_:
Edit the address in 'xig/src/settings.json'

_ConnectPort_:
Edit the Device Cloud Server Address field under Configuration, Device Cloud screen in the regular web interface. It can also be changed in the command line using 'set mgmtconnection'.