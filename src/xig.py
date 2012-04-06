'''
Created on Sep 17, 2010

@author: jordanh

XBee Internet Gateway executable scripts.

See http://code.google.com/p/xig/ or README.txt for more information.
'''

## Global String Constants
NAME = "XBee Internet Gateway (XIG)"
SHORTNAME = "xig"
VERSION = "1.5.0"

import sys

sys.path.insert(0, "./library/cp4pc")
APP_ARCHIVE = "WEB/python/_xig.zip"
sys.path.insert(0, APP_ARCHIVE)

# logging_stub will replace logging module on platforms that don't support logging.
#NOTE: logging_stub MUST be imported before logging and ANY modules that import logging
import library.logging_stub #@UnusedImport
import logging
import traceback
import time
import string

# need to override socket by importing xbee.py first
import xbee #@UnusedImport

logger = logging.getLogger("xig")
logger.setLevel(logging.DEBUG)

logger.info("%s v%s starting." % (NAME, VERSION))

# Digi specific library module imports
import rci

# XIG library imports
from library.xig_io_kernel import XigIOKernel
from library.sched_async import SchedAsync

# XIG Library imports
import sessions
try:
    from xig_config import XigConfig
except:
    logger.debug("No xig_config.py found, using default config")
    # XIG default configuration import:
    from xig_config_default import XigConfig

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
 time or xig://time:   returns the time in ISO format

$sessionHelpText
AUTO-STARTED SESSION SERVICES:

$autostartHelpText
"""

class Xig(object):
    def __init__(self):
        self.__session_classes = []
        self.__autostart_sessions = []
        self.__config = XigConfig()
        self.__sched = SchedAsync("xig_sched", self)
        
        self.helpfile = ""
        
        self.__quit_flag = False
        self.__io_kernel = XigIOKernel(xig_core=self)

    def quit(self):
        self.__quit_flag = True

    def isXBeeXmitStatusSupported(self):
        if sys.platform == "digix3":
            return False

        return True

    def getLocalIP(self):
        query_string = """\
        <rci_request version="1.1">
            <query_state><boot_stats/></query_state>
        </rci_request>"""
        response = rci.process_request(query_string)
        ip_beg, ip_end = (0, 0)
        if sys.platform == "digix3":
            ip_beg = response.find("<ip_address>")+1
            ip_end = response.find("</ip_address>")
        else:
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

    def getAutostartSessions(self, obj_type=None):
        if obj_type is None:
            return self.__autostart_sessions

        for obj in self.__autostart_sessions:
            if isinstance(obj, obj_type):
                return obj
        return None

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

    def scheduleAfter(self, delay, action, *args):
        return self.__sched.schedule_after(delay, action, *args)


    def go(self):
        logger.info("Loading and initializing configured session types...")
        for session_type in self.__config.session_types:
            if session_type not in sessions.SESSION_MODEL_CLASS_MAP:
                logger.warn('unknown session type "%s", skipping.' % session_type)
                continue
            session_classes = sessions.SESSION_MODEL_CLASS_MAP[session_type]
            logger.debug("Loading %s from %s..." % (repr(session_classes), session_type))
            for session_class in session_classes:
                class_obj = sessions.classloader(module_name="sessions." + session_type, object_name=session_class)
                if issubclass(class_obj, sessions.AbstractSession):
                    self.__session_classes.append(class_obj)
                elif issubclass(class_obj, sessions.AbstractAutostartSession):
                    self.__autostart_sessions.append(class_obj(xig_core=self))

        logger.debug("Formatting help text...")
        sessionHelpText = "".join(map(lambda c: c.commandHelpText(), self.__session_classes))
        autostartHelpText = " (none)\n"
        if len(self.__autostart_sessions):
            autostartHelpText = "".join(map(lambda c: c.helpText(), self.__autostart_sessions))

        self.helpfile = (string.Template(HELPFILE_TEMPLATE)
                               .substitute(
                                  appName=NAME, appVersion=VERSION,
                                  ipAddr=self.getLocalIP(),
                                  sessionHelpText=sessionHelpText,
                                  autostartHelpText=autostartHelpText))
        self.helpfile = self.helpfile.replace('\n', '\r\n')
        logger.info("Starting scheduler...")
        self.__sched.start()
        logger.info("XIG startup complete, ready to serve requests.")
        while not self.__quit_flag:
            try:
                self.__io_kernel.ioLoop(timeout=1)
            except Exception, e:
                logger.error("Exception during I/O loop: %s"%e)
                traceback.print_exc(file=sys.stdout)
        logger.info("Shutting down.")
        # run one last time, with feeling:
        self.__io_kernel.ioLoop(timeout=5.0)
        self.__io_kernel.shutdown()

        # unregister rci callback
        #TODO: move this elsewhere?
        try:
            rci.stop_rci_callback("xig")
        except:
            pass

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
        return(self.__io_kernel.xbeeAddrFromHwAddr(hw_addr, ep, profile, cluster))


def main():
    # take off every Xig!
    xig = Xig()
    ret = -1
    try:
        ret = xig.go()
    except Exception, e:
        logger.error("Problem in go(), exiting program: %s" % e)
        traceback.print_exc(file=sys.stdout)
        time.sleep(10)
        # TODO: until shutdown may be propagated cleanly, allow XIG to squirt
        #	out the exception before exiting (and ultimately causing a
        #	reboot on the ConnectPort)
    sys.exit(ret)


if __name__ == "__main__":
    logger = logging.getLogger('')
    logger.addHandler(logging.StreamHandler(sys.__stdout__))
    ret = main()
    sys.exit(ret)
