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
"""Test import conflicts

$Id: test_import_conflicts.py 18150 2005-10-04 16:19:49Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def testImportConflicts():
    """
    In a Five environment, importing Zope 3 packages that would use
    interfaces from the Zope 3 transaction module would lead to an
    error, because of the monkey patching.  The zope.app.mail package
    makes use of transaction interfaces, for example the following
    class:

      >>> from zope.app.mail.delivery import QueueProcessorThread

    Note that this only concerns Zope 2.7 and Zope X3 3.0.
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
