#! /usr/bin/env python

import os
import sys
import test.regrtest

ec_tests = ["test_AqAlg", "test_MultiMapping", "test_Sync",
            "test_ThreadLock", "test_acquisition", "test_add",
            "test_binding", "test_explicit_acquisition",
            "test_func_attr", "test_method_hook"]

ec_testdir = os.path.split(sys.argv[0])[0] or '.'

test.regrtest.STDTESTS = ec_tests
test.regrtest.NOTTESTS = []

test.regrtest.main(testdir=ec_testdir)
