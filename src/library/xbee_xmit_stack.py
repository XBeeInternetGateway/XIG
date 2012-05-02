'''
Created on Sep 4, 2011

@author: jordanh

The XBee XMit (transmit) Stack queues and manages application-level
retries on noisy or lossy XBee networks.  Transmit retries are
facilitated by a little known (and little documented) ConnectPort
socket option feature XBS_SO_EP_TX_STATUS where TX_STATUS messages
may be lined up with a transmit request id.  See the below
implementation for details.

'''

import random
import struct
from copy import copy
from library.addr import XBee_Addr_Tuple

import logging
logger = logging.getLogger("xig.xmit")

DISABLE_XMIT_STACK = False

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
            # Set the address given all info we've got plus transmit id:
            self.addr = XBee_Addr_Tuple(addr, options=0, transmission_id = xmit_id)
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
        self.__core = xig_core
        self.__xbee_sd = xbee_sd
        self.__xmit_id_set = set(range(1,256))        
        self.__xmit_table = XBeeXmitStack.XmitTable()
        
    def sendto(self, buf, flags, addr):
        # See if we can take a new request:
        if (self.__xmit_table.num_entries_for_addr(addr) >= 
                XBeeXmitStack.MAX_OUTSTANDING or
                    self.__xmit_table.num_entries() >= 
                        XBeeXmitStack.MAX_TOTAL_OUTSTANDING):
            # No, raise exception
            raise XBeeXmitStack.TooManyOutstandingRequests
        
        # Create new request
        self.__xmit_table.queue(
            XBeeXmitStack.XmitRequest(buf, flags, addr, self.__xmit_id_set.pop()))
        return len(buf) 
        
    def xmit(self):
        for xmit_req in self.__xmit_table.generate_tx_queue():
            # Take care to strip off any transmit option bits:
            logger.debug("SEND: to %s (id = %d)" % (repr(xmit_req.addr[0:4]), xmit_req.addr.transmission_id))
            self.__xbee_sd.sendto(xmit_req.buf, xmit_req.flags, xmit_req.addr)
            xmit_req.state = XBeeXmitStack.XmitRequest.STATE_OUTSTANDING
            if not self.__core.isXBeeXmitStatusSupported():
                # mark transmit as successful:
                self.__xmit_id_set.add(xmit_req.addr.transmission_id)
                self.__xmit_table.expunge(xmit_req.addr.transmission_id)
            
    def tx_status_recv(self, buf, addr):
        """\
        Process a TX status frame.

        Performs internal accounting.  Returns True of a valid TX status
        frame was handled, False otherwise.
        """

        if (len(addr) != 6):
            return False

        tx_status = 0
        
        xmit_id = addr.transmission_id
        xmit_req = self.__xmit_table.find_xmit_req(xmit_id)
        
        if xmit_req is None:
            return False

        if addr.cluster_id == 0x89:
            # X-API transmit status frame:
            logger.info("X-API TX Status (id = %d)" % xmit_id)
            tx_status = ord(buf[2])
        elif addr.cluster_id == 0x8b:
            # X-API ZigBee transmit status frame:
            logger.info("X-API ZigBee TX Status (id = %d)" % xmit_id)
            tx_status = ord(buf[5])
        elif addr.cluster_id == 0:
            # XBee driver status indication:
            logger.info("XBee driver status indication (id = %d)" % xmit_id)
            tx_status = struct.unpack("i", buf)[0]
        else:
            raise ValueError, (
                "XMIT FAIL: unknown status indication frame format (id = %d)" % (
                    xmit_id)) 
    
        if tx_status == 0:
            # Transmission successful!
            # Return xmit id to set:
            logger.debug("GOOD: tx_status (id = %d)" % xmit_id)
            self.__xmit_id_set.add(xmit_id)
            self.__xmit_table.expunge(xmit_id)
            return True
        
        # Bad TX status!
        xmit_req.retries_remaining -= 1
        if xmit_req.retries_remaining <= 0:
            logger.warn("send to %s FAILED permanently with tx_status = 0x%08x (%d)" % (
                addr[0], tx_status, tx_status) )
            self.__xmit_id_set.add(xmit_id)
            self.__xmit_table.expunge(xmit_id)
            return True
        
        # Mark TX for retry:
        logger.debug("send to %s FAILED with tx status = 0x%02x, will retry." % (
            addr[0], tx_status))
        xmit_req.state = XBeeXmitStack.XmitRequest.STATE_QUEUED
        return True
