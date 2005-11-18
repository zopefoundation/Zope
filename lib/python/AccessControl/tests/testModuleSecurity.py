##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Module Import Tests
"""

__rcs_id__='$Id$'
__version__='$Revision: 1.4 $'[11:-2]

import os, sys, unittest

import Testing
import ZODB
from AccessControl import User
from AccessControl import Unauthorized, ModuleSecurityInfo
from AccessControl.ZopeGuards import guarded_import

ModuleSecurityInfo('AccessControl.tests.mixed_module').declarePublic('pub')

ModuleSecurityInfo('AccessControl.tests.public_module').declarePublic('pub')
ModuleSecurityInfo('AccessControl.tests.public_module.submodule'
                   ).declarePublic('pub')

class SecurityTests(unittest.TestCase):

    def assertUnauth(self, module, fromlist):
        try:
            guarded_import(module, fromlist=fromlist)
        except (Unauthorized, ImportError):
            # Passed the test.
            pass
        else:
            assert 0, ('Did not protect module instance %s, %s' %
                       (`module`, `fromlist`))

    def assertAuth(self, module, fromlist):
        try:
            guarded_import(module, fromlist=fromlist)
        except (Unauthorized, ImportError):
            assert 0, ('Did not expose module instance %s, %s' %
                       (`module`, `fromlist`))

    def testPrivateModule(self):
        for name in '', '.submodule':
            for fromlist in (), ('priv',):
                self.assertUnauth(
                    'AccessControl.tests.private_module%s' % name,
                    fromlist)

    def testMixedModule(self):
        self.assertAuth('AccessControl.tests.mixed_module', ())
        self.assertAuth('AccessControl.tests.mixed_module', ('pub',))
        self.assertUnauth('AccessControl.tests.mixed_module', ('priv',))
        self.assertUnauth('AccessControl.tests.mixed_module.submodule', ())

    def testPublicModule(self):
        for name in '', '.submodule':
            for fromlist in (), ('pub',):
                self.assertAuth(
                    'AccessControl.tests.public_module%s' % name,
                    fromlist)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( SecurityTests ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
