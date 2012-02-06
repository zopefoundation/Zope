##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import unittest
from OFS.SimpleItem import SimpleItem
from Testing.ZopeTestCase import base


class ToBreak(SimpleItem):
    pass


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

        self.assertTrue(issubclass(klass, BrokenClass))
        self.assertEqual(klass.__name__, 'MyClass')
        self.assertEqual(klass.__module__, 'some.python.module')
        self.assertEqual(klass.product_name, 'unknown')

    def test_Broken_product_no_oid_yields_class_derived_from_Broken(self):
        from OFS.Uninstalled import Broken
        from OFS.Uninstalled import BrokenClass

        klass = Broken(self, None, ('Products.MyProduct.MyClass', 'MyClass'))

        self.assertTrue(issubclass(klass, BrokenClass))
        self.assertEqual(klass.__name__, 'MyClass')
        self.assertEqual(klass.__module__, 'Products.MyProduct.MyClass')
        self.assertEqual(klass.product_name, 'MyProduct')

    def test_Broken_product_with_oid_yields_instance_derived_from_Broken(self):
        from OFS.Uninstalled import Broken
        from OFS.Uninstalled import BrokenClass
        OID = '\x01' * 8

        inst = Broken(self, OID, ('Products.MyProduct.MyClass', 'MyClass'))

        self.assertTrue(isinstance(inst, BrokenClass))
        self.assertTrue(inst._p_jar is self)
        self.assertEqual(inst._p_oid, OID)

        klass = inst.__class__
        self.assertEqual(klass.__name__, 'MyClass')
        self.assertEqual(klass.__module__, 'Products.MyProduct.MyClass')
        self.assertEqual(klass.product_name, 'MyProduct')

    def test_Broken_instance___getattr___allows_persistence_attrs(self):
        from OFS.Uninstalled import Broken
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


class TestsIntegratedBroken(base.TestCase):

    def test_Broken_instance___getstate___gives_access_to_its_state(self):
        from Acquisition import aq_base
        from OFS.Uninstalled import BrokenClass
        from OFS.tests import test_Uninstalled
        import transaction

        # store an instance
        tr = ToBreak()
        tr.id = 'tr'
        self.app._setObject('tr', tr)
        # commit to allow access in another connection
        transaction.commit()
        # remove class from namespace to ensure broken object
        del test_Uninstalled.ToBreak
        # get new connection that will give access to broken object
        app = base.app()
        inst = aq_base(app.tr)
        self.assertTrue(isinstance(inst, BrokenClass))
        state = inst.__getstate__()
        self.assertEqual(state, {'id': 'tr'})

        # cleanup
        app.manage_delObjects('tr')
        transaction.commit()
        # check that object is not left over
        app = base.app()
        self.assertFalse('tr' in app.objectIds())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestsOfBroken))
    suite.addTest(unittest.makeSuite(TestsIntegratedBroken))
    return suite


def main():
    unittest.main(defaultTest='test_suite')
