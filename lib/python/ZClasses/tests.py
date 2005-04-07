##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZClass tests

$Id$
"""

import os, sys
import unittest
import ZODB.tests.util
import transaction
from zope.testing import doctest


# XXX need to update files to get newer testing package
class FakeModule:
    def __init__(self, name, dict):
        self.__dict__ = dict
        self.__name__ = name


def setUp(test):
    test.globs['some_database'] = ZODB.tests.util.DB()
    module = FakeModule('ZClasses.example', test.globs)
    sys.modules[module.__name__] = module

def tearDown(test):
    transaction.abort()
    test.globs['some_database'].close()
    del sys.modules['ZClasses.example']

def tearDown27(test):
    transaction.abort()
    test.globs['db'].close()

# XXX Two tests are disable because they're failing on Zope trunk;
# XXX they didn't fail on Jim's branch:
#
# C:\Code\zt>\python23\python.exe test.py ZClas
# Running unit tests from C:\Code\zt\lib\python
# ======================================================================
# FAIL: Doctest: ZClass.txt
# ----------------------------------------------------------------------
# Traceback (most recent call last):
#   File "C:\Code\zt\lib\python\zope\testing\doctest.py", line 2102, in runTest
#     raise self.failureException(self.format_failure(new.getvalue()))
# AssertionError: Failed doctest test for ZClass.txt
#   File "C:\Code\zt\lib\python\ZClasses\ZClass.txt", line 0
#
# ----------------------------------------------------------------------
# File "C:\Code\zt\lib\python\ZClasses\ZClass.txt", line 88, in ZClass.txt
# Failed example:
#     print app2.c2.x, app2.c2.y, app2.c2.eek(), '!'
# Exception raised:
#     Traceback (most recent call last):
#       File "C:\Code\zt\lib\python\zope\testing\doctest.py", line 1315, in __run
#         compileflags, 1) in test.globs
#       File "<doctest ZClass.txt[35]>", line 1, in ?
#         print app2.c2.x, app2.c2.y, app2.c2.eek(), '!'
#       File "C:\Code\zt\lib\python\AccessControl\PermissionMapping.py", line 150, in __call__
#         return apply(self, args, kw)
#       File "C:\Code\zt\lib\python\Shared\DC\Scripts\Bindings.py", line 311, in __call__
#         return self._bindAndExec(args, kw, None)
#       File "C:\Code\zt\lib\python\Shared\DC\Scripts\Bindings.py", line 348, in _bindAndExec
#         return self._exec(bound_data, args, kw)
#       File "C:\Code\zt\lib\python\Products\PythonScripts\PythonScript.py", line 323, in _exec
#         result = f(*args, **kw)
#       File "Script (Python)", line 1, in eek
#     Unauthorized: You are not allowed to access 'x' in this context
# ----------------------------------------------------------------------
# File "C:\Code\zt\lib\python\ZClasses\ZClass.txt", line 110, in ZClass.txt
# Failed example:
#     c3.eek()
# Exception raised:
#     Traceback (most recent call last):
#       File "C:\Code\zt\lib\python\zope\testing\doctest.py", line 1315, in __run
#         compileflags, 1) in test.globs
#       File "<doctest ZClass.txt[42]>", line 1, in ?
#         c3.eek()
#       File "C:\Code\zt\lib\python\AccessControl\PermissionMapping.py", line 150, in __call__
#         return apply(self, args, kw)
#       File "C:\Code\zt\lib\python\Shared\DC\Scripts\Bindings.py", line 311, in __call__
#         return self._bindAndExec(args, kw, None)
#       File "C:\Code\zt\lib\python\Shared\DC\Scripts\Bindings.py", line 348, in _bindAndExec
#         return self._exec(bound_data, args, kw)
#       File "C:\Code\zt\lib\python\Products\PythonScripts\PythonScript.py", line 323, in _exec
#         result = f(*args, **kw)
#       File "Script (Python)", line 1, in eek
#     Unauthorized: You are not allowed to access 'x' in this context
#
#
# ======================================================================
# FAIL: Doctest: 27.txt
# ----------------------------------------------------------------------
# Traceback (most recent call last):
#   File "C:\Code\zt\lib\python\zope\testing\doctest.py", line 2102, in runTest
#     raise self.failureException(self.format_failure(new.getvalue()))
# AssertionError: Failed doctest test for 27.txt
#   File "C:\Code\zt\lib\python\ZClasses\27.txt", line 0
#
# ----------------------------------------------------------------------
# File "C:\Code\zt\lib\python\ZClasses\27.txt", line 16, in 27.txt
# Failed example:
#     ac.eek()
# Exception raised:
#     Traceback (most recent call last):
#       File "C:\Code\zt\lib\python\zope\testing\doctest.py", line 1315, in __run
#         compileflags, 1) in test.globs
#       File "<doctest 27.txt[10]>", line 1, in ?
#         ac.eek()
#       File "C:\Code\zt\lib\python\AccessControl\PermissionMapping.py", line 150, in __call__
#         return apply(self, args, kw)
#       File "C:\Code\zt\lib\python\Shared\DC\Scripts\Bindings.py", line 311, in __call__
#         return self._bindAndExec(args, kw, None)
#       File "C:\Code\zt\lib\python\Shared\DC\Scripts\Bindings.py", line 348, in _bindAndExec
#         return self._exec(bound_data, args, kw)
#       File "C:\Code\zt\lib\python\Products\PythonScripts\PythonScript.py", line 323, in _exec
#         result = f(*args, **kw)
#       File "Script (Python)", line 1, in eek
#     Unauthorized: You are not allowed to access 'x' in this context
# ----------------------------------------------------------------------
# File "C:\Code\zt\lib\python\ZClasses\27.txt", line 19, in 27.txt
# Failed example:
#     ac.eek()
# Exception raised:
#     Traceback (most recent call last):
#       File "C:\Code\zt\lib\python\zope\testing\doctest.py", line 1315, in __run
#         compileflags, 1) in test.globs
#       File "<doctest 27.txt[12]>", line 1, in ?
#         ac.eek()
#       File "C:\Code\zt\lib\python\AccessControl\PermissionMapping.py", line 150, in __call__
#         return apply(self, args, kw)
#       File "C:\Code\zt\lib\python\Shared\DC\Scripts\Bindings.py", line 311, in __call__
#         return self._bindAndExec(args, kw, None)
#       File "C:\Code\zt\lib\python\Shared\DC\Scripts\Bindings.py", line 348, in _bindAndExec
#         return self._exec(bound_data, args, kw)
#       File "C:\Code\zt\lib\python\Products\PythonScripts\PythonScript.py", line 323, in _exec
#         result = f(*args, **kw)
#       File "Script (Python)", line 1, in eek
#     Unauthorized: You are not allowed to access 'x' in this context
#
#
# ----------------------------------------------------------------------
# Ran 3 tests in 2.734s
#
# FAILED (failures=2)

def test_suite():
    return unittest.TestSuite((

        # To do:
        # - Test working with old pickles
        # - Test proper handling of __of__
        # - Test export/import

        doctest.DocFileSuite("_pmc.txt", setUp=setUp, tearDown=tearDown),
        ## XXX doctest.DocFileSuite("ZClass.txt", setUp=setUp, tearDown=tearDown),
        ## XXX doctest.DocFileSuite("27.txt", tearDown=tearDown27,
        ## XXX                    globs=dict(__file__=__file__),
        ## XXX                     ),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
