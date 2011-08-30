XBee Internet Gateway for Digi ConnectPort X2/3/4/8
---------------------------------------------------
by Rob Faludi (http://faludi.com),   
   Jordan Husney (http://jordan.husney.com),
   & Ted Hayes (http://log.liminastudio.com),

I. INTRODUCTION

The XBee Internet Gateway ("XIG") is an application written for Digi's
ConnectPort series of XBee-to-IP gateways.  The XBee Internet Gateway 
gives any device the ability to connect seamlessly to the Internet by 
mirroring the interactions humans have with web browsers. Any device 
with an XBee radio can send a web URL to the XIG and receive back the 
contents of that web page. All the tricky technical aspects of web 
connections are all handled for you behind the scenes.

This simple service gives your prototype or device a simple yet completely 
flexible pathway to any web service that you can imagine, including posting
sensor values, scraping Facebook or commanding your robot army.

XIG is an open-source team effort lead by makers Robert Faludi,
Jordan Husney  and Ted Hayes with valuable support from a community of 
commercial and educational users.

For more information on Digi's gateways see the following web-page:

http://www.digi.com/products/wirelessdropinnetworking/gateways/


II. INSTALLATION

To install the XIG, ensure your Digi ConnectPort X gateway is powered
on and configured to access the Internet (by following Digi's
ConnectPort X Getting Started Guide).  Next you must transfer the
XIG application to the gateway and enable it to auto-start.  This may
be done through the iDigi Management Portal.

Follow the following steps:

1) Open a web-browser and navigate to http://www.idigi.com

2) Click on the "iDigi Login" button, and create a new iDigi
   developer account by clicking on the "Are you a new user?"
   link
   
3) Log in to your new iDigi account and click on the "Devices"
   link from the menu on the left side of the page
   
4) Ensure your Digi ConnectPort X gateway is powered on and
   connected to the same network as your computer
   
5) On the iDigi portal site, click the "+" icon from the Device
   toolbar.  Your gateway will be discovered by the iDigi portal
   site.  Select your gateway and then click the "OK" button.
   
6) Click the refresh icon on the toolbar until your gateway status
   transitions to "Connected"; double click on the your gateway
   in the table and its configuration UI will appear
   
7) Select "Python" from the configuration UI

8) Click the upload button from the "Python Files" toolbar,
   use "Browse" to select "xig.py" and "_xig.zip" from the XIG
   binary release and click "OK" to upload the files
   
9) Under "Auto-start Settings" add "xig.py" to one of the
   "Auto-start Command Line" entries and check the corresponding
   auto-start "Enable" check boxes.
   
10) Click the Save button.  Your new settings will be written to
    the gateway.
   
11) Click on the "Devices" tab, right click on the gateway entry
    and select "Administration->Reboot..."  Click "Yes" to reboot
    the device and wait.
       
    
III. USAGE

In order for your XBee to interact with the XIG application, it
must be associated to the same personal area network as the Digi
ConnectPort X gateway.  Follow Digi's Getting Started documentation
for the ConnectPort X gateway in order to associate your XBee with
the gateway.

Once your XBee is associated to your gateway, you may retrieve the
contents of a website from your XBee by sending the URL of the site
to the gateway via your XBee.  For example, sending:

http://en.wikipedia.org/w/index.php?title=Hello_world_program&printable=yes\r\n

...will retrieve the printable version of Wikipedia's entry on a
"Hello, World Program" to your XBee.  Note that the "\r" and "\n"
characters are the ASCII carriage-return and line-feed characters.

