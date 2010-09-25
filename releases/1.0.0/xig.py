'''
Created on Sep 17, 2010

@author: jordanh
'''

## Global String Constants
NAME = "XBee Internet Gateway (xig)"
SHORTNAME = "xig"
VERSION = "1.0.0"

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
import struct, errno, string, random, shlex
from copy import copy
from socket import *
from select import *

# Digi specific library module imports
if sys.platform.startswith('digi'):
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
 abort:                aborts the current session

 http://<host/path> retrieves a URL
 https://<host/path> retrieves a secure URL 
 http://<user:pass@host/path> retrieves a URL using username and password
 https://<user:pass@host/path> retrieves a URL using username and password 

USE:
 The recommended speed is 115200 baud which can be set with ATBD7
 Lower baud rates may work if you are receiving short responses

 The following formats are NOT yet supported:

  ftp://<host/path>
  ftp://<username:password@host/path>  
  telnet://<host:port>
  mailto:<addr@host>
  

"""

class Xig(object):
    def __init__(self):
        self.helpfile = (string.Template(HELPFILE_TEMPLATE)
                           .substitute(appName=NAME, appVersion=VERSION,
                                        ipAddr=self.getLocalIP()))
        self.helpfile.replace('\n', '\r\n')
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
        while not self.__quit_flag:
            self.__io_kernel.ioLoop(timeout=None)
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

        


class XigIOKernel(object):
    XBEE_S1_MAX_PAYLOAD = 100
    XBEE_S23_MAX_PAYLOAD = 72
    XBEE_MIN_PAYLOAD = XBEE_S23_MAX_PAYLOAD
    
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
        
        if sys.platform.startswith('digi'):
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
                self.__xig_sd_max_io_sz = self.XBEE_S23_MAX_PAYLOAD
            else:
                bind_addr = ('', 0xe8, 0, 0)
                self.__xig_sd_max_io_sz = self.XBEE_MIN_PAYLOAD
            self.__xbee_sd.bind(bind_addr)            
        else:
            print "Using PC-based UDP simulation mode on port %d..." % (
              XBEE_SIM_UDP_PORT)
            self.__xbee_sd = socket(AF_INET, SOCK_DGRAM)
            self.__xig_sd_max_io_sz = self.XBEE_MIN_PAYLOAD
            self.__xbee_sd.bind(('', XBEE_SIM_UDP_PORT))

        # Put XBee socket into non-blocking mode:
        self.__xbee_sd.setblocking(0)


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
                try:
                    buf = sess.getSessionToXBeeBuffer()[0:self.__xig_sd_max_io_sz]
                    #print "IO write len %d to XBee" % len(buf)
                    count = self.__xbee_sd.sendto(buf, 0, sess.getXBeeAddr())
                    print "IO wrote len %d to XBee" % count
                    sess.accountSessionToXBeeBuffer(count)
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
