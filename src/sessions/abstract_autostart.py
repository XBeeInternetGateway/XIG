"""\
Implements a session object which is not device initiated.
That is to say, it is not started by an XBee device sending a
URL string to the gateway  rather it starts automatically.
Normally auto-started sessions are used to send data from the
Internet domain to an XBee without the XBee asking for it.
"""

class AbstractAutostartSession(object):
    """\
    Abstract auto-start session started by the system automatically.
    Generally used to send data to XBee devices.
    """
    def __init__(self, xig_core):
        raise Exception, "not implemented"
    
    def helpText(self):
        """\
            Return a string of text describing what the session does.
        """
        raise Exception, "not implemented"