There are other commands available when using XIG.  You can get a
listing of available commands by entering "help" or "xig://help" from
your XBee's serial connection and pressing the enter key.  Here is
an example of available commands:

 help or xig://help:   displays this file
 quit or xig://quit:   quits program
 abort or xig://abort: aborts the current session
 time or xig://time:   prints the time in ISO format

 http://host/path: retrieves a URL
 https://host/path: retrieves a secure URL
 http://user:pass@host/path: retrieves a URL using username and password
 https://user:pass@host/path: retrieves a URL using username and password
 udp://host:port: initiate UDP session to remote server and port number
                  (note: session will end only by using xig://abort)

Asking XIG for help will also show a listing of additional services that
have been configured to run with the XIG.  For example, the XIG may
provide a service to pass messages from the Internet (even if the
ConnectPort gateway is behind a firewall!) to your XBees via the
iDigi Device Cloud service.  Here is an example of available services:

 idigi_rci is running, accepting commands on do_command target "xig"
 io_sample running, making requests to configured destinations


IV. COMMANDS & SERVICES

Below is specific information on commands and services available from
within the XIG:

A. HTTP

The set of HTTP commands allows your XBee to have access to the
World Wide Web. Websites may be fetched by using the http or https URL
command scheme.

For example, by entering the following into the XBee's serial port:

http://www.whattimeisit.com

You'll fetch the contents of the "What Time is It" web page.  If you
host your own website you can return simpler bits of information.
Using the http facility even allows you to send information from your
XBee:

http://yourwebapplication.appspot.com/?name=sensor1&temp=72

Sending URLs in this form allows a remote web application to capture
data.

If a site becomes unresponsive or the page is very large, you
may send the "xig://abort" command followed by a carriage return
or line feed character to ask the XIG to terminate the current
HTTP operation.  Do note that since a lot of data may be buffered
in the ConnectPort or within the mesh network itself it may take
quite awhile to abort the retrieval operation.

At present only HTTP GET commands are supported.


B. UDP

If you wish to stream data to a remote UDP server, you may use the
UDP command to do so.  Commands are of the form:

udp://servername:port

After XIG receives the command the session begins immediately.  Data
is sent directly to the specified server.

Use the xig://abort command to end the session.


C. Open Sound Control

Contributed by Axel Roest, the Open Sound Control session allows for
XBees to multicast Open Sound Control events to a set of targets running
on remote Open Sound Control severs.  Configuration of Open Sound
Control servers is specified within the XIG configuration file's
"osc_targets" section (see the CONFIGURATION section, below).


D. Sending Messages from the Internet to an XBee Using iDigi RCI

If you'd like to send data to an XBee from anywhere in the world, you
may use the iDigi RCI service to do so.  After you've created a free
account on http://www.idigi.com and associated your ConnectPort gateway
you can use the "Web Services Console" section of iDigi 
to send messages to XBees.

Once you're in the "Web Services Console" click "SCI Targets" and use
the form to select the numeric ID of your ConnectPort gateway
(your numeric ID is printed on a label on the bottom of your gateway)
and add the ID to the list.  Click OK.  From the "Examples" drop-down
menu select SCI->Python Callback.  Change the "target" field from
"rci_callback_example" to "xig".  Change the word "ping" to the following
XIG command taking care to replace the hw_address parameter to the
address of your XBee:

<send_data hw_address="00:13:a2:00:40:3a:8b:90!">Hello World!\r\n</send_data>

In the end you'll have a message that resembles this:

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

If you click the send button from the Web Services Console toolbar it
will send your message from the Internet to your XBee via the iDigi
Device Cloud.  Wow!

You can easily write a program or use one of many web tools (such as
the excellent command-line application "curl") to send messages to
any XBee anywhere in the world, even if it's behind a firewall.

Aside from the <send_data> command, the iDigi RCI XIG command also
supports the <send_hexdata> command.  This command allows for the
transmission of arbitrary binary data.  For example:

<send_hexdata hw_address="00:13:a2:00:40:3a:8b:90!">414243</send_hexdata>

The above command will send the characters "ABC" to the remote XBee.


E. I/O Sample HTTP Trigger

By enabling this service you can enable the XIG to generate HTTP requests
each time it receives an I/O packet.  This is done by configuring the
XIG (see the CONFIGURATION section, below) and setting the
"io_sample_destination_url" paramter.  For example:

io_sample_destination_url = "http://xbee-data.appspot.com/io_sample"

By using the above configuration the XIG will generate HTTP GET requests
containing a query predicate that reflects the I/O state of an XBee,
including raw sample values.  An example HTTP GET request sent from
the XIG looks like this:

http://xbee-data.appspot.com/io_sample?addr=%5B00%3A13%3Aa2%3A00%3A40%3A3a%3A8b%3A90%5D%21&DIO2=
1&DIO3=1&DIO0=1&DIO1=1


V. CONFIGURATION

The configuration file is called "xig_config.py" and it is included
with the XIG distribution.  You may edit this file with a text
editor and upload it to the Python files section of the ConnectPort
gateway.  If the configuration file is not found, a default configuration
shall be used.

If you wish to enable or disable XIG commands or services, refer to
the "session_types" configuration variable.  Un-commenting or commenting
out items in the "sessions_types" list enables or disables a service
respectively.


VI. KNOWN ISSUES

o  The following URL schemes are not yet supported (help contribute!):

    ftp://<host/path>
    ftp://<username:password@host/path>  
    telnet://<host:port>
    mailto:<addr@host>


VII. Release History

2011/08/30 - XIG v1.3.0

Architecture changes to allow for services (such as the I/O sample
service) in addition to sessions with commands driven from an
XBee.

Added the I/O Sample HTTP service.

Added the iDigi RCI service.

Merged in and modified the UDP service from Axel Roest.

Merged in Open Sound Control (OSC) service by Axel Roest.

README documentation updates.


2011/07/28 - XIG v1.2.1

Fixes HTTP state machine to resolve issue #7: "Failure after URL 
with no response"


2011/05/30 - XIG v1.2.0

Completes feature request input as issue #5: "Query for NTP time
directly to Gateway" XIG can now return the current time understood
by the ConnectPort X2 gateway by sending XIG the xig://time command.

Minor code refactoring updates including common modules moved into
their own library directory

Re-introduction of the ability for the XIG to be run on a PC for
UDP simulation mode.  Useful for testing with the netcat utility.


2011/02/08 - XIG v1.1.1

Two significant bug fixes. 

Fixes issue #4  "XIG stops responding after invalid URL entered"
Fixes bug reported by e-mail where URL elements including and after
'?' character in query string are ignored.
 

2010/11/17 - XIG v1.1.0

All transmissions from the ConnectPort gateway to destination XBees are
acknowledged and automatically retried if the transmit should fail. This
enables the XIG to function more cleanly with XBee devices configured for
lower baud rates.

In addition, the maximum transmission unit (MTU) for XBees is now being
dynamically determined.  This will enable the XIG to work on very large 
XBee networks where many-to-one and source routing is enabled.

The debug print messages have been changed in this release; some session
messages were outright removed while XBee interactions present more
informative and clear information.


2010/09/25 - XIG v1.0.0

Released v1.0.0 for Maker Faire New York 2010.  First public release.

