'''
Created on Sep 4, 2011

@author: jordanh

The XIG I/O kernel implements the I/O multiplexing and callbacks for the
entirety of the XIG system.  One may say it is the "heart" of the XIG.

'''
import sys
import errno
import random
import struct
from socket import *
from select import *
import exceptions

from xig_session_q import XigSessionQ
from xig_inactive_session_command_parser import XigInactiveSessionCommandParser
from xbee_xmit_stack import XBeeXmitStack

DIGI_PLATFORM_FLAG = True
if sys.platform.startswith('win'):
    from win_socketpair import SocketPair as socketpair

if DIGI_PLATFORM_FLAG:
    import xbee

class XigIOKernel(object):
    XBEE_S1_MAX_TX = 100
    XBEE_S1_MAX_RX = 100
    
    XBEE_S23_MAX_TX = 72
    XBEE_S23_MAX_RX = 84
    
    XBEE_MIN_TX = 48
    XBEE_MIN_RX = 100
    
    def __init__(self, xig_core):
        self.__core = xig_core
        self.__active_sessions = {}
        self.__queued_sessions = XigSessionQ(xig_core)
        self.__inactive_sess_cmd_parser = XigInactiveSessionCommandParser(xig_core)
        self.__iosample_subscribers = []
        self.__xig_sd = None
        self.__xig_sd_max_tx_sz = self.XBEE_MIN_TX
        self.__xig_sd_max_rx_sz = self.XBEE_MIN_RX
        self.__xbee_version = None

        
        if DIGI_PLATFORM_FLAG:
            self.__xbee_sd = socket(AF_XBEE, SOCK_DGRAM, XBS_PROT_TRANSPORT)
            self.__xbee_version = self.__getXBeeVersion()
            xbee_series = self.__xbee_version[0]
            print "XBee Version = %s, Series = %s" % (self.__xbee_version, xbee_series)
            bind_addr = ('', 0, 0, 0)
            if xbee_series == '1':
                bind_addr = ('', 0, 0, 0)
                self.__xig_sd_max_tx_sz = self.XBEE_S1_MAX_TX
                self.__xig_sd_max_rx_sz = self.XBEE_S1_MAX_RX
            elif xbee_series == '2' or xbee_series == '3':
                bind_addr = ('', 0xe8, 0, 0)
                try:
                    self.__xig_sd_max_tx_sz = struct.unpack(
                        "B", xbee.ddo_get_param(None, 'NP'))[0]
                except:
                    self.__xig_sd_max_tx_sz = self.XBEE_S23_MAX_TX
                source_routing_enabled = struct.unpack("B",
                    xbee.ddo_get_param(None, 'AR'))[0] != 0xff
                if source_routing_enabled:
                    self.__xig_sd_max_tx_sz -= 20
                self.__xig_sd_max_rx_sz = self.XBEE_S23_MAX_RX
            else:
                bind_addr = ('', 0xe8, 0, 0)
                self.__xig_sd_max_tx_sz = self.XBEE_MIN_TX
                self.__xig_sd_max_rx_sz = self.XBEE_MIN_RX
                
            try:
                self.__xbee_sd.bind(bind_addr)
            except Exception, e:
                print "XIG-ERROR: unable to bind XIG to XBee (%s)" % repr(e)
                print "XIG-ERROR: is another program running using the XBee?"
                raise(e)
            
            # Enable XBee TX_STATUS reporting:
            if self.__core.isXBeeXmitStatusSupported():
                print "XBee reliable transmit enabled"
                self.__xbee_sd.setsockopt(XBS_SOL_EP, XBS_SO_EP_TX_STATUS, 1)
            else:
                print "XBee transmit status not supported on this device."
        else:
            print "Using PC-based UDP simulation mode on port %d..." % (
              self.__core.getConfig().xbee_sim_udp_port)
            self.__xbee_sd = socket(AF_INET, SOCK_DGRAM)
            self.__xig_sd_max_tx_sz = self.XBEE_MIN_TX
            self.__xig_sd_max_rx_sz = self.XBEE_MIN_RX
            self.__xbee_sd.bind(('', self.__core.getConfig().xbee_sim_udp_port))

        print "XBee MTU = %d bytes" % (self.__xig_sd_max_tx_sz)
        print "XBee MRU = %d bytes" % (self.__xig_sd_max_rx_sz)
        # Put XBee socket into non-blocking mode:
        self.__xbee_sd.setblocking(0)

        # Setup internal socket which can be used for unblocking the
        # internal event loop asynchronously:
        self.__outer_sd, self.__inner_sd = socketpair()
        for sd in [ self.__outer_sd, self.__inner_sd ]:
            sd.setblocking(0)
        
        # Initialize XBeeXmitStack instance:
        self.__xbee_xmit_stack = XBeeXmitStack(self.__core, self.__xbee_sd)


    def __getXBeeVersion(self):
        return "%04X" % struct.unpack(">H", xbee.ddo_get_param(None, 'VR'))[0]
    
    def __homogenizeXBeeSocketAddr(self, xbee_socket_addr):
        return xbee_socket_addr[0:4] + (0,0)
    
    def xbeeAddrFromHwAddr(self, hw_addr,
                               ep=None, profile=None, cluster=None):
        xbee_series = self.__xbee_version[0]
        if xbee_series == 1:
            return (hw_addr, ep or 0, profile or 0, cluster or 0, 0, 0)
        else:
            return (hw_addr, ep or 0xe8, profile or 0xc105, cluster or 0x11, 0, 0)

    def enqueueSession(self, session):
        """\
            Adds a new session object to the XIG core for processing
            within the XIG core ioLoop().
            
            The session object must be a valid object derived from
            AbstractSession.
        """
        self.__queued_sessions.add(session)
        # unblock inner I/O loop
        self.__outer_sd.send('a')

    def ioSubscriberAdd(self, func):
        if func not in self.__iosample_subscribers:
            self.__iosample_subscribers.append(func)
            
    def ioSubscriberRemove(self, func):
        self.__iosample_subscribers.remove(func)

    def __ioSampleHook(self, buf, addr):
        """\
            Checks if packet is an XBee IO Sample, publishes packet
            to callback subscribers.  Returns Boolean.
            
            If the given packet was an I/O packet, returns True.
            Else, returns False.
        """
        
        # Matches Series 2 and Series 1 I/O packets, respectively:
        if (addr[2:4] != (0xc105, 0x92) and
            addr[2:4] != (0x0, 0x92)):
            return False
        
        if DIGI_PLATFORM_FLAG:
            # Take care to strip off XBee option bits:
            addr = addr[0:4] + (0,0)
        
        for func in self.__iosample_subscribers:
            try:
                func(buf, addr)
            except Exception, e:
                print "IOSAMPLE: exception calling callback function"
                
        return True
    
                    
    def ioLoop(self, timeout=0):
        new_xcommands = []

        # Find all sessions waiting for active processing for each
        # unique destination:
        for dest in self.__queued_sessions.waiting_destinations():
            if dest in self.__active_sessions:
                continue
            self.__active_sessions[dest] = (
                self.__queued_sessions.dequeue_session(dest))
        
        # Evaluate each active session:
        rl, wl, xl = ([self.__xbee_sd, self.__inner_sd], [], []) 
        sd_to_sess_map = {}
        pending_data_to_xbee_sessions = []
        for addr in self.__active_sessions.keys():
            sess = self.__active_sessions[addr]
            # If the session finished, reap it:
            if sess.isFinished():
                del(self.__active_sessions[addr])
                continue
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
        
        # Select active descriptors
        rl, wl, xl = select(rl, wl, xl, timeout)
        
        # Drain any characters from our internal unblocking mechanism:
        if self.__inner_sd in rl:
            rl.remove(self.__inner_sd)
            try:
                self.__inner_sd.recv(1)
            except:
                pass
        
        # XBee read processing
        if self.__xbee_sd in rl:
            rl.remove(self.__xbee_sd)
            buf, addr = self.__xbee_sd.recvfrom(self.__xig_sd_max_rx_sz)
            was_tx_status = self.__xbee_xmit_stack.tx_status_recv(buf, addr)
            addr = self.__homogenizeXBeeSocketAddr(addr)
            #print "RECV: %d bytes from %s" % (len(buf), repr(addr[0:4]))
            print "RECV: %d bytes from %s (%s)" % (len(buf), repr(addr), repr(buf))
            if was_tx_status or self.__ioSampleHook(buf, addr):
                pass
            elif addr in self.__active_sessions:
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
                buf = sess.getSessionToXBeeBuffer()[0:self.__xig_sd_max_tx_sz]
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
                for session_class in self.__core.getSessionClasses():
                    if DIGI_PLATFORM_FLAG:
                        # Take care to strip off XBee option bits:
                        addr = self.__homogenizeXBeeSocketAddr(addr)
                    sess = session_class.handleSessionCommand(
                                self.__core, xcommand.command, addr)
                    if sess is not None:
                        # valid command handler found, enqueue session for
                        # later processing:
                        self.__queued_sessions.add(sess)
                        break

    def shutdown(self):
        del(self.__xbee_sd)
        