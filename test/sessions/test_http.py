#!/usr/bin/python2.7

import sys
sys.path.insert(0, "..")

from classes.test_case_base import TestCaseBase
import pexpect

import hashlib

class TestHTTP(TestCaseBase):
    def setUp(self):
        self.xig = TestCaseBase.startXig(self)

    def tearDown(self):
        TestCaseBase.stopXig(self)

    def test_http_request(self):
        """
        Fetches http://faludi.com/test.html and compare data against
        known MD5 hash.
        """
        EXPECTED_MD5 = '36bb8fcca9a729cf7f75e2f526f58762'

        test_xbee = TestCaseBase.getTestXBee(self)
        try:
            test_xbee.write("http://faludi.com/test.html\r\n")
            test_xbee.timeout = 5
            buf = ""
            while 1:
                newbuf = test_xbee.read(128)
                self.xig.read_nonblocking(1024)
                if len(newbuf) == 0:
                    raise Exception, "serial read timeout"
                buf += newbuf
                if buf.rfind("</html>") > 0:
                    break
            buf = buf.strip()
            m = hashlib.md5()
            m.update(buf)
        finally:
            test_xbee.close()
        self.assertEqual(m.hexdigest(), EXPECTED_MD5)


    def test_http_yahoo(self):
        """
        Ensures that the entirety of yahoo.com may be retrieved.
        """
        EXPECTED_MIN_LENGTH = 200000

        test_xbee = TestCaseBase.getTestXBee(self)
        try:
            test_xbee.write("http://yahoo.com/\r\n")
            test_xbee.timeout = 8
            buf = ""
            while 1:
                newbuf = test_xbee.read(128)
                self.xig.read_nonblocking(1024)
                if len(newbuf) == 0:
                    raise Exception, "serial read timeout"
                buf += newbuf
                if buf.rfind("</html>") > 0:
                    break
        finally:
            test_xbee.close()
        self.assertGreaterEqual(len(buf), EXPECTED_MIN_LENGTH)


    def test_http_abort(self):
        """
        Ensures that the entirety of yahoo.com may be retrieved.
        """
        EXPECTED_MIN_LENGTH = 200000

        test_xbee = TestCaseBase.getTestXBee(self)
        try:
            test_xbee.write("http://yahoo.com/\r\n")
            test_xbee.timeout = 8
            buf = ""
            # accumulate some data:
            for i in xrange(64):
                buf += test_xbee.read(128)
                self.xig.read_nonblocking(1024)
            self.assertGreater(len(buf), 0)
            # send abort command:
            buf = ""
            abort_found = False
            test_xbee.write("xig://abort\r\n")
            while 1:
                newbuf = test_xbee.read(128)
                self.xig.read_nonblocking(1024)
                if len(newbuf) == 0:
                    raise Exception, "serial read timeout"
                buf += newbuf
                if buf.rfind("</html>") > 0:
                    break
                if buf.rfind("Xig: connection aborted") > 0:
                    abort_found = True
                    break
        finally:
            test_xbee.close()
        self.assertTrue(abort_found)

if __name__ == "__main__":
    unittest.main()

