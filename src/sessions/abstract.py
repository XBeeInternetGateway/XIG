class AbstractSession(object):
    """\
    An abstract Internet session, used to facilitate the gatewaying of
    data between the Internet domain and an XBee node.
    """
    def __init__(self, xig_core, url, xbee_addr):
        raise Exception, "not implemented"
    
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        """
        Attempt to handle an out-of-session command given by cmd_str from
        xbee_addr.
        
        If cmd_str is valid, return True.  If the command is not valid
        (or incomplete), return False.
        """
        raise Exception, "not implemented" 

    @staticmethod
    def commandHelpText():
        """\
            Return a string containing lines showing example what URL
            syntax the session supports.
            
            For example:
            
            http://<host/path> retrieves a URL
            https://<host/path> retrieves a secure URL
        """  
        raise Exception, "not implemented"

    def close(self):
        raise Exception, "not implemented"

    def isFinished(self):
        """Returns True when the session is ready to be reaped."""
        raise Exception, "not implemented"

    def getXBeeAddr(self):
        raise Exception, "not implemented"
    
    def getReadSockets(self):
        """Returns a list of active non-blocking socket objects which may be read"""
        raise Exception, "not implemented"

    def getWriteSockets(self):
        """Returns a list of active non-blocking socket objects which may be read"""
        raise Exception, "not implemented"
    
    def getSessionToXBeeBuffer(self):
        """Session contains data which needs to be written to XBee socket."""
        raise Exception, "not implemented"

    def getXBeeToSessionBuffer(self):
        """Session contains data which needs to be written to session socket."""
        raise Exception, "not implemented"
    
    def appendSessionToXBeeBuffer(self, buf):
        raise Exception, "not implemented"
    
    def appendXBeeToSessionBuffer(self, buf):
        raise Exception, "not implemented"
    
    def accountSessionToXBeeBuffer(self, count):
        """Remove count bytes from buffer used to write to XBee"""
    
    def read(self, sd):
        """
        Perform a read from active session socket. Returns count of bytes read.
        """
        raise Exception, "not implemented"
        
    def write(self, sd):
        """
        Perform a write to active session socket. Returns count of bytes written.
        """
        raise Exception, "not implemented"
        