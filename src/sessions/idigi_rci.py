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

The payload of the <do_command> element is XML formatted.  The
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

Set a remote AT command parameter:

  <!-- The apply flag is the equivalent of the AC command -->
  <at hw_address="00:11:22:33:44:55:66:77!" command="D1" value="4" apply="True" />

Response:

  <at_response command="D1" operation="set" result="ok"/>

Get a remote AT command parameter:

  <at hw_address="00:11:22:33:44:55:66:77!" command="D1" />

Response:

  <at_response command="D1" operation="get" result="ok" type="int" value="0x4" />

"""

import exceptions
import threading
import sys
import logging

import library.digi_ElementTree as ET
from library.io_sample import parse_is

try:
    import idigidata        # new style
except:
    pass

try:
    import rci              # old style
except:
    pass

import xbee

from abstract_autostart import AbstractAutostartSession
from abstract import AbstractSession

logger = logging.getLogger("xig.idigi_rci")
logger.setLevel(logging.INFO)


class iDigiRCIAutostartSession(AbstractAutostartSession):
    def __init__(self, xig_core):
        self.__core = xig_core
        self.__targets_desc = ""
        self.__started = False

        if 'idigidata' in sys.modules and hasattr(idigidata, 'register_callback'):
            # new style
            idigidata.register_callback("xig", lambda target, data: self.__rci_callback(data))
            self.__targets_desc = '"data_service"'
            self.__started = True
            
        if 'rci' in sys.modules and hasattr(rci, 'add_rci_callback'):
            # old style
            rci_thread = threading.Thread(name="XIG RCI Handler",
                             target=lambda: rci.add_rci_callback(
                                 "xig", self.__rci_callback))
            rci_thread.setDaemon(True)
            rci_thread.start()
            self.__targets_desc = ' '.join((self.__targets_desc,'"do_command"'))
            self.__started = True
            
        if not self.__started:
            raise Exception, "unable to start: no RCI callback registration methods"

    def helpText(self):
        return """\
 idigi_rci is running, accepting commands on "xig" target for %s services
