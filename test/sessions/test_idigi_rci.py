#!/usr/bin/python2.7

import sys
sys.path.insert(0, "..")

from common.test_case_base import TestCaseBase
from common.idigi_client import iDigiClient
import pexpect

import hashlib
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

class TestiDigiRCI(TestCaseBase):
    def setUp(self):
        self.xig = TestCaseBase.startXig(self)
        self.test_xbee = TestCaseBase.startTestXBee(self)

    def tearDown(self):
        TestCaseBase.stopTestXBee(self)
        TestCaseBase.stopXig(self)

    def test_at_read_multiple(self):
        """
        Tests the <send_data> command, sending ASCII data to a remote node.
        """

        # message to send to server
        idigi_message = """\
<sci_request version="1.0">
<send_message>
 <targets>
   <device id="%s"/>
 </targets>
 <rci_request version="1.1">
   <do_command target="xig">
     <at hw_address="%s" command="NI" />
     <at hw_address="%s" command="SH" />
     <at hw_address="%s" command="SL" />
   </do_command>
 </rci_request>
</send_message>
</sci_request>"""

        idigi = iDigiClient(self.settings["idigi-username"],
                            self.settings["idigi-password"],
                            self.settings["idigi-server"])

        hw_addr = TestCaseBase.getTestXBeeAddr(self)
        hw_addr_flat = filter(lambda c: c.lower() in "0123456789abcdef", hw_addr)
        exp_sh_val = int(hw_addr_flat[0:8], 16)
        exp_sl_val = int(hw_addr_flat[8:], 16)

        format_args = ((self.settings["idigi-device_id"],) + (hw_addr,)*3)
        idigi_message = idigi_message % ((self.settings["idigi-device_id"],) + (hw_addr,)*3)
        idigi_response = idigi.post_request("/ws/sci", idigi_message)
        tree = ET.fromstring(idigi_response)
        ni_node = tree.find('send_message/device/rci_reply/do_command/at_response[@command="NI"]')
        self.assertEqual(ni_node.get("result"), "ok")
        sh_node = tree.find('send_message/device/rci_reply/do_command/at_response[@command="SH"]')
        self.assertEqual(sh_node.get("result"), "ok")
        self.assertEqual(int(sh_node.get("value"), 16), exp_sh_val)
        sl_node = tree.find('send_message/device/rci_reply/do_command/at_response[@command="SL"]')
        self.assertEqual(sl_node.get("result"), "ok")
        self.assertEqual(int(sl_node.get("value"), 16), exp_sl_val)


    def test_send_data(self):
        """
        Tests the <send_data> command, sending ASCII data to a remote node.
        """

        # message to send to server
        idigi_message = """\
<sci_request version="1.0">
<send_message>
 <targets>
   <device id="%s"/>
 </targets>
 <rci_request version="1.1">
   <do_command target="xig">
     <send_data hw_address="%s">%s</send_data>
   </do_command>
 </rci_request>
</send_message>
</sci_request>"""

        idigi = iDigiClient(self.settings["idigi-username"],
                            self.settings["idigi-password"],
                            self.settings["idigi-server"])

        hw_addr = TestCaseBase.getTestXBeeAddr(self)
        self.test_xbee.flushInput()
        idigi_message = idigi_message % (self.settings["idigi-device_id"],
                                         hw_addr, "Hello, world!")
        idigi_response = idigi.post_request("/ws/sci", idigi_message)
        tree = ET.fromstring(idigi_response)
        send_data_response = tree.find('send_message/device/rci_reply/do_command/send_data_response')
        self.assertIsNotNone(send_data_response)
        self.assertEqual(send_data_response.get("result"), "ok")
        self.xig.read_nonblocking(1024)

        # check that message emerged from UART of test XBee
        buf = ""
        while buf.find("world!") == -1:
            newbuf = self.test_xbee.read()
            if len(newbuf) == 0:
                raise Exception, "Timeout reading data from XBee"
            buf += newbuf
        self.assertEqual("Hello, world!", buf)


    def test_send_data_long(self):
        """
        Tests the <send_data> command, sending ~32k of ASCII data to a remote node.
        """

        # message to send to server
        idigi_message = """\
<sci_request version="1.0">
<send_message>
 <targets>
   <device id="%s"/>
 </targets>
 <rci_request version="1.1">
   <do_command target="xig">
     <send_data hw_address="%s">%s</send_data>
   </do_command>
 </rci_request>
</send_message>
</sci_request>"""

        idigi = iDigiClient(self.settings["idigi-username"],
                            self.settings["idigi-password"],
                            self.settings["idigi-server"])

        hw_addr = TestCaseBase.getTestXBeeAddr(self)
        self.test_xbee.flushInput()

        test_data = TestCaseBase.randomASCII(self, 32*1024)
        test_data += "END_OF_MESSAGE"
        m = hashlib.md5()
        m.update(test_data)
        test_data_md5 = m.hexdigest()

        idigi_message = idigi_message % (self.settings["idigi-device_id"],
                                         hw_addr, escape(test_data))
        idigi_response = idigi.post_request("/ws/sci", idigi_message)
        tree = ET.fromstring(idigi_response)
        send_data_response = tree.find('send_message/device/rci_reply/do_command/send_data_response')
        self.assertIsNotNone(send_data_response)
        self.assertEqual(send_data_response.get("result"), "ok")
        self.xig.read_nonblocking(1024)

        # check that message emerged from UART of test XBee
        buf = ""
        m = hashlib.md5()
        self.test_xbee.timeout = 2
        while buf.rfind("END_OF_MESSAGE") == -1:
            newbuf = self.test_xbee.read()
            try:
                self.xig.read_nonblocking(1024, timeout=0)
            except:
                pass
            if len(newbuf) == 0:
                print buf
                raise Exception, "Timeout reading data from XBee: couldn't find END_OF_MESSAGE"
            buf += newbuf
            m.update(newbuf)
        self.assertEqual(m.hexdigest(), test_data_md5)

if __name__ == "__main__":
    unittest.main()

