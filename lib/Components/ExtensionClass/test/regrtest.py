#! /usr/bin/env python

import os
import sys
import test.regrtest

ec_tests = ["test_MultiMapping", "test_Sync", "test_ThreadLock",
            "test_acquisition", "test_add", "test_binding",
            "test_explicit_acquisition", "test_func_attr",
            "test_method_hook"]

ec_testdir = os.path.split(sys.argv[0])[0]
test.regrtest.main(tests=ec_tests, testdir=ec_testdir)
