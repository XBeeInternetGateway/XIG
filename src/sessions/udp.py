'''
Created on May 18, 2011

@author: Axel Roest
based on HTTPSession by jordanh

Modified by jordanh on August 30, 2011 to fit into XIG v1.3.0
architecture.  Sessions are now continuous until they terminate
with xig://abort command.
'''
import socket
import logging

from sessions.abstract import AbstractSession

logger = logging.getLogger("xig.udp")
logger.setLevel(logging.INFO)

# use our own urlparser which knows about the udp scheme
import library.xig_urlparse as urlparse
from library.command_parser import Command, StreamingCommandParser


class UDPSession(AbstractSession):
    STATE_INIT           = 0x0
    STATE_WRITING        = 0x1
    STATE_WRITESCLOSED   = 0x2
    STATE_DRAINTOXBEE    = 0x3
    STATE_FINISHED       = 0x4
    
    def __init__(self, xig_core, url, xbee_addr):
        self.__core = xig_core
        self.__toxbee_buf = ""
        self.__fromxbee_buf = ""
        self.__xbee_addr = xbee_addr
        self.__state = UDPSession.STATE_INIT
        self.__max_buf_size = self.__core.getConfig().global_max_buf_size 
        self.__command_parser = StreamingCommandParser()
              
        # Parse URL:
        parsedUrl = urlparse.urlsplit(url)
        self.__urlScheme = parsedUrl[0]
        self.__urlNetLoc = parsedUrl[1]
        
        logger.info("session to %s" % (self.__urlNetLoc))
        
        # check for portnumber in url
        if ':' not in self.__urlNetLoc:
            self.__do_error("UDP URL requires port number (e.g. udp://host:port)")
            return
        self.__urlNetLoc, portStr = self.__urlNetLoc.split(':')
        try:
            self.__urlPort = int(portStr)
        except ValueError:
            self.__do_error("UDP port number must be integer")
            return

        # Create command handlers:
        self.__command_parser.register_command(Command("xig://abort\r",
                                                self.__commandAbortHandler))
        self.__command_parser.register_command(Command("xig://abort\n",
                                                self.__commandAbortHandler))
        
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
        self.close(no_msg_override=True)
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
    
    def close(self, no_msg_override=False):
        try:
            self.__UDPSocket.close()
        except:
            pass
        if not no_msg_override:
            self.__toxbee_buf = "Xig: connection aborted\r\n"
        self.__state = UDPSession.STATE_DRAINTOXBEE
        
    def isFinished(self):
        # Check states, transisition as necessary until finished:
        if self.__state == UDPSession.STATE_WRITESCLOSED:
            if not len(self.__fromxbee_buf):
                self.__state = UDPSession.STATE_DRAINTOXBEE
        
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
            self.__state in (UDPSession.STATE_WRITING,
                             UDPSession.STATE_WRITESCLOSED)):
            return ([self.__UDPSocket])
        return []
    
    def getSessionToXBeeBuffer(self):
        return self.__toxbee_buf
    
    def getXBeeToSessionBuffer(self):
        return self.__fromxbee_buf

    def appendSessionToXBeeBuffer(self, buf):
        self.__toxbee_buf += buf
    
    def appendXBeeToSessionBuffer(self, buf):
        if self.__state not in (UDPSession.STATE_INIT,
                                UDPSession.STATE_WRITING):
            return
        self.__fromxbee_buf += self.__command_parser.parse(buf)
        if len(self.__fromxbee_buf) > self.__max_buf_size:
            sidx = len(self.__fromxbee_buf) - self.__max_buf_size
            self.__fromxbee_buf = self.__fromxbee_buf[sidx:]
        
    def accountSessionToXBeeBuffer(self, count):
        self.__toxbee_buf = self.__toxbee_buf[count:]

    def read(self, sd):
        return 0 # stub, this should never be called
        
    def write(self, sd):     
        if self.__state not in (UDPSession.STATE_WRITING,
                                UDPSession.STATE_WRITESCLOSED):
            return 0
        
        write_amt = self.__max_buf_size - len(self.__fromxbee_buf)
        if write_amt <= 0:
            return 0
        
        try:
            wrote = self.__UDPSocket.sendto(
                        self.__fromxbee_buf[:write_amt], 0,
                        (self.__urlNetLoc, self.__urlPort))
            self.__fromxbee_buf = self.__fromxbee_buf[wrote:]
            logger.info("XMIT of %d bytes" % (wrote))
        except Exception, e:
            self.__do_error('unexpected UDP socket error "%s"' % (str(e)))
            return 0
                
        return wrote
    
    def __commandAbortHandler(self):
        self.__state = UDPSession.STATE_WRITESCLOSED
        self.__toxbee_buf = "Xig: connection aborted\r\n"

