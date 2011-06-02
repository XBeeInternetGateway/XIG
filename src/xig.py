'''
Created on Sep 17, 2010

@author: jordanh
'''

## Global String Constants
NAME = "XBee Internet Gateway (XIG)"
SHORTNAME = "xig"
VERSION = "1.2.0"

## Global Configuration Constants
# Global blocking operation timeout, including connect times
GLOBAL_TIMEOUT_SEC = 30
# Global maximum buffer size:
GLOBAL_MAX_BUF_SIZE = 256
# UDP port when script is executed on a PC:
XBEE_SIM_UDP_PORT = 5649

# TODO: change select loop processing to include all read sockets in
#       the select loop rather than performing a linear poll.

print "%s v%s starting." % (NAME, VERSION)
print 'Unzipping and loading modules...'

import sys, time, os

APP_ARCHIVE = "WEB/python/_xig.zip"
sys.path.insert(0, APP_ARCHIVE)

# additional standard library module imports
import struct, errno, string, random, shlex, time
from copy import copy
from socket import *
from select import *

# Digi specific library module imports
DIGI_PLATFORM_FLAG = False
if sys.platform.startswith('digi'):
    DIGI_PLATFORM_FLAG = True
    import rci, xbee
    
# XIG Library imports
import sessions
print 'done.'

HELPFILE_TEMPLATE = """\
$appName $appVersion @ IP: $ipAddr
------------------------------------------------------------------------------
by Rob Faludi (http://faludi.com),   
   Jordan Husney (http://jordan.husney.com),
   & Ted Hayes (http://log.liminastudio.com),

COMMANDS:
 All commands are CR "\\r" or NL "\\n" delimited, except where noted.
 help or xig://help:   displays this file
 quit or xig://quit:   quits program
 abort or xig://abort: aborts the current session
 time or xig://time:   prints the time in ISO format

 http://<host/path> retrieves a URL
 https://<host/path> retrieves a secure URL 
 http://<user:pass@host/path> retrieves a URL using username and password
 https://<user:pass@host/path> retrieves a URL using username and password 

NOTES:
 
 The following formats are NOT yet supported:

  ftp://<host/path>
  ftp://<username:password@host/path>  
  telnet://<host:port> / tcp://host:port
  mailto:<addr@host>
  
"""

class Xig(object):
    def __init__(self):
        self.helpfile = (string.Template(HELPFILE_TEMPLATE)
                           .substitute(appName=NAME, appVersion=VERSION,
                                        ipAddr=self.getLocalIP()))
        self.helpfile = self.helpfile.replace('\n', '\r\n')
        self.__quit_flag = False
        self.__io_kernel = XigIOKernel(xig_core=self)

    def quit(self):
        self.__quit_flag = True

    def getLocalIP(self):
        if not sys.platform.startswith('digi'):
            return gethostbyname_ex('')[2]

        # Assume Digi platform:
        query_string = """\
<rci_request version="1.1">
        <query_state><boot_stats/></query_state>
</rci_request>"""
        response = rci.process_request(query_string)
        ip_beg = response.find("<ip>")
        ip_end = response.find("</ip>")
        
        return response[ip_beg+4:ip_end].strip()            

    def getShortName(self):
        return SHORTNAME
    
    def getVersion(self):
        return VERSION

    def getGlobalTimeout(self):
        return GLOBAL_TIMEOUT_SEC
    
    def getGlobalMaxBufSize(self):
        return GLOBAL_MAX_BUF_SIZE
                    
    def go(self):
        print "XIG startup complete, ready to serve requests."
        while not self.__quit_flag:
            self.__io_kernel.ioLoop(timeout=None)
            #time.sleep(1)
        # run one last time, with feeling:
        self.__io_kernel.ioLoop(timeout=5.0)
        self.__io_kernel.shutdown()
        return 0
            
