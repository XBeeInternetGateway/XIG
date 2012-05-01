
import sys
sys.path.insert(0, "..")

import pexpect

import unittest

import os
import json
import serial

class TestCaseBase(unittest.TestCase):
    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)

        self._my_dir =  os.path.dirname(os.path.abspath(__file__))
        self.xig_src_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../src"))
        settings_fname = os.path.abspath(os.path.join(self._my_dir, "../test_settings.json"))
        self.settings = json.load(open(settings_fname))

        self.xig = None

    def cdXig(self):
        """\
        Change working directory to xig source directory
        """
        os.chdir(self.xig_src_dir)

    def startXig(self):
        self.cdXig()
        child = pexpect.spawn("/usr/bin/python2.7 ./xig.py")
        child.expect("xig - XIG startup complete.*", timeout=10)
        self.xig = child

        return child

    def stopXig(self):
        self.xig.close()
        self.xig = None

    def getTestXBee(self):
        test_xbee = serial.Serial(self.settings['test-xbee-com_port'],
                                  self.settings['test-xbee-baud'],
                                  rtscts=1)
        test_xbee.writeTimeout = 1
        test_xbee.flushInput()

        return test_xbee

