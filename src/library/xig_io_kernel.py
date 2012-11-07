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
import socket
import select

from library.addr import IP_Addr_Tuple, XBee_Addr_Tuple, XBee_Addr
from xig_session_q import XigSessionQ
from xig_inactive_session_command_parser import XigInactiveSessionCommandParser
from xbee_xmit_stack import XBeeXmitStack

import logging
logger = logging.getLogger("xig.io_kernel")

import xbee

class XigIOKernel(object):
    # 802.15.4
    XBEE_S1_MAX_TX = 100
    XBEE_S1_MAX_RX = 100
    
    # ZigBee
    XBEE_S234_MAX_TX = 72
    XBEE_S234_MAX_RX = 84
    
    # DigiMesh
    XBEE_S8_MAX_TX = 256
    XBEE_S8_MAX_RX = 256
    
    # Unknown
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
        self.__xbee_version = None

        # set up XBee socket to receive commands on        
        self.__xbee_sd = socket.socket(socket.AF_XBEE, socket.SOCK_DGRAM, socket.XBS_PROT_TRANSPORT)
        self.__xbee_version = self.__getXBeeVersion() #FIXME: this doesn't work in a lot of cases.
        xbee_series = self.__xbee_version[0]
        logger.info("XBee Version = %s, Series = %s" % (self.__xbee_version, xbee_series))
        bind_addr = ('', 0, 0, 0)
        if xbee_series == '1':
            bind_addr = ('', 0, 0, 0)
            self.__xig_sd_max_tx_sz = self.XBEE_S1_MAX_TX
        elif xbee_series == '2' or xbee_series == '3' or xbee_series == '4':
            bind_addr = ('', 0xe8, 0, 0)
            try:
                self.__xig_sd_max_tx_sz = struct.unpack(
                    "B", xbee.ddo_get_param(None, 'NP'))[0]
            except:
                self.__xig_sd_max_tx_sz = self.XBEE_S234_MAX_TX
            source_routing_enabled = struct.unpack("B",
                xbee.ddo_get_param(None, 'AR'))[0] != 0xff
            if source_routing_enabled:
                self.__xig_sd_max_tx_sz -= 20
        elif xbee_series == '8':
            bind_addr = ('', 0xe8, 0, 0)
            self.__xig_sd_max_tx_sz = self.XBEE_S8_MAX_TX
        else:
            bind_addr = ('', 0xe8, 0, 0)
            self.__xig_sd_max_tx_sz = self.XBEE_MIN_TX
            
        try:
            self.__xbee_sd.bind(bind_addr)
        except Exception, e:
            logger.error("Unable to bind XIG to XBee (%s). Is another program running using the XBee?" % repr(e))
            raise(e)
        
        # Enable XBee TX_STATUS reporting:
        if self.__core.isXBeeXmitStatusSupported():
            logger.debug("XBee reliable transmit enabled")
            self.__xbee_sd.setsockopt(socket.XBS_SOL_EP, socket.XBS_SO_EP_TX_STATUS, 1)
        else:
            logger.debug("XBee transmit status not supported on this device.")
            
        #add socket to process commands from UDP port on 
        self.__udp_sd = None
        try:
            xbee_udp_port = self.__core.getConfig().xbee_udp_port
            if xbee_udp_port:
                logger.info("Enabling UDP listener on port %d..." % (xbee_udp_port))
                self.__udp_sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.__udp_sd.bind(('', xbee_udp_port))
        except Exception, e:
            logger.warning("Exception when configuring UDP listener: %s" % (repr(e)))

        logger.debug("XBee MTU = %d bytes" % (self.__xig_sd_max_tx_sz))
        # Put XBee socket into non-blocking mode:
        self.__xbee_sd.setblocking(0)

        # Setup internal socket which can be used for unblocking the
        # internal event loop asynchronously:
        self.__outer_sd, self.__inner_sd = socket.socketpair()
        for sd in [ self.__outer_sd, self.__inner_sd ]:
            sd.setblocking(0)
        
        # Initialize XBeeXmitStack instance:
        self.__xbee_xmit_stack = XBeeXmitStack(self.__core, self.__xbee_sd)


    def __getXBeeVersion(self):
        # Some DigiMesh radios return 4 bytes--with only the last two being significant.
        # Here we slice the VR parameter to only read the last two bytes.
        return "%04X" % struct.unpack(">H", xbee.ddo_get_param(None, 'VR')[-2:])[0]
    
    def __homogenizeXBeeSocketAddr(self, xbee_socket_addr):
        return XBee_Addr_Tuple(xbee_socket_addr, options=0, transmission_id=0)

    def xbeeAddrTupleFromHwAddr(self, hw_addr, **kwargs):
        xbee_series = self.__xbee_version[0]
        if xbee_series == 1:
            return XBee_Addr_Tuple(address=hw_addr, **kwargs)
        else:
            return XBee_Addr_Tuple((hw_addr, 0xE8, 0xC105, 0x0011), **kwargs)

    def xbeeAddrFromHwAddr(self, hw_addr, **kwargs):
        return XBee_Addr(address=hw_addr, **kwargs)

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
        
        # Matches Series 2 and Series 1 I/O packets:
        if (addr[2:4] not in ((0xc105, 0x92), (0x0, 0x92), (0x0, 0x93))):
            return False
        
        #Take care to strip off XBee option bits 
        # TODO: why, these could be potentially useful.
        addr = self.__homogenizeXBeeSocketAddr(addr)
        
        for func in self.__iosample_subscribers:
            try:
                func(buf, addr)
            except Exception, e:
                logger.error("Exception calling callback function: %s" % repr(e))
        return True
    
                    
    def ioLoop(self, timeout=0):
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
        pending_data_to_udp_sessions = []
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
                    if isinstance(sess.getXBeeAddr(), XBee_Addr_Tuple):
                        # this is for the XBee
                        pending_data_to_xbee_sessions.append(sess)
                    else:
                        # this is for the UDP socket
                        pending_data_to_udp_sessions.append(sess)
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
        
        # If UDP socket is defined add to read list.  
        # Also add to write list if any session has data for the UDP socket
        if self.__udp_sd:
            rl.append(self.__udp_sd)
            if len(pending_data_to_udp_sessions):
                wl.append(self.__udp_sd)
        
        # Select active descriptors
        rl, wl, xl = select.select(rl, wl, xl, timeout)
        
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
            buf, addr = self.__xbee_sd.recvfrom(4096) #bigger than any possible XBee message size
            addr = XBee_Addr_Tuple(addr)
            was_tx_status = self.__xbee_xmit_stack.tx_status_recv(buf, addr)
            addr = self.__homogenizeXBeeSocketAddr(addr)
            if not was_tx_status:
                # don't print the bytes for TX status messages
                logger.debug("RECV: %d bytes from %s (%s)" % (len(buf), repr(addr), repr(buf)))
            if was_tx_status or self.__ioSampleHook(buf, addr):
                pass
            elif addr in self.__active_sessions:
                # data is destined to session
                self.__active_sessions[addr].appendXBeeToSessionBuffer(buf)
            else:
                # data is command data:
                for xcommand in self.__inactive_sess_cmd_parser.parse(buf, addr):
                    for session_class in self.__core.getSessionClasses():
                        sess = session_class.handleSessionCommand(self.__core, xcommand.command, addr)
                        if sess is not None:
                            # valid command handler found, enqueue session for
                            # later processing:
                            self.__queued_sessions.add(sess)
                            break
        
        # UDP read processing
        if self.__udp_sd in rl:
            rl.remove(self.__udp_sd)
            buf, addr = self.__udp_sd.recvfrom(1024) #large number
            addr = IP_Addr_Tuple(addr)
            logger.debug("UDPRECV: %d bytes from %s (%s)" % (len(buf), repr(addr), repr(buf)))
            if addr in self.__active_sessions:
                # data is destined to session
                self.__active_sessions[addr].appendXBeeToSessionBuffer(buf)
            else:
                # data is command data:
                for xcommand in self.__inactive_sess_cmd_parser.parse(buf, addr):
                    for session_class in self.__core.getSessionClasses():
                        sess = session_class.handleSessionCommand(self.__core, xcommand.command, addr)
                        if sess is not None:
                            # valid command handler found, enqueue session for
                            # later processing:
                            self.__queued_sessions.add(sess)
                            break
                
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
                buf = sess.getSessionToXBeeBuffer()[:self.__xig_sd_max_tx_sz]
                try:
                    count = self.__xbee_xmit_stack.sendto(buf, 0, sess.getXBeeAddr())
                    sess.accountSessionToXBeeBuffer(count)
                except XBeeXmitStack.TooManyOutstandingRequests:
                    pass
                
                try:
                    self.__xbee_xmit_stack.xmit()
                except Exception, why:
                    # TODO: handle gracefully
                    if why[0] != errno.EWOULDBLOCK:
                        logger.error("IO: exception on XBee xmit (%s)" % repr(why)) 
                        #raise error
                    break

        # UDP write processing
        if self.__udp_sd in wl:
            wl.remove(self.__udp_sd)
            random.shuffle(pending_data_to_udp_sessions)
            # Try a single write from all active sessions until we'd block:
            for sess in pending_data_to_udp_sessions:
                buf = sess.getSessionToXBeeBuffer()[:512] #512 should be a safe size for UDP transmission
                try:
                    # send directly to UDP device
                    addr = sess.getXBeeAddr()
                    count = self.__udp_sd.sendto(buf, 0, addr)
                    sess.accountSessionToXBeeBuffer(count)
                except Exception, e:
                    logger.error("exception when responding to UDP request (%s)" % repr(e))

        # Session write processing:
        random.shuffle(wl)
        for sd in wl:
            sess = sd_to_sess_map[sd]
            sess.write(sd)
            
    def shutdown(self):
        # make sure to close the socket (this is needed when running on a PC).
        if self.__xbee_sd:
            self.__xbee_sd.close()
        if self.__udp_sd:
            self.__udp_sd.close()
    
    def __del__(self):
        self.shutdown()