class XigInactiveSessionCommandParser(object):
    def __init__(self):
        self.__addr_cmd_buf_map = {}

    class XigInactiveSessionCommand(object):
        def __init__(self, command, addr):
            self.command = command
            self.addr = addr
        
    def parse(self, buf, addr):
        if addr not in self.__addr_cmd_buf_map:
            self.__addr_cmd_buf_map[addr] = ""
        cmd_buf = self.__addr_cmd_buf_map[addr] + buf

        if len(cmd_buf) > GLOBAL_MAX_BUF_SIZE:
            sidx = len(cmd_buf) - GLOBAL_MAX_BUF_SIZE
            cmd_buf = cmd_buf[sidx:]
            
        # normalize line-endings in buffer:
        cmd_buf = cmd_buf.replace("\r","\n").replace("\n\n","\n")
        
        # if no complete commands, return
        if '\n' not in cmd_buf:
            self.__addr_cmd_buf_map[addr] = cmd_buf
            return []
        
        # return all complete commands:
        eidx = cmd_buf.rfind('\n')
        try:
            cmds = shlex.split(cmd_buf[0:eidx])
        except:
            # whoa! bad command buffer!
            print "XISC error parsing command buffer, flushing."
            self.__addr_cmd_buf_map[addr] = ""
            return []
        cmd_buf = cmd_buf[eidx:]
        cmds = map(lambda c: self.XigInactiveSessionCommand(c, addr), cmds)
        self.__addr_cmd_buf_map[addr] = cmd_buf
        return cmds

        
