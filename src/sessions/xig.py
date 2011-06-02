"""
XigSession implementation.  Handles all xig:// control commands.
"""

from abstract import AbstractSession
from library import time_helpers

class XigSession(AbstractSession):
    """\
    An abstract Internet session, used to facilitate the gatewaying of
    data between the Internet domain and an XBee node.
    """
    
    def __init__(self, xig_core, url, xbee_addr):
        self.__core = xig_core 
        self.__xbee_addr = xbee_addr
        self.__write_buf = ""
        self.__read_buf = ""
         

        if url in ('help', 'xig://help'):
            self.appendSessionToXBeeBuffer(xig_core.helpfile)
        elif url in ('abort', 'xig://abort'):
            self.appendSessionToXBeeBuffer("Xig: No session to abort.\r\n")
        elif url in ('time','xig://time'):
            self.handleCommandTime()
        elif url in('quit', 'xig://quit'):
            self.appendSessionToXBeeBuffer("Xig: Quitting...\r\n")
            self.__core.quit()
        else:
            self.appendSessionToXBeeBuffer(
              xig_core.helpfile + "\r\n\r\nUnknown command: %s\r\n" % url) 
    
                           
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        """
        Attempt to handle an in-session command given by cmd_str from
        xbee_addr

        Always returns a XigSession instance.
        """
        return XigSession(xig_core, cmd_str, xbee_addr)
         
    def isFinished(self):
        return len(self.__write_buf) == 0

    def getXBeeAddr(self):
        return self.__xbee_addr
    
    def getReadSockets(self):
        return []
    
    def getWriteSockets(self):
        return []

    def getSessionToXBeeBuffer(self):
        return self.__write_buf
    
    def getXBeeToSessionBuffer(self):
        return self.__read_buf

    def appendSessionToXBeeBuffer(self, buf):
        self.__write_buf += buf
        
    def appendXBeeToSessionBuffer(self, buf):
        self.__read_buf += buf
        
    def accountSessionToXBeeBuffer(self, count):
        self.__write_buf = self.__write_buf[count:]
        
    def accountXBeeToSessionBuffer(self, count):
        self.__read_buf = self.__read_buf[count:]

    def handleCommandTime(self):
        # Get the current time, add time zone adjustment, if any:
        time_str = time_helpers.iso_date(t=None, use_local_time_offset=True)          
        self.appendSessionToXBeeBuffer("Xig: " + time_str + "\r\n")
                 