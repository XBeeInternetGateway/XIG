NAME = 'XBee Internet Gateway (xig)'
VERSION = '1.00a26'

print NAME + ' v' + VERSION
print 'unzipping and loading modules...'
import sys, time
from socket import *
from select import *

sys.path.append('WEB/python/url_libs.zip')
sys.path.append('WEB/python/email.zip')

import urllib

stopTime = 0

############ NEXT STEPS ############
""""
show current ip in help file

log transaction to file system
get UTC time for logs
write log header to file


"""
####################################

helpFile = '\n\r---------------------------\n\r'+ NAME + ' v' + VERSION + """
\r  by Rob Faludi faludi.com\r
\r
COMMANDS:\r
 help: displays this file\r
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

print 'initializing URL calls...'
urllib.urlopen('http://www.google.com')


if len(sys.argv) > 1: # if there's an argument we use it for the stop time
    stopTime = int(sys.argv[1])
else:
    stopTime = 0 # otherwise we keep running for 5 minutes
print 'stopping after %d seconds' % (stopTime,)
startTime = time.clock()

## create a socket using the ZigBee address family, datagram mode and a proprietary transport
sd = socket(AF_ZIGBEE, SOCK_DGRAM, ZBS_PROT_TRANSPORT)
# bind to end point zero
# end point, profile ID and cluster ID are zero when using the 802.15.4 radios
sd.bind(("",0xe8,0,0))

# Configure the socket for non-blocking operation: 
sd.setblocking(0)

# Initialize state variables: 
response = "" 
src_addr = ()

while (time.clock()-startTime < stopTime or stopTime==0):
    
    # Reset the ready lists: 
    rlist, wlist = ([], []) 
    if len(response) == 0: 
        # If the response buffer is empty, 
        # add socket to read list: 
        rlist = [sd]
        wlist = []
    else: 
        # Otherwise, add the socket to the 
        # write list: 
        wlist = [sd]
        rlist = []
        
    # select (r,w,e) returns a tupple of the sockets that are actually readable, writeable or in error
    rlist, wlist, xlist = select(rlist,wlist,[])
    if sd in rlist:
        try:
            # Receive from the socket: 
            request, src_addr = sd.recvfrom(72)
            print 'Source: ' + src_addr[0] +' Requests: ' + request
            if request == 'help' or request == '?': # send the help file
                response = helpFile
            else:
                f = urllib.urlopen(request) # get the URL
                response = f.read() # parse the incoming data
                print '\tgot '+ str(len(response)) + ' bytes'
        except Exception, e:
            response = '** request failed: ' + request + '\n\r\t' + str(e) + '\n\r'
            print '* request failed *'
            print e
    if sd in wlist:
        try:
            # Send to the socket:
            part = response[:72] #packets can't be larger than 72 bytes
            count = sd.sendto(part, 0, src_addr)
            # Slice off count bytes from the buffer
            response = response[count:]
            time.sleep(0.00) # 0.01 WORKS FINE FOR 57600 BAUD but 0.5 is too slow for 9600 baud
        except Exception, e: #general exception handler
            print '* response failed *'
            print type(e)
            print e
            response = response[1:] # if a send fails, pare off the response and try again
print 'stop time reached'
print 'exiting normally'