class XBeeXmitStack(object):
    
    DEFAULT_RETRIES = 3             # total retries before failing a transmit
    MAX_OUTSTANDING = 1             # total outstanding xmits for single stn
    MAX_TOTAL_OUTSTANDING = 3       # maximum total outstanding xmits

    class XmitRequest(object):
        STATE_QUEUED = 0
        STATE_OUTSTANDING = 1
        
        def __init__(self, buf, flags, addr, xmit_id):
            self.retries_remaining = XBeeXmitStack.DEFAULT_RETRIES
            self.buf = buf
            self.flags = flags
            self.addr = addr[0:5] + (xmit_id,)
            self.xmit_id = xmit_id
            self.state = XBeeXmitStack.XmitRequest.STATE_QUEUED          
    
    class XmitTable(object):
        def __init__(self):
            self.__table = {}

        def queue(self, xmit_req):
            if type(xmit_req) is not XBeeXmitStack.XmitRequest:
                raise TypeError, "xmit_req must be XBeeXmitStack.XmitRequest object"
            
            if xmit_req.addr[0] not in self.__table:
                self.__table[xmit_req.addr[0]] = []
            self.__table[xmit_req.addr[0]].append(xmit_req)
            
        def generate_tx_queue(self):
            dest_list = self.__table.keys()
            random.shuffle(dest_list)
            # Copy table, carefully controlling references:
            # (we are only copying references to the list objects here)
            table_copy = {}
            for dest in dest_list:
                table_copy[dest] = copy(self.__table[dest])
                
            while len(dest_list) != 0:
                for dest in copy(dest_list):
                    xmit_req = table_copy[dest].pop(0)
                    if (xmit_req.state ==
                        XBeeXmitStack.XmitRequest.STATE_OUTSTANDING):
                        # this destination has no more packets to send
                        dest_list.remove(dest)
                        continue
                    if len(table_copy[dest]) == 0:
                        dest_list.remove(dest)
                    yield xmit_req

        def num_entries_for_addr(self, addr):
            try:
                return len(self.__table[addr[0]])
            except KeyError:
                return 0

        def num_entries(self):
            return sum(map(lambda k: len(self.__table[k]),
                           self.__table.keys()))
            
        def find_xmit_req(self, xmit_id):
            for k in self.__table.keys():
                q = filter(lambda xr: xr.xmit_id == xmit_id,
                           self.__table[k])
                if len(q):
                    return q[0]
            return None
        
        def expunge(self, xmit_id):
            xmit_req = self.find_xmit_req(xmit_id)
            hw_addr = xmit_req.addr[0]
            self.__table[hw_addr].remove(xmit_req)
            if len(self.__table[hw_addr]) == 0:
                del(self.__table[hw_addr])

    class TooManyOutstandingRequests(Exception):
        pass
            
    def __init__(self, xig_core, xbee_sd):
        self.__xbee_sd = xbee_sd
        self.__xmit_id_set = set(range(1,256))        
        self.__xmit_table = XBeeXmitStack.XmitTable()
        
        if not DIGI_PLATFORM_FLAG:
            self.tx_status_recv = self._sim_tx_status_recv
            self.sendto = self._sim_sendto
            self.xmit = self._sim_xmit
        
    def sendto(self, buf, flags, addr):
        # See if we can take a new request:
        if (self.__xmit_table.num_entries_for_addr(addr) >= 
                XBeeXmitStack.MAX_OUTSTANDING or
                    self.__xmit_table.num_entries() >= 
                        XBeeXmitStack.MAX_TOTAL_OUTSTANDING):
            # No, raise exception
            # print "XMIT too many entries (%d)" % self.__xmit_table.num_entries()
            raise XBeeXmitStack.TooManyOutstandingRequests
        
        # Create new request
        self.__xmit_table.queue(
            XBeeXmitStack.XmitRequest(buf, flags, addr, self.__xmit_id_set.pop()))
        return len(buf) 
        
    def xmit(self):
        for xmit_req in self.__xmit_table.generate_tx_queue():
            # print "XMIT write len %d to XBee" % len(xmit_req.buf)
            # Take care to strip off any transmit option bits:
            # print "XMIT dest addr %s" % repr(xmit_req.addr)
            print "XMIT SEND: to %s (id = %d)" % (repr(xmit_req.addr[0:4]), xmit_req.addr[5])
            count = self.__xbee_sd.sendto(xmit_req.buf, xmit_req.flags, xmit_req.addr)
            # print "XMIT wrote len %d to XBee" % count
            xmit_req.state = XBeeXmitStack.XmitRequest.STATE_OUTSTANDING
            
    def tx_status_recv(self, buf, addr):
        """\
        Process a TX status frame.

        Performs internal accounting.
        """

        tx_status = 0
        cluster_id = addr[3]
        xmit_id = addr[5]
        xmit_req = self.__xmit_table.find_xmit_req(xmit_id)
        
        if xmit_req is None:
            return
     
    
        if xmit_id < 1:
            print "XMIT FAIL: frame is not TX Status frame!"
    
        if cluster_id == 0x89:
            # X-API transmit status frame:
            print "XMIT INFO: X-API TX Status (id = %d)" % xmit_id
            tx_status = ord(buf[2])
        elif cluster_id == 0x8b:
            # X-API ZigBee transmit status frame:
            print "XMIT INFO: X-API ZigBee TX Status (id = %d)" % xmit_id
            tx_status = ord(buf[5])
        elif cluster_id == 0:
            # XBee driver status indication:
            print "XMIT INFO: XBee driver status indication (id = %d)" % xmit_id
            tx_status = struct.unpack("i", buf)[0]
        else:
            raise ValueError, (
                "XMIT FAIL: unknown status indication frame format (id = %d)" % (
                    xmit_id)) 
    
        if tx_status == 0:
            # Transmission successful!
            # Return xmit id to set:
            print "XMIT GOOD: tx_status (id = %d)" % xmit_id
            self.__xmit_id_set.add(xmit_id)
            self.__xmit_table.expunge(xmit_id)
            return
        
        # Bad TX status!
        xmit_req.retries_remaining -= 1
        if xmit_req.retries_remaining <= 0:
            print "XMIT FAIL: xmit to %s FAILED permanently with tx_status = 0x%08x (%d)" % (
                addr[0], tx_status, tx_status) 
            self.__xmit_id_set.add(xmit_id)
            self.__xmit_table.expunge(xmit_id)
            return
        
        # Mark TX for retry:
        print "XMIT FAIL: to %s FAILED with tx status = 0x%02x, will retry." % (
            addr[0], tx_status)            
        xmit_req.state = XBeeXmitStack.XmitRequest.STATE_QUEUED
        
    # The below methods are used when the XIG is simulated on a PC,
    # these methods get re-bound in __init__ if a non-ConnectPort environment
    # is detected:
    def _sim_tx_status_recv(self, buf, addr):
        print "XBeeXmitStack._sim_tx_status_recv()"
    def _sim_sendto(self, buf, flags, addr):
        print "XBeeXmitStack._sim_sendto()"
        return self.__xbee_sd.sendto(buf, flags, addr)
    def _sim_xmit(self):
        print "XBeeXmitStack._sim_xmit()"

