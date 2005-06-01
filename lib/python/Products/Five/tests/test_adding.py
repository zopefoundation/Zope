##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Test adding views

$Id: test_adding.py 12915 2005-05-31 10:23:19Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import Products.Five.tests.fivetest   # starts Zope, loads Five, etc.

def test_suite():
    from Testing.ZopeTestCase import ZopeDocFileSuite
    return ZopeDocFileSuite('adding.txt',
                            package="Products.Five.tests")

if __name__ == '__main__':
    framework()
