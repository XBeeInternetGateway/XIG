"""\ 
iDigi RCI Session implementation.  Allows you to send data from the
Internet to an XBee via the iDigi cloud service.

In order to send data to a XIG instance running on a ConnectPort X
gateway via iDigi, you must formulate an XML message and use HTTP
POST to iDigi's SCI URL interface (e.g.
http://developer.idigi.com/ws/sci).  This message is formatted as
follows:

<sci_request version="1.0">
  <send_message>
    <targets>
      <device id="">
    </targets>
  </send_message>
  <rci_request version="1.1">
    <do_command target="xig">
      <!-- XIG XML command payload -->
    </do_command>
  </rci_request>
</sci_request>

This message must be posted to iDigi using your proper iDigi
user account credentials.  Visit http://www.idigi.com in order
to create your free developer account.

The payload of the <do_command> element is JSON formatted.  The
structure for XIG commands is the following:

  <COMMAND_NAME param1="val1" param2="val2" ..>data</COMMAND_NAME>

Response structure is:

  <COMMAND_NAME_response result="result string" />

General errors shall be reported as:

  <error message="exception string" />

The following commands are supported:

Send data to a remote XBee:

  <send_data hw_address="00:11:22:33:44:55:66:77!"/>Hello!</send_data>

Response:

  <send_data_response result="ok" />  
   
Send hex-encoded binary data to a remote XBee:

  <send_hexdata hw_address="00:11:22:33:44:55:66:77!">4A4B4C</send_hexdata>
                 
Response:

  <send_hexdata_response result="ok" />

"""

import sys
import exceptions
import threading
from encodings import string_escape

import library.digi_ElementTree as ET
import library.xbee_addressing as xbee_addressing


if sys.platform.startswith('digi'):
    import rci

from abstract_autostart import AbstractAutostartSession
from abstract import AbstractSession

class iDigiRCIAutostartSession(AbstractAutostartSession):
    def __init__(self, xig_core):
        self.__core = xig_core
        
        if not sys.platform.startswith('digi'):
            # this will not work on non-Digi platforms, early exit
            return
        
        rci_thread = threading.Thread(name="XIG RCI Handler",
                         target=lambda: rci.add_rci_callback(
                             "xig", self.__rci_callback)) 
        rci_thread.start()

    def helpText(self):
        return """\
 idigi_rci is running, accepting commands on do_command target "xig"
"""

    def __xml_err_msg(self, error_msg):
        error_tree = ET.Element("error")
        error_tree.set("message", error_msg)
        error_tree = ET.ElementTree(error_tree)
        return str(error_tree.writestring())
        
    def __rci_callback(self, message):
        #print "RCI: %s" % repr(message)
        try:
            xig_tree = ET.fromstring(message)
        except Exception, e:
            return self.__xml_err_msg(str(e))
        
        destination = str(xig_tree.get("hw_address"))
        data = ""
        
        # switch on command names, unhandled command names will generate
        # an error:
        if xig_tree.tag == "send_data":
            data = str(xig_tree.text) or ""
            data = data.decode("string_escape")
        elif xig_tree.tag == "send_hexdata":
            data = str(xig_tree.text) or ""
            data = filter(lambda c: c in "0123456789abcdef", data.lower())
            # Pythonic decode of hex data to binary string:
            try:
                data = ''.join([chr(int(''.join(t),16)) for t in 
                             zip(*[iter(data)]*2) ])
            except:
                return self.__xml_err_msg("bad hexdata given")
        else:
            return self.__xml_err_msg(
                    "unknown command: %s" % str(xig_tree.tag))
                
        if destination is None:
            return self.__xml_err_msg("hw_address parameter missing")

        try:
            destination = xbee_addressing.normalize_address(destination)
        except:
            return self.__xml_err_msg('invalid hw_address "%s" (missing \'!\'?)' % destination)
        
        destination = self.__core.xbeeAddrFromHwAddr(destination)
        new_session = iDigiRCISession(xig_core=self.__core,
                                      url="",
                                      xbee_addr=destination)
        new_session.appendSessionToXBeeBuffer(data)
        try:
            self.__core.enqueueSession(new_session)
        except exceptions.OverflowError:
            return self.__xml_err_msg("queue full for destination")
        
        # generate the RCI response:
        response_tree = ET.Element(xig_tree.tag + "_response")
        response_tree.set("result", "ok")
        response_tree = ET.ElementTree(response_tree)
        return str(response_tree.writestring())
        
        
class iDigiRCISession(AbstractSession):
    """\
    An abstract Internet session, used to facilitate the gatewaying of
    data between the Internet domain and an XBee node.
    """
    
    def __init__(self, xig_core, url, xbee_addr):
        self.__core = xig_core 
        self.__xbee_addr = xbee_addr
        self.__write_buf = ""     
        # no URLs are handled by this session, do nothing with the URL
                               
    @staticmethod
    def handleSessionCommand(xig_core, cmd_str, xbee_addr):
        # New sessions may not be started by an XBee-initiated command,
        # always return None.
        return None

    @staticmethod
    def commandHelpText():
        # supports no URL commands, return no help text
        return ""
         
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
        return ""

    def appendSessionToXBeeBuffer(self, buf):
        self.__write_buf += buf
        
    def appendXBeeToSessionBuffer(self, buf):
        return
        
    def accountSessionToXBeeBuffer(self, count):
        self.__write_buf = self.__write_buf[count:]
        
    def accountXBeeToSessionBuffer(self, count):
        return
                 