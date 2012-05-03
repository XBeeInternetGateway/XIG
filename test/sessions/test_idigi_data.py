#!/usr/bin/python2.7

import sys
sys.path.insert(0, "..")

from common.test_case_base import TestCaseBase
from common.idigi_client import iDigiClient
import pexpect

import hashlib
import random
import time
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

class TestiDigiData(TestCaseBase):
    def setUp(self):
        self.xig = TestCaseBase.startXig(self)
        self.test_xbee = TestCaseBase.startTestXBee(self)

    def tearDown(self):
        TestCaseBase.stopTestXBee(self)
        TestCaseBase.stopXig(self)

    def test_idigi_data(self):
        """
        Test the idigi_data session, closed loop with iDigi.
        """

        # message to send to server
        idigi = iDigiClient(self.settings["idigi-username"],
                            self.settings["idigi-password"],
                            self.settings["idigi-server"])

        hw_addr = TestCaseBase.getTestXBeeAddr(self)
        idigi_xbee_name = "XBee_" + filter(lambda c: c.lower() in '0123456789abcdef', hw_addr)[-8:].upper()

        # inject some data into iDigi
        random_counter = random.randint(0,2**32)
        xig_command = "idigi_data:names=temperature,counter,stooge&values=21.5,%d,curly&units=C,people,\r\n" % (
                            random_counter)
        self.test_xbee.write(xig_command)
        self.xig.expect("upload of \d+ samples successful", timeout=60)

        # request samples from iDigi:
        time.sleep(2.0) # wait for iDigi data store to become coherent
        idigi_req_path = "/ws/DiaChannelDataFull/%s/%s" % (self.settings["idigi-device_id"], idigi_xbee_name)
        idigi_response = idigi.get_request(idigi_req_path)

        # set our expectations:
        expectations = {
                "temperature": ("21.5", "C"),
                "counter": (str(random_counter), "people"),
                "stooge": ("curly", ""),
        }

        tree = ET.fromstring(idigi_response)

        for subtree in tree.findall("DiaChannelDataFull"):
            channel_name = subtree.findtext("id/dcChannelName")
            if channel_name in expectations:
                exp_value, exp_unit = expectations[channel_name]
                value = subtree.findtext("dcdStringValue").strip()
                unit = subtree.findtext("dcUnits").strip()
                self.assertEqual(exp_value, value)
                self.assertEqual(exp_unit, unit)
                del(expectations[channel_name])

        self.assertDictEqual(expectations, {})


if __name__ == "__main__":
    unittest.main()

