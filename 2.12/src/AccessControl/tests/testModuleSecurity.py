##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import unittest

class ModuleSecurityTests(unittest.TestCase):

    def setUp(self):
        from AccessControl import ModuleSecurityInfo as MSI
        MSI('AccessControl.tests.mixed_module').declarePublic('pub')
        MSI('AccessControl.tests.public_module').declarePublic('pub')
        MSI('AccessControl.tests.public_module.submodule').declarePublic('pub')

    def tearDown(self):
        import sys
        for module in ('AccessControl.tests.public_module',
                       'AccessControl.tests.public_module.submodule',
                       'AccessControl.tests.mixed_module',
                       'AccessControl.tests.mixed_module.submodule',
                       'AccessControl.tests.private_module',
                       'AccessControl.tests.private_module.submodule',
                      ):
            if module in sys.modules:
                del sys.modules[module]

    def assertUnauth(self, module, fromlist, level=-1):
        from zExceptions import Unauthorized
        from AccessControl.ZopeGuards import guarded_import
        self.assertRaises(Unauthorized, guarded_import, module,
                          fromlist=fromlist, level=level)

    def assertAuth(self, module, fromlist, level=-1):
        from AccessControl.ZopeGuards import guarded_import
        guarded_import(module, fromlist=fromlist, level=level)

    def testPrivateModule(self):
        self.assertUnauth('AccessControl.tests.private_module', ())
        self.assertUnauth('AccessControl.tests.private_module', ('priv',))
        self.assertUnauth('AccessControl.tests.private_module.submodule', ())
        self.assertUnauth('AccessControl.tests.private_module.submodule',
                          ('priv',))

    def testMixedModule(self):
        self.assertAuth('AccessControl.tests.mixed_module', ())
        self.assertAuth('AccessControl.tests.mixed_module', ('pub',))
        self.assertUnauth('AccessControl.tests.mixed_module', ('priv',))
        self.assertUnauth('AccessControl.tests.mixed_module.submodule', ())

    def testPublicModule(self):
        self.assertAuth('AccessControl.tests.public_module', ())
        self.assertAuth('AccessControl.tests.public_module', ('pub',))
        self.assertAuth('AccessControl.tests.public_module.submodule', ())
        self.assertAuth('AccessControl.tests.public_module.submodule',
                        ('pub',))

    def test_public_module_asterisk_not_allowed(self):
        self.assertUnauth('AccessControl.tests.public_module', ('*',))

    def test_failed_import_keeps_MSI(self):
        # LP #281156
        from AccessControl import ModuleSecurityInfo as MSI
        from AccessControl.SecurityInfo import _moduleSecurity as MS
        from AccessControl.ZopeGuards import guarded_import
        MSI('AccessControl.tests.nonesuch').declarePublic('pub')
        self.failUnless('AccessControl.tests.nonesuch' in MS)
        self.assertRaises(ImportError,
                      guarded_import, 'AccessControl.tests.nonesuch', ())
        self.failUnless('AccessControl.tests.nonesuch' in MS)

    def test_level_default(self):
        self.assertAuth('AccessControl.tests.public_module', (), level=-1)

    def test_level_nondefault(self):
        self.assertUnauth('AccessControl.tests.public_module', (), level=1)


def test_suite():
    return unittest.makeSuite(ModuleSecurityTests)
