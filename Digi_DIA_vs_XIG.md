The [DIA](http://www.digi.com/wiki/developer/index.php/Device_Cloud_Wiki) is a very robust data acquisition and control framework from Digi International that runs on Digi's ConnectPort hardware.

The [XIG](http://code.google.com/p/xig/w/edit) is an open source project that also runs on the ConnectPort but its aims are much simpler: the XIG is intended to be an application which allows XBee's to talk to the Internet and the Internet to XBees.  It allows XBee modules to fetch URLs and for Internet applications to reach out to XBees via [Device Cloud](http://devicecloud.com).  The ConnectPort gateway, when used with the XIG, acts as a conduit for data.  It doesn't intend to manipulate the information in any way.

The DIA on the other hand acts as more than a simple conduit. DIA is capable of interfacing between lots of device types (e.g. XBee, serial, Modbus, IP and more), collecting information from them, storing this information in a local database (called the channel database), transforming the data (e.g. Fahrenheit to Celsius), making decisions on the ConnectPort about the data (e.g. the sensor is saying
it's warmer than 25C, turn on the fan!) and, of course, managing interactions with [Device Cloud](http://devicecloud.com).

Here is an older Digi Webinar talking about how to get
started with the DIA: http://www.idigi.com/video/player?videoid=getting-started-with-idigi-dia

In summary: if you are looking for a simple conduit or if you want to prototype an XBee-based design interacting with the Internet quickly, use the XIG.  If you want to make decisions on the gateway, integrate
in other systems, or build something commercial-ready: use the [DIA](http://www.digi.com/wiki/developer/index.php/Device_Cloud_Wiki).