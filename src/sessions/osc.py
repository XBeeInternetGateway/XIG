'''
Created on May 31, 2011

@author: Axel Roest
based on HTTPSession by jordanh
'''

import errno
# use our own urlparser which knows about the osc scheme
import library.xig_urlparse as urlparse
import base64
import socket
import library.OSCClient
import logging

logger = logging.getLogger("xig.osc")
logger.setLevel(logging.INFO)

from sessions.abstract import AbstractSession

# version 0.1, only 1 OSC server, not multiple servers
# version 0.2, multiple OSC servers, using targets.txt file
# 
# May 2011, Adapted from UDPSession by Axel Roest
#
# addr = (host,port)        // tuple
# UDPSock = socket(AF_INET,SOCK_DGRAM)


# msg = "Whatever message goes here..."
# OSCSock.sendto(msg,addr)
# 
# Current bug: OSCClient checks for reuse of the same host and switches the port to a new port on the address tuple:

class OSCSession(AbstractSession):
    
    def __init__(self, xig_core, url, xbee_addr):
        
        self.__core = xig_core
        self.__write_buf = ""
        self.__read_buf = ""
        self.__xbee_addr = xbee_addr
        self.__max_buf_size = self.__core.getConfig().global_max_buf_size 

        # Read configuration from configuration file:
        self.__targets = self.getTargetsFromConfig()

        # self.__oscclient = OSCClient.OSCClient()
        self.__multiclient = OSCClient.OSCMultiClient()
        
        # Parse URL:
        parsedUrl = urlparse.urlsplit(url)
        
        # could be rewritten as self.__urlScheme = parsedUrl.scheme  etc.
        self.__urlScheme = parsedUrl[0]
        self.__urlNetLoc = parsedUrl[1]
        self.__urlPath = parsedUrl[2]
        if len(parsedUrl[3]):
            # paramString = parsedUrl[3]
            self.__urlParameters = parsedUrl[3].split('&')
        else:
            self.__urlParameters = []

        if len(self.__urlNetLoc) :
            self.__urlPort = 0
            if ':' in self.__urlNetLoc:
                self.__urlNetLoc, portStr = self.__urlNetLoc.split(':')
                self.__urlPort = int(portStr)
            self.__multiclient.setOSCTarget( (self.__urlNetLoc,self.__urlPort) )        # use this host target if supplied
        else:
            # self.__oscclient.connect(self.__target)
            for target in self.__targets:
                self.__multiclient.setOSCTarget( target )
        
        logger.info("starting OSC connection to [%s] %s | %s | %s'" % (self.__urlScheme,self.__urlNetLoc,self.__urlPath, self.__urlParameters))

        self.__connect()
                    
    def __connect(self):
        myMessage = OSCClient.OSCMessage()
        if self.__urlScheme == "osc":
            # TODO: connect timeout
            # addr = (host,port)        // tuple
            # split different kind of messages (x, reset)
            # Perform OSC connection:
            myMessage = OSCClient.OSCMessage()
            myMessage.setAddress(self.__urlPath)
            if len(self.__urlParameters) :
                for param in self.__urlParameters :
                    myMessage.append(int(param),'i')
                    # for now only ints are allowed, until we find a way to update the URI scheme
        
            # print myMessage
            # hexDump(myMessage.getBinary())

        try:
            # self.__oscclient.send(myMessage)
            # timeout of zero means non blocking, no timeout means blocking (!) timeout in (float) seconds
            self.__multiclient.send(myMessage,1)

        except socket.gaierror, e:
            self.__do_error("unable to perform OSC request '%s'" % str(e))
            return
        except socket.error, e:
            self.__do_error("unable to perform OSC request '%s'" % str(e))
            return
        self.__multiclient.close()          # necessary?
            
    def __do_error(self, error_msg):
        self.__write_buf = "Xig-Error: " + error_msg + "\r\n"
        self.__multiclient.close()          # necessary?
    
    def getTargetsfromFile(self, filename):        
        input_targets = getattr(self.__core.getConfig(), "osc_targets", None)
        targets = []
        for input_target in input_targets:
            addr, portStr = input_target.split(':')
            addr = addr.replace(' ', '')
            port = int(portStr.replace(' ', ''))
            targets.append( (addr, port) )

        return targets
        
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        """
        Attempt to handle an in-session command given by cmd_str from
        xbee_addr
        
        If cmd_str is valid, return True.  If the command is not valid
        (or incomplete), return False.
        """
        
        if cmd_str.startswith("osc://"):
            return OSCSession(xig_core, cmd_str, xbee_addr)
        
        return None

    @staticmethod
    def commandHelpText():
        return """\
 osc://host:port: initiate UDP session to remote server and port number
"""

    
    def close(self):
        try:
            self.__multiclient.close()
        except:
            pass
        self.__write_buf = "Xig: connection aborted\r\n"
        
    
    def isFinished(self):
        return True
    
    def getXBeeAddr(self):
        return self.__xbee_addr
    
    def getReadSockets(self):
        return []
    
    def getWriteSockets(self):
        return []
    
    def getSessionToXBeeBuffer(self):
        return self.__write_buf
    
    def getXBeeToSessionBuffer(self):
        return "" # stub to complete interface

    def appendSessionToXBeeBuffer(self, buf):
        self.__write_buf += buf # stub, not used
    
    def appendXBeeToSessionBuffer(self, buf):
        self.__read_buf += buf
        self.__read_buf = self.__read_buf.replace("\r", "\n")
        self.__read_buf = self.__read_buf.replace("\n\n", "\n")
        if self.__read_buf.find("abort\n") > -1:
            self.close()
            self.__read_buf = ""
        elif len(self.__read_buf) > self.__max_buf_size:
            sidx = len(self.__read_buf) - self.__max_buf_size
            self.__read_buf = self.__read_buf[sidx:]
        
    def accountSessionToXBeeBuffer(self, count):
        self.__write_buf = self.__write_buf[count:]

    def read(self, sd):
        return 0
        
    def write(self, sd):
        return 0 # stub, this should never be called
