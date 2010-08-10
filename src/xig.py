# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
##

## Global String Constants
NAME = "XBee Internet Gateway (xig)"
SHORTNAME = "xig"
VERSION = "1.0.0"

## Global Configuration Constants
# The default URL for iDigi Management and Data Services:
IDIGI_URL = "en://developer.idigi.com"
# The maximum number of bytes outstanding the gateway will buffer,
# per session, in either direction:
MAX_SESSION_BUF_SIZE = 1024
# Global blocking operation timeout, including connect times
GLOBAL_TIMEOUT_SEC = 30

print 'Unzipping and loading modules...'

import sys, time, os

APP_ARCHIVE = "WEB/python/_xig.zip"
sys.path.insert(0, APP_ARCHIVE)

# additional standard library module imports
import urlparse, base64, errno, string, struct, random
import digi_httplib as httplib
from socket import *
from select import *


# Digi specific library module imports
import rci, xbee
print 'done.'

class XIGApp(object):
    """XBee Internet Gateway - "Take off every XIG." """
    
    HELPFILE_TEMPLATE = """\
$appName $appVersion @ IP: $ipAddr
------------------------------------------------------------------------------
by Rob Faludi <faludi.com>,
   Ted Hayes <log.liminastudio.com>,
   & Jordan Husney <jordan.husney.com>

COMMANDS:
 All commands are CR "\\r" or NL "\\n" delimited, except where noted.
 help or xig://help:   displays this file
 quit or xig://quit:   quits program
 abort or xig://abort: aborts the current request, clears the receive buffer

 http://<host/path> retrieves a URL
 https://<host/path> retrieves a secure URL 
 http://<user:pass@host/path> retrieves a URL using username and password
 https://<user:pass@host/path> retrieves a URL using username and password 

USE:
 The recommended speed is 115200 baud which can be set with ATBD7
 Lower baud rates may work if you are receiving short responses

 The following formats are NOT yet supported:

  ftp://<host/path>
  ftp://<username:password@host/path>  
  telnet://<host:port>
  mailto:<addr@host>
  
                                                                 xig help
"""
    XBEE_S1_MAX_PAYLOAD_BYTES = 100
    

    def __init__(self):
        self.sessions = {}              # sessions, keyed by xbee address
        self.xbee_rx_bufs = {}          # rx buffers, keyed by xbee address
        self.xbee_tx_bufs = {}          # tx buffers, "
        self.xbee_sd = None
        self.max_xbee_rx_size = 0
        
        self.xbee_sd = socket(AF_XBEE, SOCK_DGRAM, XBS_PROT_TRANSPORT)
        xbee_version = self.getXBeeVersion()
        xbee_series = xbee_version[0]
        print "XBee Version = %s, Series = %s" % (xbee_version, xbee_series)
        bind_addr = ('', 0, 0, 0)
        if xbee_series == '1':
            bind_addr = ('', 0, 0, 0)
            self.max_xbee_rx_size = self.XBEE_S1_MAX_PAYLOAD_BYTES
        elif xbee_series == '2' or xbee_series == '3':
            bind_addr = ('', 0xe8, 0, 0)
            self.max_xbee_rx_size = 72
        else:
            bind_addr = ('', 0xe8, 0, 0)
            self.max_xbee_rx_size = self.getXBeeMaxPayloadBytes()
        self.xbee_sd.bind(bind_addr)
        
        
    def getHelpfile(self):
        help_template = string.Template(XIGApp.HELPFILE_TEMPLATE)
        helpfile = help_template.substitute(appName=NAME, appVersion=VERSION,
                                        ipAddr=self.getLocalIP())
         
        return helpfile.replace('\n', '\r\n')

      
    def getLocalIP(self):
        """\
        Returns a string of the local gateways IP address.
        
        Uses the local Digi XML RCI ("Remote Command Interface") in order
        to perform the query.
        """
        
        query_string = """\
<rci_request version="1.1">
        <query_state><boot_stats/></query_state>
</rci_request>"""
        response = rci.process_request(query_string)
        ip_beg = response.find("<ip>")
        ip_end = response.find("</ip>")
        
        return response[ip_beg+4:ip_end].strip()

    
    def setiDigiConnection(self, server_url, reconnect_time=5):
        rci_request = """\
<rci_request version="1.1">
    <set_setting>
          <mgmtconnection index="1">
          <connectionType>client</connectionType>
            <connectionEnabled>on</connectionEnabled>
            <timedConnectionPeriod>%s</timedConnectionPeriod>
            <timedConnectionOffset>immediate</timedConnectionOffset>
            <lastKnownAddressUpdateEnabled>on</lastKnownAddressUpdateEnabled>
            <clientConnectionReconnectTimeout>60</clientConnectionReconnectTimeout>
            <pagedConnectionOverrideEnabled>off</pagedConnectionOverrideEnabled>
            <serverArray>
              <serverAddress>%s</serverAddress>
              <securitySettingsIndex>0</securitySettingsIndex>
            </serverArray>
          </mgmtconnection>
    </set_setting>
</rci_request>""" % (reconnect_time, server_url)

        rci.process_request(rci_request)

    def getXBeeVersion(self):
        return "%04X" % struct.unpack(">H", xbee.ddo_get_param(None, 'VR'))[0]
    
    def getXBeeMaxPayloadBytes(self):
        return struct.unpack(">H", xbee.ddo_get_param(None, 'NP'))[0]

    def __doXBeeRx(self, buf, addr):
        if addr not in self.xbee_rx_bufs:
            self.xbee_rx_bufs[addr] = ""

        buf = buf.replace('\r','\n')

        # manage the size of the XBee receive buffer
        if (len(self.xbee_rx_bufs[addr]) + len(buf)) > MAX_SESSION_BUF_SIZE:
            self.xbee_rx_bufs[addr] = self.xbee_rx_bufs[addr][len(buf):]
        self.xbee_rx_bufs[addr] += buf
        
        if '\n' not in self.xbee_rx_bufs[addr]:
            # no valid tokens yet
            return

        print "buf is %s" % repr(self.xbee_rx_bufs[addr])
        
        for tok in self.xbee_rx_bufs[addr].split('\n'):
            print "tok is %s" % repr(tok)
            self.xbee_rx_bufs[addr] = self.xbee_rx_bufs[addr][len(tok)+1:]
            if not len(tok):
                # empty command
                continue            
            if tok in ('help', 'xig://help'):
                self.__appendTx(self.getHelpfile(), addr)
            elif tok in ('quit', 'xig://quit'):
                self.__appendTx("NYI\r\n", addr)
            elif tok in ('abort', 'xig://abort'):
                self.__appendTx("NYI\r\n", addr)
            elif len(urlparse.urlsplit(tok)[0]):
                # URL scheme found:
                try:
                    new_session = SessionFactory.create(tok)
                except:
                    self.__appendTx("error: unable to handle url '%s'\r\n" % tok,
                                    addr)
                    continue
                if addr in self.sessions:
                    self.__appendTx("error: session already active\r\n", addr)
                    continue
                print "Created new session to '%s'" % tok
                new_session.setDataCb(
                    lambda buf, addr=addr: self.__sessionDataCb(buf, addr))
                new_session.setCompletionCb(
                    lambda addr=addr: self.__sessionCompletionCb(addr))
                new_session.connect()                
                self.sessions[addr] = new_session
                if addr not in self.xbee_tx_bufs:
                    self.xbee_tx_bufs[addr] = ""
            else:
                self.__appendTx("error: unknown command '%s'" % tok, addr)
                    
    
    def __doXBeeTx(self, addr):
        if addr not in self.xbee_tx_bufs:
            return
        sendbuf = self.xbee_tx_bufs[addr][0:self.max_xbee_rx_size]
        if len(sendbuf) == 0:
            return
        sent = self.xbee_sd.sendto(sendbuf, 0, addr)
        self.xbee_tx_bufs[addr] = self.xbee_tx_bufs[addr][sent:]

    def __sessionDataCb(self, buf, addr):
        if addr not in self.xbee_tx_bufs:
            self.xbee_tx_bufs[addr] = ""
        self.xbee_tx_bufs[addr] += buf
        
    def __appendTx(self, buf, addr):
        self.__sessionDataCb(buf, addr)
    
    def __sessionCompletionCb(self, addr):
        if addr in self.sessions:
            del(self.sessions[addr])
        # note: we don't delete the tx buffer because more data may need
        #       draining!

    def ioLoopOnce(self):
        rl, wl, xl = ([self.xbee_sd], [], [])
        
        # do we have anything to transmit?
        if len(filter(lambda k: len(self.xbee_tx_bufs[k]) > 0,
                      self.xbee_tx_bufs)) > 0:
            wl.append(self.xbee_sd)
        
