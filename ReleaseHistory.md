# RELEASE HISTORY #

## 2014/7/7 - XIG v1.5.1 ##

Released from beta.

Full site updated to use "Device Cloud" rebranding from now-deprecated "iDigi."

## 2014/4/30 - XIG v1.5.1b20 ##

Change the UID in the web interface, rebranding the iDigi references to
Device Cloud.

Added support for dc\_data.

## 2012/11/11 - XIG v1.5.1b19 ##

Optimized garbage collection for ConnectPort X2.  Should resolve
XIG crashing due to insufficient memory on this platform.

Added timezone support so samples show up and graph properly when
using iDigi's DataStreams.

Added support for the ConnectPort X2e.

Added some useful logging messages to the idigi\_rci and idigi\_data
session types.

Log levels now configurable in configuration file.

Improved upload algorithm for idigi\_data session.

Work around for exceptions during execution on Raspberry Pi Raspbian
platform when using Raspian's stock Python v2.7.1 interpreter.

Fixes for DigiMesh.

Misc bugfixes

## 2012/07/14 - XIG v1.5.0 ##

First release of the XIG for Macintosh, Windows and Linux computers.
Code restructuring and other bug fixes.

## 2012/03/06 - XIG v1.4.2 ##

Fixes [issue #19](https://code.google.com/p/xig/issues/detail?id=#19); added additional exception handling around httplib
and global exception handler to prevent XIG from crashing.

Fixed gateway crash in idigi\_data session.


## 2012/01/29 - XIG v1.4.1 ##

Added parser for IS AT command. If you use the remote-AT command
functionality via iDigi and execute an IS command on a remote
XBee, the XIG will parse the IS packet for you.


## 2012/01/29 - XIG v1.4.0 ##

Added idigi\_data session allowing automatic I/O sample and free-form
key/value data pairs to be upload to the iDigi Dia data service
(see http://www.idigi.com).

Enhanced the idigi\_rci session to allow the setting of remote AT
commands.

Fixed [issue #18](https://code.google.com/p/xig/issues/detail?id=#18), a crash caused due to a missing import statement.


## 2011/12/15 - XIG v1.3.2 ##

Fixes [issue #12](https://code.google.com/p/xig/issues/detail?id=#12) catching when the radio is in use by another Python
program by printing an error message to console.

Fixes [issue #15](https://code.google.com/p/xig/issues/detail?id=#15) where data was being dropped due to XIG not using the
proper maximum receive packet size.

Found and fixed minor issue where XBee receive status messages were
being stored in the rolling command buffer.  Fixing this issue leads
to a small performance enhancement.


## 2011/11/29 - XIG v1.3.1 ##

Added support for multiple destinations to the io\_sample session.
By setting the io\_sample\_destination\_url to a dictionary mapping
hardware address to destination URLs the XIG can now forward
I/O sample information to multiple servers.

## 2011/09/14 - XIG v1.3.0 ##

Fixed [Issue #10](https://code.google.com/p/xig/issues/detail?id=#10) where URLs containing usernames and passwords would
cause an exception to be thrown.

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


## 2011/07/28 - XIG v1.2.1 ##

Fixes HTTP state machine to resolve [issue #7](https://code.google.com/p/xig/issues/detail?id=#7): "Failure after URL
with no response"


## 2011/05/30 - XIG v1.2.0 ##

Completes feature request input as [issue #5](https://code.google.com/p/xig/issues/detail?id=#5): "Query for NTP time
directly to Gateway" XIG can now return the current time understood
by the ConnectPort X2 gateway by sending XIG the xig://time command.

Minor code refactoring updates including common modules moved into
their own library directory

Re-introduction of the ability for the XIG to be run on a PC for
UDP simulation mode.  Useful for testing with the netcat utility.


## 2011/02/08 - XIG v1.1.1 ##

Two significant bug fixes.

Fixes [issue #4](https://code.google.com/p/xig/issues/detail?id=#4)  "XIG stops responding after invalid URL entered"
Fixes bug reported by e-mail where URL elements including and after
'?' character in query string are ignored.


## 2010/11/17 - XIG v1.1.0 ##

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


## 2010/09/25 - XIG v1.0.0 ##

Released v1.0.0 for Maker Faire New York 2010.  First public release.