""" % (self.__targets_desc)

    def __xml_err_msg(self, error_msg):
        error_tree = ET.Element("error")
        error_tree.set("message", error_msg)
        error_tree = ET.ElementTree(error_tree)
        return str(error_tree.writestring())

    def __rci_send_data(self, xig_tree):
        """\
        Process a send_data node, rci_xig_tree is an ElementTree.

        Node tag may be of type "send_data" or "send_hexdata". Returns a
        string response.
        """

        destination = str(xig_tree.get("hw_address"))
        data = ""

        if xig_tree.tag == "send_data":
            data = str(xig_tree.text) or ""
            encoding = xig_tree.get("encoding")
            if encoding is None:
              encoding = "ascii"

            if encoding == "ascii":
              data = str(data.decode("ascii"))
            elif encoding == "string_escape":
              data = str(data.decode("string_escape"))
            else:
              return self.__xml_err_msg("unknown encoding %s" % encoding)
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
            destination = self.__core.xbeeAddrTupleFromHwAddr(destination)
        except:
            return self.__xml_err_msg('invalid hw_address "%s"' % str(destination))
        new_session = iDigiRCISession(xig_core=self.__core,
                                      url="",
                                      xbee_addr=destination)
        new_session.appendSessionToXBeeBuffer(data)
        try:
            self.__core.enqueueSession(new_session)
            logger.info("%s %d bytes to %s" % (xig_tree.tag, len(data), repr(destination)))
        except exceptions.OverflowError:
            return self.__xml_err_msg("queue full for destination")

        # generate the RCI response:
        response_tree = ET.Element(xig_tree.tag + "_response")
        response_tree.set("result", "ok")
        response_tree = ET.ElementTree(response_tree)
        return str(response_tree.writestring())

    def __format_is_response_tree(self, is_data):
        sample = parse_is(is_data)
        # build pin sets:
        ad_set = set(map(lambda d: "AD%d" % d, range(7)))
        dio_set = set(map(lambda d: "DIO%d" % d, range(13)))
        io_set = ad_set.union(dio_set)
        sample_set = set(sample.keys())

        # build nodes:
        new_nodes = [ ]
        for io_pin in io_set.intersection(sample_set):
            response_tree = ET.Element("io_pin")
            response_tree.set("name", io_pin)
            value = str(bool(int(sample[io_pin])))
            if io_pin in ad_set:
                value = str(int(sample[io_pin]))
                response_tree.set("unit", "int")
            else:
                response_tree.set("unit", "bool")
            response_tree.set("value", value)
            new_nodes.append(response_tree)

        return new_nodes

    def __rci_at(self, xig_tree):
        """\
        Process a an "at" node, xig_tree is an ElementTree.

        Returns a string response.
        """
        destination = str(xig_tree.get("hw_address"))
        command = str(xig_tree.get("command")).upper()
        if destination is None:
            return self.__xml_err_msg('invalid hw_address "%s" (missing \'!\'?)' % destination)
        if command is None:
            return self.__xml_err_msg('invalid command "%s"' % command)
        value = xig_tree.get("value")
        if value is not None:
            value = str(value)
        apply = False
        try:
            apply = bool(xig_tree.get("apply").lower() == "true")
        except:
            pass

        # interpret value:
        if command in ("NI","DN"):
            pass            # interpret value as string
        elif command in ("AC", "WR"):
            value = ""
        elif value is None or len(value) == 0 or value.isspace():
            value = None    # will cause us to read instead of write param
        elif value.lower().startswith("0x"):
            try:
                value = int(value, 16)
            except:
                return self.__xml_err_msg(
                            "unable to parse hex int for cmd %s" % repr(command))
        else:
            try:
                value = int(value)
            except:
                return self.__xml_err_msg(
                            "unable to parse int for cmd %s" % repr(command))
        # run command:
        try:
            result = ""
            operation = "set"
            if value is not None:
                logger.info("AT set param to %s %s=%s" % (repr(destination), command, repr(value)))
                value = xbee.ddo_set_param(destination, command, value, apply=apply)
                result = "ok"
            else:
                operation = "get"
                logger.info("AT get param %s from %s" % (command, repr(destination)))
                value = xbee.ddo_get_param(destination, command)
                result = "ok"
        except Exception, e:
            result = "error"
            value = str(e)

        # Normalize value and generate type information:
        original_value = value
        if operation == "get" or result != "ok":
            if command == "NI" or result != "ok":
                value = str(value)
                type = "str"
            else:
                # unpack byte string:
                try:
                    value = hex(reduce(lambda s, x: (s << 8) + ord(x), value, 0))
                    type = "int"
                except:
                    return self.__xml_err_msg(
                                "unable to form result for %s" % repr(value))


        # generate the RCI response:
        response_tree = ET.Element("at_response")
        response_tree.set("command", command)
        response_tree.set("operation", operation)
        response_tree.set("result", result)
        if operation == "get" or result != "ok":
            response_tree.set("type", type)
            response_tree.set("value", value)
        # special decode for IS response:
        if command == "IS" and operation == "get" and result == "ok":
            for node in self.__format_is_response_tree(original_value):
                response_tree.append(node)
        response_tree = ET.ElementTree(response_tree)
        return str(response_tree.writestring())


    def __rci_callback(self, message):
        # sneakily re-root message string:
        message = "<root>" + message + "</root>"
        try:
            xig_tree = ET.fromstring(message)
        except Exception, e:
            return self.__xml_err_msg(str(e))

        result = ""
        # switch on command names, unhandled command names will generate
        # an error:
        for node in xig_tree:
            if node.tag in ("send_data", "send_hexdata"):
                result += self.__rci_send_data(node)
            elif node.tag == "at":
                result += self.__rci_at(node)
            else:
                result += self.__xml_err_msg(
                        "unknown command: %s" % str(node.tag))

        return result


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