class XigIOKernel(object):
    XBEE_S1_MAX_PAYLOAD = 100
    XBEE_S23_MAX_PAYLOAD = 72
    XBEE_MIN_PAYLOAD = 48
    
    def __init__(self, xig_core):
        self.__core = xig_core
        self.__session_classes = (
          sessions.HTTPSession,                                  
          sessions.XigSession,    # must be last, it handles unknown commands
          )
        self.__active_sessions = {}
        self.__inactive_sess_cmd_parser = XigInactiveSessionCommandParser()
        self.__xig_sd = None
        self.__xig_sd_max_io_sz = self.XBEE_MIN_PAYLOAD
        
        if DIGI_PLATFORM_FLAG:
            self.__xbee_sd = socket(AF_XBEE, SOCK_DGRAM, XBS_PROT_TRANSPORT)
            xbee_version = self.__getXBeeVersion()
            xbee_series = xbee_version[0]
            print "XBee Version = %s, Series = %s" % (xbee_version, xbee_series)
            bind_addr = ('', 0, 0, 0)
            if xbee_series == '1':
                bind_addr = ('', 0, 0, 0)
                self.__xig_sd_max_io_sz = self.XBEE_S1_MAX_PAYLOAD
            elif xbee_series == '2' or xbee_series == '3':
                bind_addr = ('', 0xe8, 0, 0)
                try:
                    self.__xig_sd_max_io_sz = struct.unpack(
                        "B", xbee.ddo_get_param(None, 'NP'))[0]
                except:
                    self.__xig_sd_max_io_sz = self.XBEE_S23_MAX_PAYLOAD
                source_routing_enabled = struct.unpack("B",
                    xbee.ddo_get_param(None, 'AR'))[0] != 0xff
                if source_routing_enabled:
                    self.__xig_sd_max_io_sz -= 20
            else:
                bind_addr = ('', 0xe8, 0, 0)
                self.__xig_sd_max_io_sz = self.XBEE_MIN_PAYLOAD
            self.__xbee_sd.bind(bind_addr)
            
            # Enable XBee TX_STATUS reporting:
            self.__xbee_sd.setsockopt(XBS_SOL_EP, XBS_SO_EP_TX_STATUS, 1)
        else:
            print "Using PC-based UDP simulation mode on port %d..." % (
              XBEE_SIM_UDP_PORT)
            self.__xbee_sd = socket(AF_INET, SOCK_DGRAM)
            self.__xig_sd_max_io_sz = self.XBEE_MIN_PAYLOAD
            self.__xbee_sd.bind(('', XBEE_SIM_UDP_PORT))

        print "XBee MTU = %d bytes" % (self.__xig_sd_max_io_sz)
        # Put XBee socket into non-blocking mode:
        self.__xbee_sd.setblocking(0)
        
        # Initialize XBeeXmitStack instance:
        self.__xbee_xmit_stack = XBeeXmitStack(self, self.__xbee_sd)


    def __getXBeeVersion(self):
        return "%04X" % struct.unpack(">H", xbee.ddo_get_param(None, 'VR'))[0]

            
    def ioLoop(self, timeout=0):
        new_xcommands = []
        
        rl, wl, xl = ([self.__xbee_sd], [], []) 
        sd_to_sess_map = {}
        pending_data_to_xbee_sessions = []
        # Evaluate each active session:
        #print "IO Active sessions: %s" % repr(self.__active_sessions) 
        for addr in copy(self.__active_sessions):
            sess = self.__active_sessions[addr]
            # If the session finished, reap it:
            if sess.isFinished():
                del(self.__active_sessions[addr])
            # Extract all sockets for reading and writing:
            new_rl, new_wl = (sess.getReadSockets(), sess.getWriteSockets())
            try:
                if len(sess.getSessionToXBeeBuffer()) > 0:
                    pending_data_to_xbee_sessions.append(sess)
            except:
                pass
            # Build reverse session map:
            for sd in (new_rl + new_wl):
                sd_to_sess_map[sd] = sess
            rl.extend(new_rl)
            wl.extend(new_wl)
        # If any session has data for the XBee socket, add the XBee socket
        # to the select write list:
        if len(pending_data_to_xbee_sessions):
            wl.append(self.__xbee_sd)
        
        #print "IO XBee SD: %s" % repr(self.__xbee_sd)
        #print "IO BEFORE rl %s" % repr(rl)

        # Select active descriptors
        rl, wl, xl = select(rl, wl, xl, timeout)
        #print "IO AFTER rl %s" % repr(rl)
        
        # XBee read processing
        if self.__xbee_sd in rl:
            rl.remove(self.__xbee_sd)
            buf, addr = self.__xbee_sd.recvfrom(self.__xig_sd_max_io_sz)
            self.__xbee_xmit_stack.tx_status_recv(buf, addr)
            print "RECV: %d bytes from %s" % (len(buf), repr(addr[0:4]))
            if addr in self.__active_sessions:
                # data is destined to session
                self.__active_sessions[addr].appendXBeeToSessionBuffer(buf)
            else:
                # data is command data:
                new_xcommands = self.__inactive_sess_cmd_parser.parse(buf, addr)

                
        # Session read processing
        random.shuffle(rl)
        for sd in rl:
            sess = sd_to_sess_map[sd]
            sess.read(sd)
            
        # XBee write processing
        if self.__xbee_sd in wl:
            wl.remove(self.__xbee_sd)
            random.shuffle(pending_data_to_xbee_sessions)
            # Try a single write from all active sessions until we'd block:
            for sess in pending_data_to_xbee_sessions:
                buf = sess.getSessionToXBeeBuffer()[0:self.__xig_sd_max_io_sz]
                try:
                    count = self.__xbee_xmit_stack.sendto(buf, 0, sess.getXBeeAddr())
                    sess.accountSessionToXBeeBuffer(count)
                except XBeeXmitStack.TooManyOutstandingRequests:
                    pass
                
                try:
                    self.__xbee_xmit_stack.xmit()
                except error, why:
                    # TODO: handle gracefully
                    if why[0] != errno.EWOULDBLOCK:
                        print "IO sendto exception %s" % repr(why) 
                        #raise error
                    break                

        # Session write processing:
        random.shuffle(wl)
        for sd in wl:
            sess = sd_to_sess_map[sd]
            sess.write(sd)
            
        # Command processing:
        if len(new_xcommands):
            for xcommand in new_xcommands:
                for session_class in self.__session_classes:
#                    print "Trying: '%s' on '%s'" % (xcommand.command, session_class.__name__)
                    if DIGI_PLATFORM_FLAG:
                        # Take care to strip off XBee option bits:
                        addr = addr[0:4] + (0,0)
                    sess = session_class.handleSessionCommand(
                                self.__core, xcommand.command, addr)
                    if sess is not None:
                        # valid command handler found, new session started
                        self.__active_sessions[xcommand.addr] = sess
                        break

    def shutdown(self):
        del(self.__xbee_sd)

        
def main():
    # take off every Xig!
    xig = Xig()
    ret = xig.go()
    sys.exit(ret)

    
if __name__ == "__main__":
    ret = main()
    sys.exit(ret)

