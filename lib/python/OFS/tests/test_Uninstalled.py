##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import unittest

class TestsOfBroken(unittest.TestCase):
    """Tests for the factory for "broken" classes.
    """

    def setUp(self):
        from OFS.Uninstalled import broken_klasses
        from OFS.Uninstalled import broken_klasses_lock
        self.broken_klasses_OLD = {}
        broken_klasses_lock.acquire()
        try:
            self.broken_klasses_OLD.update(broken_klasses)
            broken_klasses.clear()
        finally:
            broken_klasses_lock.release()

    def tearDown(self):
        from OFS.Uninstalled import broken_klasses
        from OFS.Uninstalled import broken_klasses_lock
        broken_klasses_lock.acquire()
        try:
            broken_klasses.clear()
            broken_klasses.update(self.broken_klasses_OLD)
        finally:
            broken_klasses_lock.release()

    def test_Broken_non_product_no_oid_yields_class_derived_from_Broken(self):
        from OFS.Uninstalled import Broken
        from OFS.Uninstalled import BrokenClass

        klass = Broken(self, None, ('some.python.module', 'MyClass'))

        self.failUnless(issubclass(klass, BrokenClass))
        self.assertEqual(klass.__name__, 'MyClass')
        self.assertEqual(klass.__module__, 'some.python.module')
        self.assertEqual(klass.product_name, 'unknown')

    def test_Broken_product_no_oid_yields_class_derived_from_Broken(self):
        from OFS.Uninstalled import Broken
        from OFS.Uninstalled import BrokenClass

        klass = Broken(self, None, ('Products.MyProduct.MyClass', 'MyClass'))

        self.failUnless(issubclass(klass, BrokenClass))
        self.assertEqual(klass.__name__, 'MyClass')
        self.assertEqual(klass.__module__, 'Products.MyProduct.MyClass')
        self.assertEqual(klass.product_name, 'MyProduct')

    def test_Broken_product_with_oid_yields_instance_derived_from_Broken(self):
        from OFS.Uninstalled import Broken
        from OFS.Uninstalled import BrokenClass
        OID = '\x01' * 8

        inst = Broken(self, OID, ('Products.MyProduct.MyClass', 'MyClass'))

        self.failUnless(isinstance(inst, BrokenClass))
        self.failUnless(inst._p_jar is self)
        self.assertEqual(inst._p_oid, OID)

        klass = inst.__class__
        self.assertEqual(klass.__name__, 'MyClass')
        self.assertEqual(klass.__module__, 'Products.MyProduct.MyClass')
        self.assertEqual(klass.product_name, 'MyProduct')

    def test_Broken_instance___getstate___raises_useful_exception(self):
        # see http://www.zope.org/Collectors/Zope/2157
        from OFS.Uninstalled import Broken
        from OFS.Uninstalled import BrokenClass
        OID = '\x01' * 8

        inst = Broken(self, OID, ('Products.MyProduct.MyClass', 'MyClass'))

        try:
            dict = inst.__getstate__()
        except SystemError, e:
            self.failUnless('MyClass' in str(e), str(e))
        else:
            self.fail("'__getstate__' didn't raise SystemError!")

    def test_Broken_instance___getattr___allows_persistence_attrs(self):
        from OFS.Uninstalled import Broken
        from OFS.Uninstalled import BrokenClass
        OID = '\x01' * 8
        PERSISTENCE_ATTRS = ["_p_changed",
                             "_p_jar",
                             "_p_mtime",
                             "_p_oid",
                             "_p_serial",
                             "_p_state",
                            ]
        PERSISTENCE_METHODS = ["_p_deactivate",
                               "_p_activate",
                               "_p_invalidate",
                               "_p_getattr",
                               "_p_setattr",
                               "_p_delattr",
                              ]

        inst = Broken(self, OID, ('Products.MyProduct.MyClass', 'MyClass'))

        for attr_name in PERSISTENCE_ATTRS:
            attr = getattr(inst, attr_name) # doesn't raise

        for meth_name in PERSISTENCE_METHODS:
            meth = getattr(inst, meth_name) # doesn't raise

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite(TestsOfBroken))
    return suite

def main():
    unittest.main(defaultTest='test_suite')

if __name__ == '__main__':
    main()

