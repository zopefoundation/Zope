#! /usr/bin/env python

##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

import os
import sys
import test.regrtest

ec_tests = ["test_AqAlg", "test_MultiMapping", "test_Sync",
            "test_ThreadLock", "test_acquisition", "test_add",
            "test_binding", "test_explicit_acquisition",
            "test_method_hook"]

ec_testdir = os.path.split(sys.argv[0])[0] or '.'

test.regrtest.STDTESTS = ec_tests
test.regrtest.NOTTESTS = []

test.regrtest.main(testdir=ec_testdir)