#        print "I/O pre-select: %s" % repr((rl, wl, xl))
        rl, wl, xl = select(rl, wl, xl, 0.250)
#        print "I/O post-select: %s" % repr((rl, wl, xl))
        
        # read list processing:
        if self.xbee_sd in rl:
            buf, addr = self.xbee_sd.recvfrom(self.max_xbee_rx_size)
            self.__doXBeeRx(buf, addr)

        # write list processing:
        if self.xbee_sd in wl:
            # randomize session list order for queuing fairness:
            xbee_addrs = self.xbee_tx_bufs.keys()
            random.shuffle(xbee_addrs)
            try:
                for xbee_addr in xbee_addrs:
                    self.__doXBeeTx(xbee_addr)
            except error, why:
                if why[0] != errno.EWOULDBLOCK: 
                    raise error
        
        # perform Session I/O
        session_xbee_addrs = self.sessions.keys()
        random.shuffle(session_xbee_addrs)        
        for xbee_addr in session_xbee_addrs:
            read_amt = min(self.max_xbee_rx_size,
                           MAX_SESSION_BUF_SIZE - len(self.xbee_tx_bufs[xbee_addr]))
            if not read_amt:
                continue
            self.sessions[xbee_addr].ioLoopOnce(read_amt)
        

class AbstractSession(object):
    """\
    An abstract Internet session, used to facilitate the gatewaying of
    data between the Internet domain and an XBee node.
    """
    def __init__(self, url):
        self.data_cb = None
        self.completion_cb = None

    def connect(self):
        raise Exception, "not implemented"
    
    def close(self):
        raise Exception, "not implemented"

    def setDataCb(self, data_cb):
        self.data_cb = data_cb
        
    def setCompletionCb(self, completion_cb):
        self.completion_cb = completion_cb
    
    def ioLoopOnce(self, read_amt):
        raise Exception, "not implemented"


