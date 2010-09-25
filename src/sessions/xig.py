
from abstract import AbstractSession

class XigSession(AbstractSession):
    """\
    An abstract Internet session, used to facilitate the gatewaying of
    data between the Internet domain and an XBee node.
    """
    
    COMMAND_NONE  = 0x0
    COMMAND_HELP  = 0x1
    COMMAND_ABORT = 0x2
    COMMAND_QUIT  = 0x3
    
    def __init__(self, xig_core, url, xbee_addr):
        self.__core = xig_core
        self.__xbee_addr = xbee_addr
        
        self.__write_buf = ""
        self.__read_buf = ""
        self.__command = XigSession.COMMAND_NONE
         

        if url == 'xig://help':
            self.__command = XigSession.COMMAND_HELP
            self.__write_buf = xig_core.helpfile
        elif url == 'xig://abort':
            self.__command = XigSession.COMMAND_ABORT
            self.__write_buf = "Xig: No session to abort.\r\n"
        elif url == 'xig://quit':
            self.__command = XigSession.COMMAND_QUIT
            self.__write_buf = "Xig: Quitting...\r\n"
            self.__core.quit()
        else:
            self.__command = XigSession.COMMAND_HELP
            self.__write_buf = xig_core.helpfile + (
                "\r\n\r\nUnknown command: %s\r\n" % url)
    
                           
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        """
        Attempt to handle an in-session command given by cmd_str from
        xbee_addr
        
        If cmd_str is valid, return True.  If the command is not valid
        (or incomplete), return False.
        """
        if cmd_str in ('help', 'xig://help'):
            return XigSession(xig_core, 'xig://help', xbee_addr)
        elif cmd_str in ('abort', 'xig://abort'):
            return XigSession(xig_core, 'xig://abort', xbee_addr)
        elif cmd_str in ('quit', 'xig://quit'):
            return XigSession(xig_core, 'xig://quit', xbee_addr)
        else:
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
