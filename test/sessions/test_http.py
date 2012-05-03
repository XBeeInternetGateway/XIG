#!/usr/bin/python2.7

import sys
sys.path.insert(0, "..")

from common.test_case_base import TestCaseBase
import pexpect

import hashlib

class TestHTTP(TestCaseBase):
    def setUp(self):
        self.xig = TestCaseBase.startXig(self)
        self.test_xbee = TestCaseBase.startTestXBee(self)

    def tearDown(self):
        TestCaseBase.stopTestXBee(self)
        TestCaseBase.stopXig(self)

    def test_http_request(self):
        """
        Fetches http://faludi.com/test.html and compare data against
        known MD5 hash.
        """
        EXPECTED_MD5 = '36bb8fcca9a729cf7f75e2f526f58762'

        test_xbee = self.test_xbee
        test_xbee.flushInput()
        test_xbee.write("http://faludi.com/test.html\r\n")
        test_xbee.timeout = 2
        buf = ""
        while buf.rfind("</html>") == -1:
            newbuf = test_xbee.read()
            try:
                self.xig.read_nonblocking(1024, timeout=0)
            except:
                pass
            if len(newbuf) == 0:
                print buf
                raise Exception, "serial read timeout"
            buf += newbuf
        buf = buf.strip()
        m = hashlib.md5()
        m.update(buf)
        self.assertEqual(m.hexdigest(), EXPECTED_MD5)


    def test_http_request_long(self):
        """
        Ensures that a large request can be transferred.
        """
        EXPECTED_MIN_LENGTH = 142410

        test_xbee = self.test_xbee
        test_xbee.flushInput()
        test_xbee.write("http://www.gutenberg.org/files/5200/5200-h/5200-h.htm\r\n")
        test_xbee.timeout = 2
        buf = ""
        while buf.rfind("</html>") == -1:
            newbuf = test_xbee.read()
            try:
                self.xig.read_nonblocking(1024, timeout=0)
            except:
                pass
            if len(newbuf) == 0:
                print buf
                raise Exception, "serial read timeout"
            buf += newbuf
        self.assertGreaterEqual(len(buf), EXPECTED_MIN_LENGTH)


    def test_http_abort(self):
        """
        Ensures that the entirety of yahoo.com may be retrieved.
        """
        EXPECTED_MIN_LENGTH = 200000

        test_xbee = self.test_xbee
        test_xbee.flushInput()
        test_xbee.write("http://www.gutenberg.org/files/5200/5200-h/5200-h.htm\r\n")
        test_xbee.timeout = 2
        buf = ""
        # accumulate some data:
        for i in xrange(64):
            buf += test_xbee.read(128)
            try:
                self.xig.read_nonblocking(1024, timeout=0)
            except:
                pass
        self.assertGreater(len(buf), 0)
        # send abort command:
        buf = ""
        abort_found = False
        test_xbee.write("xig://abort\r\n")
        while 1:
            newbuf = test_xbee.read()
            try:
                self.xig.read_nonblocking(1024, timeout=0)
            except:
                pass
            if len(newbuf) == 0:
                print buf
                raise Exception, "serial read timeout"
            buf += newbuf
            if buf.rfind("</html>") != -1:
                break
            if buf.rfind("Xig: connection aborted") != -1:
                abort_found = True
                break
        self.assertTrue(abort_found)

if __name__ == "__main__":
    unittest.main()

