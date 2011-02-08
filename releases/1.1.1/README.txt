XBee Internet Gateway for Digi ConnectPort X2/3/4/8
---------------------------------------------------
by Rob Faludi (http://faludi.com),   
   Jordan Husney (http://jordan.husney.com),
   & Ted Hayes (http://log.liminastudio.com),

I. Introduction

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


II. Installation

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
       
    
III. Usage

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

There are other commands available when using XIG:

     All commands are CR "\\r" or NL "\\n" delimited, except where noted.
     help or xig://help:   displays this file
     quit or xig://quit:   quits program
     abort or xig://abort: aborts the current session
    
     http://<host/path> retrieves a URL
     https://<host/path> retrieves a secure URL 
     http://<user:pass@host/path> retrieves a URL using username and password
     https://<user:pass@host/path> retrieves a URL using username and password 
 

IV. Known Issues

o  The following URL schemes are not yet supported (help contribute!):

    ftp://<host/path>
    ftp://<username:password@host/path>  
    telnet://<host:port>
    mailto:<addr@host>


V. Release History

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

