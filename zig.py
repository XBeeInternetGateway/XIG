NAME = 'ZigBee Internet Gateway (zig)'
VERSION = '1.00a35'
TIMEOUT = 0                             # default length of time (s) before main loop automatically times out, 0 runs forever
SLEEP_DUR = 0.00                        # sleep delay
TERMINATOR = "\r"                       # command terminator byte
QUIT_CODE = "^"
CLEAR_CODE = "`"			# manually clear your request buffer

print NAME + ' v' + VERSION
print 'Unzipping and loading modules...'

import sys, time, os
from socket import *
from select import *

APP_ARCHIVE = "WEB/python/zig_library.zip"
sys.path.insert(0, APP_ARCHIVE)
sys.path.insert(0, os.path.join(APP_ARCHIVE, "lib"))

import urllib, digicli
print '  ...done.'

stopTime = 0

############ NEXT STEPS ############
""""
log transaction to file system
get UTC time for logs
write log header to file

use dictionary dict = {} to store buffers for different addresses
for key in dict.keys()

"""
####################################


## TURN ON CONNECTION TO IDIGI ##
def idigiOn():
    success,response = digicli.digicli("set mgmtconnection conntype=client connenabled=on clntreconntimeout=60 svraddr1=en://developer.idigi.com")
    if success==False:
        print  "iDigi settings failed: " + str(response)
    else:
        print "iDigi settings succeeded. " + str(response)
    return success

## OBTAIN XBEE VERSION ##
def getXBeeVersion():
    success, response = digicli.digicli('display xbee address')
    if success:
        for line in response:
            if line.find('  firmware_version (VR): 0x')>=0:
                return line[27:31]
    return '0000'

## OBTAIN LOCAL IP ADDRESS ##
def getIPAddr():
    success, response = digicli.digicli('show network')
    if success:
        for line in response:
            if line.find('  ipaddress          : ')>=0:
                return line[23:37].strip()
    return '000.000.000.000'

helpFile = '\n\r---------------------------\n\r'+ NAME + ' v' + VERSION + '  IP: ' + getIPAddr() + """
\r  by Rob Faludi <faludi.com> and Ted Hayes <log.liminastudio.com>\r
\r
ARGUMENTS:\r
 timeout: Time in seconds before program automatically quits. If not used, program runs indefinitely.\r
COMMANDS:\r
 All commands are carriage-return (CR / ASCII 13 / "\\r") delimited, except where noted.\r
\r
 help:  displays this file\r
 ^:     quits program, does not require delimiting\r
 `:     clears your request buffer\r
\r
 http://<host/path> receives a URL\r
 https://<host/path> receives a secure URL\r
 http://<host/path:port>\r
 https://<host/path:port>\r
 ftp://<host/path>\r
 ftp://<username:password@host & path>\r
 \r
USE:\r
 The recommeded speed is 115200 baud which can be set with ATBD7\r
 Lower baud rates may work if you are receiving short responses\r
\r
 The following formats are NOT yet supported:\r
  http://<username:password@host/path>\r
  telnet://<host:port>\r
  mailto:<addr@host>\r
  XBee I/O into a database\r
---------------------------\r
"""


print 'Initializing URL calls...'
urllib.urlopen('http://www.google.com')
print '  ...done.'

# Turn on iDigi connections
idigiOn()

# Get radio hardware version
response = getXBeeVersion()
series = response[0]
print "XBee version 0x" + str(response) + " series " + str(series)


if len(sys.argv) > 1: # if there's an argument we use it for the stop time
    stopTime = int(sys.argv[1])
    print 'Stopping after %d seconds' % (stopTime,)
else:
    stopTime = TIMEOUT # otherwise use default
    print 'Running indefinitely. Send '+QUIT_CODE+' to quit.'

startTime = time.clock()

# Create a socket using the ZigBee address family, datagram mode and a proprietary transport
sd = socket(AF_ZIGBEE, SOCK_DGRAM, ZBS_PROT_TRANSPORT)
# Different radios have different bindings
## end point, profile ID and cluster ID are zero when using the 802.15.4 radios
if series == '1':
    sd.bind(("",0,0,0)) #bindings for series 1 radios
    packetSize = 100
# end point is 0xE8 when using ZigBee radios
elif series == '2':
    sd.bind(("",0xe8,0,0)) #bindings for series 2 radios
    packetSize = 72
else:
    print "Unknown radio version, bindings and packet size may not be correct"
    sd.bind(("",0,0,0)) #bindings for unknown radios
    packetSize = 72

# Configure the socket for non-blocking operation:
sd.setblocking(0)

# Initialize state variables:
data = ""                        # holds the incoming data
buf = ""                        # holds collected data
response = ""                # parsed buffer
src_addr = ()
request = ""
tIndex = -1
bufferDict = {};				# declare address/buffer dictionary

while (time.clock()-startTime < stopTime or stopTime==0):
    
    # Reset the ready lists:
    rlist, wlist = ([], [])
    if len(response) == 0:
        # If the response buffer is empty, add socket to read list:
        rlist = [sd]
        wlist = []
    else:
        # Otherwise, add the socket to the write list:
        wlist = [sd]
        rlist = []
    
    # select (r,w,e) returns a tuple of the sockets that are actually readable, writeable or in error
    rlist, wlist, xlist = select(rlist,wlist,[])
    if sd in rlist:
        try:
        # Receive from the socket:
            # data, src_addr = sd.recvfrom(1)
            data, src_addr = sd.recvfrom(packetSize)
            #print "data: " + data + " / ascii: " + str(ord(data)) + " / buffer: " + buf
            #buf += data
            bufferDict[src_addr[0]] += data
            buf = bufferDict[src_addr[0]]
            tIndex = str.find(buf, TERMINATOR)
            #request = ""

            # If there's a request in this buffer, parse it
            if tIndex > -1:
                request = buf[:tIndex]
                
                print 'Source: ' + src_addr[0] + ' / endpoint: ' + str(src_addr[1]) + ' / profile ID: ' + str(src_addr[2]) + ' / cluster ID: ' + str(src_addr[3]) + ' / tIndex: ' + str(tIndex) + ' / Request: ' + request
                
                if request == 'help': # send the help file
                    response = helpFile
                    bufferDict[src_addr[0]] = ""
                    request = ""
                else:
                    f = urllib.urlopen(request) # get the URL
                    response = f.read() # parse the incoming data
                    print '\tGot '+ str(len(response)) + ' bytes'
                    bufferDict[src_addr[0]] = ""
                    request = ""
            elif data == QUIT_CODE:
                print "QUITTING"
                break;
            elif data == CLEAR_CODE:
                bufferDict[src_addr[0]] = ""
                request = ""
            elif data == "|":
                print bufferDict
            #else:
                # no terminator detected, so append 
                #bufferDict[src_addr[0]] += data
	
        except Exception, e:
            response = '*** request failed: ' + request + ' | ' + str(e) + '\n\r'
            bufferDict[src_addr[0]] = ""
            request = ""
            print '* request failed *'
            print e
    
    if sd in wlist:
        try:
            # Send to the socket:
            part = response[:packetSize] #packets can't be larger than 72 bytes
            count = sd.sendto(part, 0, src_addr)
            # Slice off count bytes from the buffer
            response = response[count:]
            time.sleep(SLEEP_DUR) # 0.01 WORKS FINE FOR 57600 BAUD but 0.5 is too slow for 9600 baud
        except Exception, e: #general exception handler
            print '* response failed *'
            print type(e)
            print e
            request = ""
            response = response[1:] # if a send fails, pare off the response and try again

print 'Exiting normally.'
