# XBee Internet Gateway for Digi ConnectPort X2(d,e)/4/8, OSX, Windows and Linux #

---

by Rob Faludi (http://faludi.com), Jordan Husney (http://jordan.husney.com), Michael Sutherland (http://digi.com), Francisco Gil Martinez (http://digi.com) & Ted Hayes (http://log.liminastudio.com)

NOTE: "iDigi" was [rebranded](http://www.digi.com/news/pressrelease?prid=856) "Device Cloud by Etherios" in April of 2013.



## I. INTRODUCTION ##

The XBee Internet Gateway makes it easy to connect Digi's XBee radios to the Internet. Plug a sensor into your XBee and stream environmental data right into your online application. Attach a switch, motors or lights to an XBee, then activate them from the Internet. All the tricky technical aspects of web connections are all handled for you behind the scenes! Add an Arduino or microcontroller to make your XBee a web browser that can read from or post to any web page. The XIG gives your XBee a simple yet completely flexible pathway to any web service, including ones that you created yourself. You can read industrial sensor networks, analyze and control distant equipment, scrape gossip from Facebook or simply flip switches in your own home!

Xbee Internet Gateway will soon work directly on Macintosh, Windows and Linux computers. For longer-term, dedicated installations we recommend running XIG on Digi's line of ConnectPort gateways, that can host stable connections via Ethernet, cellular data, satellite links and more.

XIG is an open-source team effort lead by Internet of Things enthusiasts Rob Faludi and Jordan Husney. It was written with valuable support from a community of commercial and educational users including Ted Hayes, Michael Sutherland, Tom Collins and many others.

**For more information on Digi's gateways see the following web-page:**

http://www.digi.com/products/wireless-routers-gateways/

## II. INSTALLATION ##

To install the XIG, follow the appropriate instructions:
  * [Macintosh\_Installation](Macintosh_Installation.md)
  * [Windows\_Installation](Windows_Installation.md)
  * [Linux\_Installation](Linux_Installation.md)
  * [ConnectPort\_Installation](ConnectPort_Installation.md)

## III. USAGE ##

In order for your XBee to interact with the XIG application, it
must be associated to the same personal area network as the Digi
ConnectPort X gateway.

For gateways with ZigBee (Series 2 hardware) you need to:
Configure your Series 2 radio as a ZB firmware Router or End-Device in AT mode, using the X-CTU software
If you’ve set a PAN on the gateway then configure that same PAN on the radio using the ATID command
Set the radio’s destination address to zero: ATDH0 and ATDL0 (this is the default)


For gateways with 802.15.4 (Series 1 hardware) you need to:
Configure your Series 1 radio with the latest firmware using the X-CTU software
Set a PAN ID on your gateway, then configure that same PAN on the radio using the ATID command
Confirm that the MY address on the gateway is 0.
Set the radio’s destination address to zero: ATDH0 and ATDL0 (this is the default)


Digi's Getting Started documentation for the ConnectPort X gateway has full information on associating your XBee with the gateway. Rob Faludi’s book, Building Wireless Sensor Networks also has a full chapter that covers setup.

Once your XBee is associated to your gateway, you may retrieve the
contents of a website from your XBee by sending the URL of the site
to the gateway via your XBee.  For example, sending:

```
http://en.wikipedia.org/w/index.php?title=Hello_world_program&printable=yes\r\n
```

...will retrieve the printable version of Wikipedia's entry on a
"Hello, World Program" to your XBee.  Note that the "\r" and "\n"
characters are the ASCII carriage-return and line-feed characters. If you are using Arduino you could also use the Serial.println() command to add the line feeds:

```
Serial.println(“http://en.wikipedia.org/w/index.php?title=Hello_world_program&printable=yes”);
```

Arduino Sample Code:
Attach the XBee to your Arduino’s hardware serial port (pins 0 and 1), then send a URL and you’ll get back the response. For example to send your request from Arduino:

```
Serial.println(“http://www.faludi.com/test.html”);
```

And to read the response back:

```
if (Serial.available()) {

char inChar = Serial.read();

print ( inChar );

}
```

There are other commands available when using XIG.  You can get a
listing of available commands by entering "help" or "xig://help" from
your XBee's serial connection and pressing the enter key.  Here is
an example of available commands:

```
 help or xig://help:   displays this file
 quit or xig://quit:   quits program
 abort or xig://abort: aborts the current session
 time or xig://time:   prints the time in ISO format

 http://host/path: retrieves a URL
 https://host/path: retrieves a secure URL
 http://host:port/path: retrieves a URL from the specified port
 http://user:pass@host/path: retrieves a URL using username and password
 https://user:pass@host/path: retrieves a URL using username and password
 udp://host:port: initiate UDP session to remote server and port number
                  (note: session will end only by using xig://abort)
```

Asking XIG for help will also show a listing of additional services that
have been configured to run with the XIG.  For example, the XIG may
provide a service to pass messages from the Internet (even if the
ConnectPort gateway is behind a firewall!) to your XBees via the Device Cloud service.  Here is an example of available services:

dc\_rci is running, accepting commands on do\_command target "xig"
> io\_sample running, making requests to configured destinations


## IV. COMMANDS & SERVICES ##

Below is specific information on commands and services available from
within the XIG:

### A. HTTP ###

The set of HTTP commands allows your XBee to have access to the
World Wide Web. Websites may be fetched by using the http or https URL
command scheme.

For example, by entering the following into the XBee's serial port:

```
http://www.whattimeisit.com
```

You'll fetch the contents of the "What Time is It" web page.  If you
host your own website you can return simpler bits of information.
Using the http facility even allows you to send information from your
XBee:

```
http://yourwebapplication.appspot.com/?name=sensor1&temp=72
```

Sending URLs in this form allows a remote web application to capture
data.

If a site becomes unresponsive or the page is very large, you
may send the "xig://abort" command followed by a carriage return
or line feed character to ask the XIG to terminate the current
HTTP operation.  Because a lot of data may be buffered
in the ConnectPort or within the mesh network itself, it may take
some time to abort the retrieval operation.

At present only HTTP GET requests are supported.


### B. UDP ###

If you wish to stream data to a remote UDP server, you may use the
UDP command to do so.  Commands are of the form:

```
udp://servername:port
```

After XIG receives the command the session begins immediately.  Data
is sent directly to the specified server.

Use the xig://abort command to end the session.


### C. Open Sound Control ###

Contributed by Axel Roest, the Open Sound Control session allows for
XBees to multicast Open Sound Control events to a set of targets running
on remote Open Sound Control severs.  Configuration of Open Sound
Control servers is specified within the XIG configuration file's
"osc\_targets" section (see the CONFIGURATION section, below).


### D. Sending Messages from the Internet to an XBee Using Device Cloud RCI ###

If you'd like to send data to an XBee from anywhere in the world, you
may use the Device Cloud RCI service to do so.  After you've created a free
[Developer Zone](http://www.etherios.com/products/devicecloud/developerzone) account and associated your ConnectPort gateway you can use the "API Explorer" section of Device Cloud
to send messages to XBees.

Once you're in the "API Explorer" click "SCI Targets" and use
the form to select the numeric ID of your ConnectPort gateway
(your numeric ID is printed on a label on the bottom of your gateway)
and add the ID to the list.  Click OK.  From the "Examples" drop-down
menu select SCI->Python Callback.  Notice the HTTP Method will change to POST. Change the "target" field from
"rci\_callback\_example" to "xig".  Change the word "ping" to the following
XIG command taking care to replace the hw\_address parameter to the
address of your XBee:

```
<send_data hw_address="00:13:a2:00:40:3a:8b:90!">Hello World!\r\n</send_data>
```

In the end you'll have a message that resembles this:

```
<sci_request version="1.0">
  <send_message>
    <targets>
      <device id="00000000-00000000-00409DFF-FF43FA07"/>
    </targets>
    <rci_request version="1.1">
      <do_command target="xig">
        <send_data hw_address="00:13:a2:00:40:3a:8b:90!">Hello World!\r\n</send_data>
      </do_command>
    </rci_request>
  </send_message>
</sci_request>
```

If you click the send button from the Web Services Console toolbar it
will send your message from the Internet to your XBee via
Device Cloud.  Wow!

You can easily write a program or use one of many web tools (such as
the excellent command-line application "curl") to send messages to
any XBee anywhere in the world, even if it's behind a firewall.

Aside from the `<send_data>` command, the Device Cloud RCI XIG command also
supports the `<send_hexdata>` command.  This command allows for the
transmission of arbitrary binary data.  For example:

```
<send_hexdata hw_address="00:13:a2:00:40:3a:8b:90!">414243</send_hexdata>
```

The above command will send the characters "ABC" to the remote XBee.

**NOTE:** when using the ConnectPort X2e, it uses Device Cloud's _device\_request_ command.  When using _device\_request_ the commands to the XIG must be HTML escaped.  For example:

```
<sci_request version="1.0">
  <data_service>
    <targets>
      <device id="00000000-00000000-00409DFF-FF521DEC"/>
    </targets>
    <requests>
      <device_request target_name="xig">
        &lt;send_data hw_address="00:13:a2:00:40:3a:8b:90!"&gt;Hello World!\r\n&lt;/send_data&gt;
      </device_request>
    </requests>
  </data_service>
</sci_request>
```

### E. Setting or Getting Remote XBee AT Settings via Device Cloud RCI ###

If you'd like to set or get remote AT parameters of an XBee from anywhere in the
world using Device Cloud, you can use the following XML syntax to do so.  First, follow the
instructions from the previous section ("Sending Messages from the Internet to an XBee Using Device Cloud RCI")
to learn how to format and send a message to the XIG using Device Cloud.  To set a remote AT
parameters, format a message like this:

```
<sci_request version="1.0">
  <send_message>
    <targets>
      <device id="00000000-00000000-00409DFF-FF43FA07"/>
    </targets>
    <rci_request version="1.1">
      <do_command target="xig">
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D0" value="1" />       
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D1" value="4" />
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D2" value="4" />       
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D3" value="3" />
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D4" value="3" />
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="IR" value="30000" />
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="IC" value="0x000C" />
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="WR" apply="True" />
      </do_command>
    </rci_request>
  </send_message>
</sci_request>
```

In order to read a remote AT paramter, you format the commands like this:

```
<at hw_address="00:13:a2:00:40:48:5a:23!" command="NI" />
```

You'll get a response from Device Cloud which will looks like this:

```
<sci_reply version="1.0">
  <send_message>
    <device id="00000000-00000000-00409DFF-FF43FA07">
      <rci_reply version="1.1">
        <do_command target="xig">
          <at_response command="NI" operation="get" result="ok" type="str" value="JordansXBee"/>
        </do_command>
      </rci_reply>
    </device>
  </send_message>
</sci_reply>
```

**NOTE:** when using the ConnectPort X2e, it uses Device Cloud's _device\_request_ command.  When using _device\_request_ the commands to the XIG must be HTML escaped.  For example:

```
<sci_request version="1.0">
  <data_service>
    <targets>
      <device id="00000000-00000000-00409DFF-FF521DEC"/>
    </targets>
    <requests>
      <device_request target_name="xig">
        &lt;at hw_address="00:13:A2:00:40:99:60:27!" command="NI" /&gt;
        &lt;at hw_address="00:13:A2:00:40:99:60:27!" command="D2" value="2" /&gt;
      </device_request>
    </requests>
  </data_service>
</sci_request>
```

### F. Sending Sample Data to Device Cloud ###

Need a place to stash your data?  You can configure the XIG to automatically
decode XBee sample packets or specially formatted serial strings and upload them
to Device Cloud.  Once on Device Cloud you can retrieve the data by fetching

> http://login.etherios.com/ws/DataStream

Data will be returned in the following format:

```
<?xml version="1.0" encoding="ISO-8859-1"?>
<result>
   <resultSize>510</resultSize>
   <requestedSize>1000</requestedSize>
   <pageCursor>7bffdfca-1fe-ac96ec7b</pageCursor>
   <DataStream>
      <cstId>3</cstId>
      <streamId>dia/channel/00000000-00000000-00409DFF-FF3DA1BE/XBee_112233/AD0</streamId>
      <dataType>DOUBLE</dataType>
      <forwardTo/>
      <currentValue>
         <id>4aa2eb66-fe6a-11e1-98d1-404007e9381f</id>
         <timestamp>1347626827000</timestamp>
         <serverTimestamp>1347626830656</serverTimestamp>
         <data>604.0</data>
         <description/>
         <quality>0</quality>
      </currentValue>
      <description/>
      <units></units>
      <dataTtl>8035200</dataTtl>
      <rollupTtl>63244800</rollupTtl>
   </DataStream>
  <!-- ... more records ... -->
</result>
```

When I/O sample packets are uploaded to Device Cloud, the streamId will be
set to dia/channel/XBee\_AABBCC/IO\_PIN where AABBCC is the DL value of your XBee and IO\_PIN
will be set to the name of the I/O pin (e.g. "AD0").

You can also upload data to Device Cloud using your own names by sending strings to the
XIG formatted in the following way:

```
    dc_data:names=N1,N2,..Nn&values=V1,V2,..,VN,[units=U1,U2,..,Un]
    dc_data:names=temp,humidity,alarm&values=21,40,False&units=C,RH%,bool
```

Data will then appear on Device Cloud with a streamId
set to dia/channel/XBee\_AABBCC/NAME where AABBCC  ddInstanceName of XBee\_AABBCC where AABBCC
is the DL value of the XBee and NAME is N[0..N] from the above dc\_data command.

The idigi\_data\_max\_rate\_sec controls the number of seconds which must
elapse before sample batches are upload to Device Cloud.  This is set to prevent the gateway
from uploading too often and not having the time to process incoming data from
the XBee network.

You can retrieve historical data and perform analytical queries by fetching

> http://login.etherios.com/ws/DataStream_/streamId_

For example:

> http://login.etherios.com/ws/DataPoint/dia/channel/00000000-00000000-00409DFF-FF3DA1BE/XBee_112233/AD0

This will fetch all historical data associated with the AD0 channel of XBee\_112233:

```
<?xml version="1.0" encoding="ISO-8859-1"?>
<result>
   <resultSize>314</resultSize>
   <requestedSize>1000</requestedSize>
   <pageCursor>4aa2eb66-fe6a-11e1-98d1-404007e9381f</pageCursor>
   <requestedStartTime>-1</requestedStartTime>
   <requestedEndTime>-1</requestedEndTime>
   <DataPoint>
      <id>162c60a5-fe4e-11e1-847e-404082824def</id>
      <cstId>3</cstId>
      <streamId>dia/channel/00000000-00000000-00409DFF-FF3DA1BE/sensor0/light</streamId>
      <timestamp>1347614713073</timestamp>
      <serverTimestamp>1347614714222</serverTimestamp>
      <data>0.0</data>
      <description/>
      <quality>0</quality>
   </DataPoint>
   <DataPoint>
      <id>2507f51d-fe4e-11e1-847e-404082824def</id>
      <cstId>3</cstId>
      <streamId>dia/channel/00000000-00000000-00409DFF-FF3DA1BE/sensor0/light</streamId>
      <timestamp>1347614738000</timestamp>
      <serverTimestamp>1347614740471</serverTimestamp>
      <data>638.0</data>
      <description/>
      <quality>0</quality>
   </DataPoint>
```

If you don't want all of the data and would rather receive hourly averages, you can modify the query the following way:

> http://login.etherios.com/ws/DataPoint/dia/channel/00000000-00000000-00409DFF-FF3DA1BE/sensor0/light?rollupInterval=hour&rollupMethod=average

It's also possible to get data pushed to your web application via HTTP.  For more information on this feature please see [Device Cloud Web Service Programmers Guide](http://ftp1.digi.com/support/documentation/90002008_G.pdf) and refer to the section on the Device Cloud Monitor API.


### G. I/O Sample HTTP Trigger ###

By enabling this service you can enable the XIG to generate HTTP requests
each time it receives an I/O packet.  This is done by configuring the
XIG (see the CONFIGURATION section, below) and setting the
"io\_sample\_destination\_url" paramter.  For example:

```
io_sample_destination_url = "http://xbee-data.appspot.com/io_sample"
```

Properly formatted port numbers, https and authentication should all work fine in the URL. By using the above configuration the XIG will generate HTTP GET requests
containing a query predicate that reflects the I/O state of an XBee,
including raw sample values.  An example HTTP GET request sent from
the XIG looks like this:

```
http://xbee-data.appspot.com/io_sample?addr=%5B00%3A13%3Aa2%3A00%3A40%3A3a%3A8b%3A90%5D%21&DIO2=
1&DIO3=1&DIO0=1&DIO1=1
```


## V. CONFIGURATION ##

The configuration file is called "xig\_config.py" and it is included
with the XIG distribution.  You may edit this file with a text
editor.
  * On the Digi ConnectPort you can upload it to the Python files section of the ConnectPort gateway.
  * On the version for Windows the file may be added to the root directory alongside xig\_app.exe.
  * On the version for Macintosh, right-click on the xig application and select "Show Package Contents", then navigate to Contents/Resources to edit the xig\_config.py file.
  * On the version for Linux the file may be added to the xig/src directory.

If the configuration file is not found, a default configuration will be used.

If you wish to enable or disable XIG commands or services, refer to
the "session\_types" configuration variable.  Un-commenting or commenting
out items in the "sessions\_types" list enables or disables a service
respectively.

The Windows, Macintosh and Linux software versions also have a _second_ configuration file that includes settings for things like baud rate, com port, device id, Device Cloud server and more.
  * On Linux you can edit those additional parameters in xig/src/settings.json
  * On Macintosh you can change the parameters by right-clicking on the XIG app, choosing Show Package Contents, then editing the file Contents/Resources/settings.json
  * On Windows you can edit the parameters in the settings.json file located in the main xig directory

## VI. UPDATES ##
  * **Follow** the [XIGproject on Twitter](http://twitter.com/xigproject).
  * **Join** the [XBee Internet Gateway discussion group](http://groups.google.com/group/xbee-internet-gateway)


## VII. KNOWN ISSUES ##

  * Some slowdown has accumulated on the ConnectPort X2 due to increased processing requirements
  * The following URL schemes are not yet supported (help contribute!):
    * [ftp://host/path](ftp://host/path)
    * [ftp://username:password@host/path](ftp://username:password@host/path)
    * [telnet://host:port](telnet://host:port)
    * [mailto:addr@host](mailto:addr@host)

## VIII. RELEASE HISTORY ##

See ReleaseHistory.