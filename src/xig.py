'''
Created on Sep 17, 2010

@author: jordanh

See XIG README.txt for more information.
'''

## Global String Constants
NAME = "XBee Internet Gateway (XIG)"
SHORTNAME = "xig"
VERSION = "1.3.0a3"

print "%s v%s starting." % (NAME, VERSION)
print 'Unzipping and loading modules...'

import sys

APP_ARCHIVE = "WEB/python/_xig.zip"
sys.path.insert(0, APP_ARCHIVE)

# additional Python standard library imports
from socket import gethostbyname_ex
import string

# Digi specific library module imports
DIGI_PLATFORM_FLAG = False
if sys.platform.startswith('digi'):
    DIGI_PLATFORM_FLAG = True
    import rci, xbee

# XIG library imports
from library.xig_io_kernel import XigIOKernel

# Windows specific library module imports:
if sys.platform.startswith('win'):
    from library.win_socketpair import SocketPair as socketpair
    
# XIG Library imports
import sessions
# XIG default configuration import:
from xig_config_default import XigConfig
try:
    from xig_config import XigConfig
except:
    print "  (no xig_config.py found, using default config)"
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

$sessionHelpText
AUTO-STARTED SESSION SERVICES:

$autostartHelpText
"""

class Xig(object):
    def __init__(self):
        self.__session_classes = []
        self.__autostart_sessions = []
        self.__config = XigConfig()
 
        self.helpfile = ""
        
        self.__quit_flag = False
        self.__io_kernel = XigIOKernel(xig_core=self)

    def quit(self):
        self.__quit_flag = True

    def getLocalIP(self):
        if not sys.platform.startswith('digi'):
            if sys.platform.startswith('darwin'):
                return gethostbyname_ex('localhost')[2]
            else:
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

    def getSessionClasses(self):
        # XigSession must always be last for proper command handling:
        return self.__session_classes + [sessions.XigSession]

    def getConfig(self):
        return self.__config

    def ioSampleSubcriberAdd(self, func):
        """\
            Called by another object if it wishes to receive a
            callback for each XBee I/O Sample packet.
            
            func argument must be a function which accepts two
            arguments buf and addr.
        """
        self.__io_kernel.ioSubscriberAdd(func)
        
    def ioSampleSubcriberRemove(self, func):
        """\
            Called by an object if it wishes to stop receiving
            callbacks for each XBee I/O Sample packet.
            
            The func argument must match the argument given
            previously to ioSampleSubscriberAdd()
        """
        self.__io_kernel.ioSubscriberRemove(func)
                    
    def go(self):
        print "Loading and initializing configured session types..."
        for session_type in self.__config.session_types:
            if session_type not in sessions.SESSION_MODEL_CLASS_MAP:
                print 'unknown session type "%s", skipping.' % session_type
                continue
            session_classes = sessions.SESSION_MODEL_CLASS_MAP[session_type]
            print "Loading %s from %s..." % (repr(session_classes),
                                             session_type)
            for session_class in session_classes:
                class_obj = sessions.classloader(
                              module_name="sessions." + session_type,
                              object_name=session_class)
                if issubclass(class_obj, sessions.AbstractSession):
                    self.__session_classes.append(class_obj)
                elif issubclass(class_obj, sessions.AbstractAutostartSession):
                    self.__autostart_sessions.append(class_obj(xig_core=self))

        print "Formatting help text..."
        sessionHelpText = "".join(map(lambda c: c.commandHelpText(),
                                        self.__session_classes))
        autostartHelpText = " (none)\n"
        if len(self.__autostart_sessions):
            autostartHelpText = "".join(map(lambda c: c.helpText(),
                                              self.__autostart_sessions))
                   
        self.helpfile = (string.Template(HELPFILE_TEMPLATE)
                          .substitute(
                            appName=NAME, appVersion=VERSION,
                            ipAddr=self.getLocalIP(),
                            sessionHelpText=sessionHelpText,
                            autostartHelpText=autostartHelpText))
        self.helpfile = self.helpfile.replace('\n', '\r\n')        
        print "XIG startup complete, ready to serve requests."
        while not self.__quit_flag:
            self.__io_kernel.ioLoop(timeout=None)
        # run one last time, with feeling:
        self.__io_kernel.ioLoop(timeout=5.0)
        self.__io_kernel.shutdown()

        # From Digi support, to prevent the dreaded:
        # "zipimport.ZipImportError: bad local file header in WEB/python/_xig.zip" error
        import zipimport
        syspath_backup = list(sys.path)
        zipimport._zip_directory_cache.clear()
        sys.path = syspath_backup
        
        return 0


    def enqueueSession(self, session):
        """\
            Adds a new session object to the XIG core for processing
            within the XIG core ioLoop().
            
            The session object must be a valid object derived from
            AbstractSession.
        """
        self.__io_kernel.enqueueSession(session)
        
    def xbeeAddrFromHwAddr(self, hw_addr, ep=None, profile=None, cluster=None):
        return(
          self.__io_kernel.xbeeAddrFromHwAddr(hw_addr, ep, profile, cluster))

                    
def main():
    # take off every Xig!
    xig = Xig()
    ret = xig.go()
    sys.exit(ret)

    
if __name__ == "__main__":
    ret = main()
    sys.exit(ret)
