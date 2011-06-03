'''
Created on May 18, 2011

@author: Axel Roest
based on HTTPSession by jordanh
'''
import errno
# use our own urlparser which knows about the udp scheme, as the standard one doesn't, even though it's compliant
import library.urlparse2
import base64
import socket

from sessions.abstract import AbstractSession

# TODO: in a more perfect world, we would have a thread q to which we could
#       dispatch blocking operations to, such as the blocking connect which
#       occurs in this session.  The size of the thread q could be made
#       to be configurable and taylored to the target Digi ConnectPort target
#       environment.
# 
# May 2011, Adapted from HTTPSession by Axel Roest
#
# msg = "Whatever message goes here..."
# UDPSock.sendto(msg,addr)
# 
# Problem: urlparse doesn't understand the udp:// url (funny that)
# Solution: urlparse2
#
# Possible bugs (untested): what happens if a UDP packet is bigger than an XBee packet, of say 80 bytes

class UDPSession(AbstractSession):
    
    def __init__(self, xig_core, url, xbee_addr):
        
        self.__core = xig_core
        self.__write_buf = ""
        self.__read_buf = ""
        self.__xbee_addr = xbee_addr
        self.__max_buf_size = self.__core.getGlobalMaxBufSize() 
              
        # Parse URL:
        parsedUrl = urlparse2.urlsplit(url)
        
        # could be rewritten as self.__urlScheme = parsedUrl.scheme  etc.
        self.__urlScheme = parsedUrl[0]
        self.__urlNetLoc = parsedUrl[1]
        self.__urlPath = parsedUrl[2]
        if len(parsedUrl[3]):
            self.__urlPath += '?' + parsedUrl[3]
        if len(parsedUrl[4]):
            self.__urlPath += '#' + parsedUrl[4] 
        self.__urlUsername = None
        self.__urlPassword = ""
        
        if '@' in self.__urlNetLoc:
            self.__urlUsername, self.__urlNetLoc = self.__urlNetLoc.split('@')
            
        if self.__urlUsername is not None and ':' in self.__urlUsername:
            self.__urlUsername, self.__urlPassword = self.__urlUsername.split(':')
        
        print "starting UDP connection to [%s] %s" % ( self.__urlScheme, self.__urlNetLoc )
        # check for portnumber in url
        self.__urlPort = 0
        if ':' in self.__urlNetLoc:
            self.__urlNetLoc, portStr = self.__urlNetLoc.split(':')
            self.__urlPort = int(portStr)
        
        # Perform UDP connection:
        self.__connect()
                    
    def __connect(self):
        if self.__urlScheme == "udp":
            # TODO: connect timeout
            # addr = (host,port)        // tuple
            addr = self.__urlNetLoc, self.__urlPort
            self.__UDPSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
          
        bytesSent = 0

        try:
            # maybe we need to connect first (NO!), and close later?
            bytesSent = self.__UDPSocket.sendto(self.__urlPath, addr)

        except socket.gaierror, e:
            self.__do_error("unable to perform UDP request '%s'" % str(e))
            return
        except socket.error, e:
            self.__do_error("unable to perform UDP request '%s'" % str(e))
            return
            
        if bytesSent != len(self.__urlPath):
            print "UDP WARNING not all bytes sent: %d from %d" % (bytesSent, len(self.__urlPath))

 #       self.__UDPSocket.close()

            
    def __do_error(self, error_msg):
        self.__write_buf = "Xig-Error: " + error_msg + "\r\n"
        self.__UDPSocket.close()
    
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        """
        Attempt to handle an in-session command given by cmd_str from
        xbee_addr
        
        If cmd_str is valid, return True.  If the command is not valid
        (or incomplete), return False.
        """
        
        if cmd_str.startswith("udp://"):
            return UDPSession(xig_core, cmd_str, xbee_addr)
        
        return None
    
    def close(self):
        try:
            self.__UDPSocket.close()
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
        elif len(self.__read_buf) > self.__core.getGlobalMaxBufSize():
            sidx = len(self.__read_buf) - self.__core.getGlobalMaxBufSize()
            self.__read_buf = self.__read_buf[sidx:]
        
    def accountSessionToXBeeBuffer(self, count):
        self.__write_buf = self.__write_buf[count:]

    def read(self, sd):
        return 0
        
    def write(self, sd):
        return 0 # stub, this should never be called
