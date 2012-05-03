
import sys
sys.path.insert(0, "..")

import pexpect

import unittest

import os
import json
import serial
import time

class TestCaseBase(unittest.TestCase):
    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)

        self._my_dir =  os.path.dirname(os.path.abspath(__file__))
        self.xig_src_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../src"))
        settings_fname = os.path.abspath(os.path.join(self._my_dir, "../test_settings.json"))
        self.settings = json.load(open(settings_fname))

        self.xig = None
        self.test_xbee = None
        self.test_xbee_addr = None

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

    def startTestXBee(self):
        if self.test_xbee is not None:
            return self.test_xbee

        self.test_xbee = serial.Serial(self.settings['test-xbee-com_port'],
                                  self.settings['test-xbee-baud'],
                                  rtscts=1)
        self.test_xbee.writeTimeout = 1
        self.test_xbee.timeout = 5
        self.test_xbee.flushInput()

        return self.test_xbee

    def stopTestXBee(self):
        try:
            self.test_xbee.close()
        finally:
            self.test_xbee = None
            #self.test_xbee_addr = None  # do not flush known address from cache to speed test execution

    def doTestXBeeCommand(self, command):
        self.test_xbee.write("\r")
        time.sleep(2.000)
        self.test_xbee.write("+++")
        buf = self.test_xbee.read(16)
        if buf.find("OK") == -1:
            raise Exception, "unable to enter XBee command mode"
        time.sleep(0.250)
        self.test_xbee.write("AT%s\r" % command)
        buf = ""
        while buf.find("\r") == -1:
            newbuf = self.test_xbee.read()
            if len(newbuf) == 0:
                raise Exception, "no response to XBee AT command %s" % repr(command)
            buf += newbuf
        self.test_xbee.write("ATCN\r")
        self.test_xbee.read(3)

        return buf

    def getTestXBeeAddr(self):
        if self.test_xbee_addr is not None:
            return self.test_xbee_addr

        hw_addr = int(self.doTestXBeeCommand("SH"), 16) << 32
        hw_addr = hw_addr | int(self.doTestXBeeCommand("SL"), 16)
        hw_addr = "%016x" % hw_addr
        hw_addr = ':'.join([ p+q for p,q in zip(hw_addr[0::2], hw_addr[1::2]) ]) + '!'
        self.test_xbee_addr = hw_addr

        return self.test_xbee_addr

    def randomBytes(self, num_bytes):
        return os.urandom(num_bytes)

    def randomASCII(self, num_bytes):
        return (''.join(map(lambda c: chr((ord(c)) * (126 - 32) / 255 + 32),
                   self.randomBytes(num_bytes))))

