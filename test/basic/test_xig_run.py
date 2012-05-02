#!/usr/bin/python2.7

import sys
sys.path.insert(0, "..")

from common.test_case_base import TestCaseBase

class TestXigRun(TestCaseBase):
    def test_xig_run(self):
        TestCaseBase.startXig(self)
        TestCaseBase.stopXig(self)

if __name__ == "__main__":
    unittest.main()

