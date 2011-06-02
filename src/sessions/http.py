"""
HTTP Session implementation.  Commmunicates with the World-Wide Web.
Handles all http:// and https:// prefixed commands.
"""

import errno
import urlparse
import base64
import socket

import library.digi_httplib as httplib

from abstract import AbstractSession

# TODO: in a more perfect world, we would have a thread q to which we could
#       dispatch blocking operations to, such as the blocking connect which
#       occurs in this session.  The size of the thread q could be made
#       to be configurable and taylored to the target Digi ConnectPort target
#       environment.

class HTTPSession(AbstractSession):
    STATE_INIT      = 0x0
    STATE_CONNECTED = 0x1
    STATE_DRAIN     = 0x2
    STATE_FINISHED  = 0x3
    
    def __init__(self, xig_core, url, xbee_addr):
        
        self.__core = xig_core
        self.__write_buf = ""
        self.__read_buf = ""
        self.__state = HTTPSession.STATE_INIT 
        self.__xbee_addr = xbee_addr
        self.__max_buf_size = self.__core.getGlobalMaxBufSize() 

        self.__httpConn = None
        self.__httpMethod = "GET"
        self.__httpRequest = ""
        self.__httpResponse = None
              
        # Parse URL:
        parsedUrl = urlparse.urlsplit(url)
        
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

        # Perform HTTP connection:
        try:
            self.__connect()
        except httplib.InvalidURL:
            self.__do_error("unable to perform HTTP request; invalid URL")

                    
    def __connect(self):
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
            header['Authorization'] = "Basic %s" % (
                base64.encodestring(
                    "%s:%s" % (self.__urlUsername, self.__urlPassword))[:-1]) 

        try:
            self.__httpConn.request(self.__httpMethod, self.__urlPath,
                                  self.__httpRequest, headers)
        except socket.gaierror, e:
            self.__do_error("unable to perform HTTP request '%s'" % str(e))
            return
        except socket.error, e:
            self.__do_error("unable to perform HTTP request '%s'" % str(e))
            return
            
        self.__httpResponse = self.__httpConn.getresponse()
        if self.__httpResponse.status != 200:
            print "HTTP WARNING status = %d, reason = %s" % (
                self.__httpResponse.status, self.__httpResponse.reason)
        
        if self.__httpConn.sock is None:
            # Since socket is closed, read on file object will not block:
            self.__write_buf += self.__httpResponse.read()
            self.__state = HTTPSession.STATE_DRAIN
            return
            
        # configure socket for non-blocking I/O operation:
        self.__httpConn.sock.setblocking(0)
        self.__state = HTTPSession.STATE_CONNECTED


    def __do_error(self, error_msg):
        self.__state = HTTPSession.STATE_DRAIN
        self.__write_buf = "Xig-Error: " + error_msg + "\r\n"
        
    
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        """
        Attempt to handle an in-session command given by cmd_str from
        xbee_addr
        
        If cmd_str is valid, return True.  If the command is not valid
        (or incomplete), return False.
        """
        
        if cmd_str.startswith("http://") or cmd_str.startswith("https://"):
            return HTTPSession(xig_core, cmd_str, xbee_addr)
        
        return None
    
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
        if (self.__state == HTTPSession.STATE_DRAIN and
            len(self.__write_buf) == 0):
            #print "HTTP STATE DRAIN -> FINISHED"
            self.__state = HTTPSession.STATE_FINISHED
        
    def read(self, sd):
        read_amt = self.__max_buf_size - len(self.__write_buf)
        if read_amt <= 0:
            return 0
        
        buf = ""
        try:
            buf = self.__httpResponse.read(read_amt)
        except socket.error, why:
            print "HTTP read error %s" % errno.errorcode[why[0]]
            if why[0] not in (errno.EWOULDBLOCK, errno.WSAEWOULDBLOCK):
                self.__state = HTTPSession.STATE_DRAIN
            else:
                return 0
        except httplib.IncompleteRead:
            print "HTTP Incomplete Read of HTTP 1.1 chunk"
            self.__state = HTTPSession.STATE_DRAIN
            self.close()
            
        if (len(buf) == 0 or self.__httpResponse.length == 0 or
            self.__httpResponse.isclosed()):
            self.__state = HTTPSession.STATE_DRAIN
        self.__write_buf += buf
        
        return len(buf)

    def write(self, sd):
        return 0 # stub, this should never be called