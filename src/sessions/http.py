"""
HTTP Session implementation.  Commmunicates with the World-Wide Web.
Handles all http:// and https:// prefixed commands.
"""

import sys
import errno
import urlparse
import base64
import socket
import logging

import library.digi_httplib as httplib
from library.command_parser import Command, StreamingCommandParser

logger = logging.getLogger('xig.http')

from abstract import AbstractSession

# TODO: in a more perfect world, we would have a thread q to which we could
#       dispatch blocking operations to, such as the blocking connect which
#       occurs in this session.  The size of the thread q could be made
#       to be configurable and tailored to the target Digi ConnectPort target
#       environment.

class HTTPSession(AbstractSession):
    STATE_INIT      = 0x0
    STATE_CONNECTED = 0x1
    STATE_DRAIN     = 0x2
    STATE_FINISHED  = 0x3
    
    def __init__(self, xig_core, url, xbee_addr, ignore_response=False):
        
        self.__core = xig_core
        self.__write_buf = ""
        self.__read_buf = ""
        self.__state = HTTPSession.STATE_INIT 
        self.__xbee_addr = xbee_addr
        self.__max_buf_size = self.__core.getConfig().global_max_buf_size
        self.__command_parser = StreamingCommandParser() 

        self.__httpConn = None
        self.__httpMethod = "GET"
        self.__httpRequest = ""
        self.__httpResponse = None
        # Must use different constants for different platforms:
        if sys.platform.startswith("digi"):
            self.__eWouldBlockExcs = (errno.EWOULDBLOCK,)
        elif sys.platform.startswith("win"):
            self.__eWouldBlockExcs = (errno.EWOULDBLOCK, errno.WSAEWOULDBLOCK)
        else:
            # Sanity, a la Linux & Mac OSX
            self.__eWouldBlockExcs = (errno.EWOULDBLOCK, errno.EAGAIN)
              
        # Parse URL:
        self.__urlUsername = None
        self.__urlPassword = ""
        self.parse_url(url)
        
        # Perform HTTP connection:
        try:
            self.__connect(ignore_response)
        except httplib.InvalidURL:
            self.__do_error("unable to perform HTTP request; invalid URL")
            
        # Setup command parser:
        self.__command_parser.register_command(Command("abort\r",
                                                self.__commandAbortHandler))
        self.__command_parser.register_command(Command("abort\n",
                                                self.__commandAbortHandler))
        self.__command_parser.register_command(Command("xig://abort\r",
                                                self.__commandAbortHandler))
        self.__command_parser.register_command(Command("xig://abort\n",
                                                self.__commandAbortHandler))

    def parse_url(self, url):
        # Parse URL:
        parsedUrl = urlparse.urlsplit(url)
        
        self.__url = url
        self.__urlScheme = parsedUrl[0]
        self.__urlNetLoc = parsedUrl[1]
        self.__urlPath = parsedUrl[2]
        if len(parsedUrl[3]):
            self.__urlPath += '?' + parsedUrl[3]
        if len(parsedUrl[4]):
            self.__urlPath += '#' + parsedUrl[4] 
        
        if '@' in self.__urlNetLoc:
            self.__urlUsername, self.__urlNetLoc = self.__urlNetLoc.split('@')
            
        if self.__urlUsername is not None and ':' in self.__urlUsername:
            self.__urlUsername, self.__urlPassword = self.__urlUsername.split(':')

                    
    def __connect(self, ignore_response=False):
        if self.__urlScheme == "https":
            # TODO: connect timeout
            self.__httpConn = httplib.HTTPSConnection(self.__urlNetLoc)            
        else:
            # TODO: connect timeout
            self.__httpConn = httplib.HTTPConnection(self.__urlNetLoc)
            
        headers = { 'Accept': 'text/plain, text/html',
                    'User-Agent': '%s-%s' % (self.__core.getShortName(),
                                             self.__core.getVersion()) }
        
        if self.__urlUsername is not None:
            headers['Authorization'] = "Basic %s" % (
                base64.encodestring(
                    "%s:%s" % (self.__urlUsername, self.__urlPassword))[:-1]) 

        try:
            self.__httpConn.request(self.__httpMethod, self.__urlPath,
                                  self.__httpRequest, headers)
            logger.info("successful %s of %s" % (self.__httpMethod,
                                                 self.__url))
        except socket.gaierror, e:
            if not ignore_response:
                self.__do_error("unable to perform HTTP request '%s'" % str(e))
            else:
                self.__state = HTTPSession.STATE_FINISHED
            return
        except socket.error, e:
            if not ignore_response:
                self.__do_error("unable to perform HTTP request '%s'" % str(e))
            else:
                self.__state = HTTPSession.STATE_FINISHED
            return
        
        if ignore_response:
            self.close()
            self.__state = HTTPSession.STATE_FINISHED
            return
        
        try:    
            self.__httpResponse = self.__httpConn.getresponse()
        except socket.error, e:
            self.__do_error("error while parsing HTTP response: %s" % repr(str(e)))
            return
        except Exception, e:
            self.__do_error("httplib exception: %s" % repr(str(e)))
            return           
        
        if self.__httpResponse.status in (300, 301, 302, 303):
            # redirect
            location = self.__httpResponse.msg.get('location').strip()
            if location:
                logger.info("redirect to %s" % (location))
                self.parse_url(location)
                self.__connect(ignore_response)
        
        if self.__httpResponse.status != 200:
            logger.warning("status = %d, reason = %s" % (
                self.__httpResponse.status, self.__httpResponse.reason))
        
        if self.__httpConn.sock is None:
            # Since socket is closed, read on file object will not block:
            self.__write_buf += self.__httpResponse.read()
            if len(self.__write_buf) == 0:
                self.__state = HTTPSession.STATE_FINISHED
            else:
                self.__state = HTTPSession.STATE_DRAIN
            return

        # configure socket for non-blocking I/O operation:
        self.__httpConn.sock.setblocking(0)
        self.__state = HTTPSession.STATE_CONNECTED
                
        if self.__httpResponse.length == 0:
            self.__do_error("0 length response from server")
            return


    def __do_error(self, error_msg):
        self.__state = HTTPSession.STATE_DRAIN
        self.__write_buf = "Xig-Error: " + error_msg + "\r\n"
        
    
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        """
        Attempt to handle an in-session command given by cmd_str from
        xbee_addr
        """
        
        if cmd_str.startswith("http://") or cmd_str.startswith("https://"):
            return HTTPSession(xig_core, cmd_str, xbee_addr)
        
        return None
  
    @staticmethod
    def commandHelpText():
        return """\
 http://host/path: retrieves a URL
 https://host/path: retrieves a secure URL 
 http://user:pass@host/path: retrieves a URL using username and password
 https://user:pass@host/path: retrieves a URL using username and password
"""
    
    def close(self):
        try:
            self.__httpRequest.close()
        except:
            pass
        if self.__httpConn.sock is not None:
            try:
                self.__httpConn.close()
            except:
                pass
        self.__write_buf = "Xig: connection aborted\r\n"
        self.__state = HTTPSession.STATE_DRAIN
        
    
    def isFinished(self):
        return self.__state == HTTPSession.STATE_FINISHED
    
    def getXBeeAddr(self):
        return self.__xbee_addr
    
    def getReadSockets(self):
        if self.__state == HTTPSession.STATE_CONNECTED:
            return [self.__httpConn.sock]
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
        self.__read_buf += self.__command_parser.parse(buf)
        if len(self.__read_buf) > self.__max_buf_size:
            sidx = len(self.__read_buf) - self.__max_buf_size
            self.__read_buf = self.__read_buf[sidx:]

    def accountSessionToXBeeBuffer(self, count):
        self.__write_buf = self.__write_buf[count:]
        if (self.__state == HTTPSession.STATE_DRAIN and
            len(self.__write_buf) == 0):
            self.__state = HTTPSession.STATE_FINISHED
        
    def read(self, sd):
        read_amt = self.__max_buf_size - len(self.__write_buf)
        if read_amt <= 0:
            return 0
        buf = ""
        try:
            buf = self.__httpResponse.read(read_amt)
        except socket.error, why:
            if why[0] not in self.__eWouldBlockExcs:
                logger.error("read error %s" % errno.errorcode[why[0]])
                self.__state = HTTPSession.STATE_DRAIN
                self.close()
            else:
                return 0
        except httplib.IncompleteRead:
            logger.error("incomplete read of HTTP 1.1 chunk")
            self.__state = HTTPSession.STATE_DRAIN
            self.close()
            
        if (len(buf) == 0 or 
            self.__httpResponse.isclosed() or
            self.__httpResponse.length == 0):
            logger.info("connection closed by remote server")
            self.__state = HTTPSession.STATE_DRAIN
        
        self.__write_buf += buf
        return len(buf)

    def write(self, sd):
        return 0 # stub, this should never be called
    
    def __commandAbortHandler(self):
        self.close()
        self.__read_buf = ""