class HTTPSession(AbstractSession):
    def __init__(self, url, method="GET", request=""):
        AbstractSession(self).__init__(url)
        
        parsedUrl = urlparse.urlsplit(url)
        
        self.urlScheme = parsedUrl[0]
        self.urlNetLoc = parsedUrl[1]
        self.urlPath = parsedUrl[2] 
        self.urlUsername = None
        self.urlPassword = ""
        
        if '@' in self.urlNetLoc:
            self.urlUsername, self.urlNetLoc = self.urlNetLoc.split('@')
            
        if self.urlUsername is not None and ':' in self.urlUsername:
            self.urlUsername, self.urlPassword = self.urlUsername.split(':')

        self.httpConn = None
        self.httpMethod = method
        self.httpRequest = ""
        self.httpResponse = None
        
        self.buf = ""

    def connect(self):
        if self.urlScheme == "https":
            # TODO: connect timeout
            self.httpConn = httplib.HTTPSConnection(self.urlNetLoc)            
        else:
            # TODO: connect timeout
            self.httpConn = httplib.HTTPConnection(self.urlNetLoc)
            
        headers = { 'Accept': 'text/plain, text/html',
                    'User-Agent': '%s-%s' % (SHORTNAME, VERSION) }
        
        if self.urlUsername is not None:
            header['Authorization'] = "Basic %s" % (
                base64.encodestring(
                    "%s:%s" % (self.urlUsername, self.urlPassword))[:-1]) 

        try:
            self.httpConn.request(self.httpMethod, self.urlPath,
                                  self.httpRequest, headers)
        except gaierror:
            self.close()
            return
            
        self.httpResponse = self.httpConn.getresponse()
        if self.httpResponse.status != 200:
            print "BAD HTTP status = %d, reason = %s" % (
                self.httpResponse.status, self.httpResponse.reason)
            self.close()
            return
        # configure socket for non-blocking I/O operation:
        self.httpConn.sock.setblocking(0)
        
    def close(self):
        print "io session of %s closed" % repr(self.urlNetLoc)
        try:
            self.httpConn.close()
        except:
            pass
        if self.completion_cb is not None:
            self.completion_cb()
        
    def ioLoopOnce(self, read_amt):
        print "io session poll of %s max read %d" % (repr(self.urlNetLoc), read_amt)
        try:
            buf = self.httpResponse.read(read_amt)
        except error, why:
            if why[0] != errno.EWOULDBLOCK:
                self.completion_cb()
            else:
                pass
            
        if len(buf) == 0:
            self.close()
                
        if self.data_cb is not None and len(buf):
            self.data_cb(buf) 
        

class SessionFactory(object):
    """\
    Provides a static method create() used to create an appropriate Session
    object based upon provided URL.
    """
     
    @staticmethod
    def create(url):
        parsedUrl = urlparse.urlsplit(url)
        scheme = parsedUrl[0]
        if scheme == "http" or scheme == "https":
            return HTTPSession(url)
        else:
            raise ValueError, "unknown scheme '%s'" % scheme


def main():  
    random.seed(None)

    xig_app = XIGApp()
    xig_app.setiDigiConnection(server_url=IDIGI_URL)
    while 1:
        xig_app.ioLoopOnce()
    
    return 0

if __name__ == "__main__":
    ret = main()
    sys.exit(ret)
