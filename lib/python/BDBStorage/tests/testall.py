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

# Framework for running Unit tests

import unittest

MODULES = ('commitlog', 'create', 'virgin', 'zodb_simple', 'storage_api')



def suite():
    alltests = unittest.TestSuite()
    for modname in MODULES:
        mod = __import__('test_'+modname)
        alltests.addTest(mod.test_suite())
    return alltests

def test_suite():
    # Just to silence the top-level test.py
    return None



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
