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
sensor values, scraping Facebook or commanding your robotic kitten army.

XIG offeres a myriad of other interesting and useful communications services
to your XBee network.  For complete documentation and setup instructions
please visit:

http://code.google.com/p/xig/

See also:

http://code.google.com/p/xig/wiki/UserDocumentation
http://faludi.com/xig
http://www.digi.com/products/wireless-routers-gateways/gateways/

XIG is brought to you by an open-source team by makers Robert Faludi,
Jordan Husney and Ted Hayes with valuable support from a community of 
commercial and educational users.


II. RELEASE HISTORY

2011/12/15 - XIG v1.3.2

Fixes issue #12 catching when the radio is in use by another Python
program by printing an error message to console.

Fixes issue #15 where data was being dropped due to XIG not using the
proper maximum receive packet size.

Found and fixed minor issue where XBee receive status messages were
being stored in the rolling command buffer.  Fixing this issue leads
to a small performance enhancement.


2011/11/29 - XIG v1.3.1

Added support for multiple destinations to the io_sample session.
By setting the io_sample_destination_url to a dictionary mapping
hardware address to destination URLs the XIG can now forward
I/O sample information to multiple servers.


2011/09/14 - XIG v1.3.0

Fixed  Issue #10  where URLs containing usernames and passwords 
would cause an exception to be thrown.

Architecture changes to allow for services (such as the I/O sample
service) in addition to sessions with commands driven from an
XBee.

Code re-factorization to split apart growing xig.py into multiple
library files.

New streaming command parser should resolve issues where sessions
could not be aborted if "xig://abort" was not sent in a single
packet.

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

