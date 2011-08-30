'''
Created on May 18, 2011

@author: Axel Roest
based on HTTPSession by jordanh

Modified by jordanh on August 30, 2011 to fit into XIG v1.3.0
architecture.  Sessions are now continuous until they terminate
with xig://abort command.
'''
# use our own urlparser which knows about the udp scheme
import library.xig_urlparse as urlparse
import socket

from sessions.abstract import AbstractSession


class UDPSession(AbstractSession):
    STATE_INIT           = 0x0
    STATE_WRITING        = 0x1
    STATE_DRAINTOXBEE    = 0x2
    STATE_FINISHED       = 0x3
    
    def __init__(self, xig_core, url, xbee_addr):
        self.__core = xig_core
        self.__toxbee_buf = ""
        self.__fromxbee_buf = ""
        self.__xbee_addr = xbee_addr
        self.__state = UDPSession.STATE_INIT
        self.__max_buf_size = self.__core.getGlobalMaxBufSize() 
              
        # Parse URL:
        parsedUrl = urlparse.urlsplit(url)
        self.__urlScheme = parsedUrl[0]
        self.__urlNetLoc = parsedUrl[1]
        
        print "UDP: session to %s" % (self.__urlNetLoc)
        
        # check for portnumber in url
        self.__urlPort = 0
        if ':' in self.__urlNetLoc:
            self.__urlNetLoc, portStr = self.__urlNetLoc.split(':')
            self.__urlPort = int(portStr)
        
        # Perform UDP connection:
        self.__create_socket()
                    
    def __create_socket(self):
        addr = self.__urlNetLoc, self.__urlPort
        try:
            self.__UDPSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except:
            self.__do_error("unable to create UDP socket")
        self.__state = UDPSession.STATE_WRITING
            
    def __do_error(self, error_msg):
        self.__toxbee_buf = "Xig-Error: " + error_msg + "\r\n"
        self.close()
        self.__state = UDPSession.STATE_DRAINTOXBEE
    
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

    @staticmethod
    def commandHelpText():
        return """\
 udp://host:port: initiate UDP session to remote server and port number
                  (note: session will end only by using xig://abort)
"""
    
    def close(self):
        try:
            self.__UDPSocket.close()
        except:
            pass
        self.__toxbee_buf = "Xig: connection aborted\r\n"
        self.__state = UDPSession.STATE_DRAINTOXBEE
        
    def isFinished(self):
        # Take this opportunity to see if we should transistion to the
        # finished state:
        if self.__state == UDPSession.STATE_DRAINTOXBEE:
            if not len(self.__toxbee_buf):
                self.__state = UDPSession.STATE_FINISHED
                
        if self.__state == UDPSession.STATE_FINISHED:
            return True
        
        return False
    
    def getXBeeAddr(self):
        return self.__xbee_addr
    
    def getReadSockets(self):
        return []
    
    def getWriteSockets(self):
        if (len(self.__fromxbee_buf) and
            self.__state == UDPSession.STATE_WRITING):
            return ([self.__UDPSocket])
        return []
    
    def getSessionToXBeeBuffer(self):
        return self.__toxbee_buf
    
    def getXBeeToSessionBuffer(self):
        return self.__fromxbee_buf

    def appendSessionToXBeeBuffer(self, buf):
        self.__toxbee_buf += buf
    
    def appendXBeeToSessionBuffer(self, buf):
        self.__fromxbee_buf += buf
        
        if (self.__fromxbee_buf.find("xig://abort\n") > -1 or
            self.__fromxbee_buf.find("xig://abort\r") > -1):
            self.__fromxbee_buf = ""
            self.close()
            return
        
        if len(self.__fromxbee_buf) > self.__core.getGlobalMaxBufSize():
            sidx = len(self.__fromxbee_buf) - self.__core.getGlobalMaxBufSize()
            self.__fromxbee_buf = self.__fromxbee_buf[sidx:]
        
    def accountSessionToXBeeBuffer(self, count):
        self.__toxbee_buf = self.__toxbee_buf[count:]

    def read(self, sd):
        return 0 # stub, this should never be called
        
    def write(self, sd):     
        if self.__state != UDPSession.STATE_WRITING:
            return 0
        
        write_amt = self.__max_buf_size - len(self.__fromxbee_buf)
        if write_amt <= 0:
            return 0
        
        try:
            wrote = self.__UDPSocket.sendto(
                        self.__fromxbee_buf[:write_amt], 0,
                        (self.__urlNetLoc, self.__urlPort))
            self.__fromxbee_buf = self.__fromxbee_buf[wrote:]
        except Exception, e:
            self.__do_error('unexpected UDP socket error "%s"') % (str(e))
                
        return wrote
