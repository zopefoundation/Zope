##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unittests for ZCatalog
"""

import unittest
import Zope2
Zope2.startup()

from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl import Unauthorized
from Acquisition import Implicit
import ExtensionClass
import OFS.Application
from OFS.Folder import Folder as OFS_Folder
from ZODB.DB import DB
from ZODB.DemoStorage import DemoStorage
import transaction


def createDatabase():
    # Create a DemoStorage and put an Application in it
    db = DB(DemoStorage())
    conn = db.open()
    root = conn.root()
    app = OFS.Application.Application()
    root['Application'] = app
    transaction.commit()
    return app

app = createDatabase()


class Folder(OFS_Folder):
    def __init__(self, id):
        self._setId(id)
        OFS_Folder.__init__(self)


class zdummy(ExtensionClass.Base):
    def __init__(self, num):
        self.num = num

    def title(self):
        return '%d' % self.num


class zdummyFalse(zdummy):

    def __nonzero__(self):
        return False


class dummyLenFail(zdummy):

    def __init__(self, num, fail):
        zdummy.__init__(self, num)
        self.fail = fail

    def __len__(self):
        self.fail("__len__() was called")


class dummyNonzeroFail(zdummy):
    def __init__(self, num, fail):
        zdummy.__init__(self, num)
        self.fail = fail

    def __nonzero__(self):
        self.fail("__nonzero__() was called")


class FakeTraversalError(KeyError):
    """fake traversal exception for testing"""


class fakeparent(Implicit):

    # fake parent mapping unrestrictedTraverse to
    # catalog.resolve_path as simulated by TestZCatalog

    marker = object()

    def __init__(self, d):
        self.d = d

    def unrestrictedTraverse(self, path, default=marker):
        result = self.d.get(path, default)
        if result is self.marker:
            raise FakeTraversalError(path)
        return result


class PickySecurityManager:

    def __init__(self, badnames=[]):
        self.badnames = badnames

    def validateValue(self, value):
        return 1

    def validate(self, accessed, container, name, value):
        if name not in self.badnames:
            return 1
        raise Unauthorized(name)


class ZCatalogBase(object):

    def _makeOne(self):
        from Products.ZCatalog.ZCatalog import ZCatalog
        return ZCatalog('Catalog')

    def setUp(self):
        self._catalog = self._makeOne()

    def tearDown(self):
        self._catalog = None


class TestZCatalog(ZCatalogBase, unittest.TestCase):

    def setUp(self):
        ZCatalogBase.setUp(self)
        self._catalog.resolve_path = self._resolve_num
        self._catalog.addIndex('title', 'KeywordIndex')
        self._catalog.addColumn('title')

        self.upper = 10
        self.d = {}
        for x in range(0, self.upper):
            # make uid a string of the number
            ob = zdummy(x)
            self.d[str(x)] = ob
            self._catalog.catalog_object(ob, str(x))

    def _resolve_num(self, num):
        return self.d[num]

    def test_interfaces(self):
        from Products.ZCatalog.interfaces import IZCatalog
        from Products.ZCatalog.ZCatalog import ZCatalog
        from zope.interface.verify import verifyClass

        verifyClass(IZCatalog, ZCatalog)

    def test_len(self):
        self.assertEquals(len(self._catalog), self.upper)

    # manage_edit
    # manage_subbingToggle

    def testBooleanEvalOn_manage_catalogObject(self):
        self.d['11'] = dummyLenFail(11, self.fail)
        self.d['12'] = dummyNonzeroFail(12, self.fail)
        # create a fake response that doesn't bomb on manage_catalogObject()
        class myresponse:
            def redirect(self, url):
                pass
        # this next call should not fail
        self._catalog.manage_catalogObject(None, myresponse(),
                                           'URL1', urls=('11', '12'))

    # manage_uncatalogObject
    # manage_catalogReindex

    def testBooleanEvalOn_refreshCatalog_getobject(self):
        # wrap catalog under the fake parent providing unrestrictedTraverse()
        catalog = self._catalog.__of__(fakeparent(self.d))
        # replace entries to test refreshCatalog
        self.d['0'] = dummyLenFail(0, self.fail)
        self.d['1'] = dummyNonzeroFail(1, self.fail)
        # this next call should not fail
        catalog.refreshCatalog()

        for uid in ('0', '1'):
            rid = catalog.getrid(uid)
            # neither should these
            catalog.getobject(rid)

    # manage_catalogClear
    # manage_catalogFoundItems
    # manage_addColumn
    # manage_delColumn
    # manage_addIndex
    # manage_delIndex
    # manage_clearIndex

    def testReindexIndexDoesntDoMetadata(self):
        self.d['0'].num = 9999
        self._catalog.reindexIndex('title', {})
        data = self._catalog.getMetadataForUID('0')
        self.assertEqual(data['title'], '0')

    def testReindexIndexesFalse(self):
        # setup
        false_id = self.upper + 1
        ob = zdummyFalse(false_id)
        self.d[str(false_id)] = ob
        self._catalog.catalog_object(ob, str(false_id))
        # test, object evaluates to false; there was bug which caused the
        # object to be removed from index
        ob.num = 9999
        self._catalog.reindexIndex('title', {})
        result = self._catalog(title='9999')
        self.assertEquals(1, len(result))

    # manage_reindexIndex
    # catalog_object
    # uncatalog_object
    # uniqueValuesFor
    # getpath
    # getrid

    def test_getobject_traversal(self):
        # getobject doesn't mask TraversalErrors and doesn't delegate to
        # resolve_url
        # wrap catalog under the fake parent providing unrestrictedTraverse()
        catalog = self._catalog.__of__(fakeparent(self.d))
        # make resolve_url fail if ZCatalog falls back on it
        def resolve_url(path, REQUEST):
            self.fail(".resolve_url() should not be called by .getobject()")
        catalog.resolve_url = resolve_url

        # traversal should work at first
        rid0 = catalog.getrid('0')
        # lets set it up so the traversal fails
        del self.d['0']
        self.assertRaises(FakeTraversalError,
                          catalog.getobject, rid0, REQUEST=object())
        # and if there is a None at the traversal point, that's where it
        # should return
        self.d['0'] = None
        self.assertEquals(catalog.getobject(rid0), None)

    def testGetMetadataForUID(self):
        testNum = str(self.upper - 3) # as good as any..
        data = self._catalog.getMetadataForUID(testNum)
        self.assertEqual(data['title'], testNum)

    def testGetIndexDataForUID(self):
        testNum = str(self.upper - 3)
        data = self._catalog.getIndexDataForUID(testNum)
        self.assertEqual(data['title'][0], testNum)

    def testUpdateMetadata(self):
        self._catalog.catalog_object(zdummy(1), '1')
        data = self._catalog.getMetadataForUID('1')
        self.assertEqual(data['title'], '1')
        self._catalog.catalog_object(zdummy(2), '1', update_metadata=0)
        data = self._catalog.getMetadataForUID('1')
        self.assertEqual(data['title'], '1')
        self._catalog.catalog_object(zdummy(2), '1', update_metadata=1)
        data = self._catalog.getMetadataForUID('1')
        self.assertEqual(data['title'], '2')
        # update_metadata defaults to true, test that here
        self._catalog.catalog_object(zdummy(1), '1')
        data = self._catalog.getMetadataForUID('1')
        self.assertEqual(data['title'], '1')

    # getMetadataForRID
    # getIndexDataForRID
    # schema
    # indexes
    # index_objects
    # getIndexObjects
    # _searchable_arguments
    # _searchable_result_columns

    def testSearchResults(self):
        query = {'title': ['5', '6', '7']}
        sr = self._catalog.searchResults(query)
        self.assertEqual(len(sr), 3)

    def testCall(self):
        query = {'title': ['5', '6', '7']}
        sr = self._catalog(query)
        self.assertEqual(len(sr), 3)

    def testSearch(self):
        query = {'title': ['5', '6', '7']}
        sr = self._catalog.search(query)
        self.assertEqual(len(sr), 3)

    # resolve_url
    # resolve_path
    # manage_normalize_paths
    # manage_setProgress
    # _getProgressThreshold


class TestAddDelColumnIndex(ZCatalogBase, unittest.TestCase):

    def testAddIndex(self):
        self._catalog.addIndex('id', 'FieldIndex')
        self.assert_('id' in self._catalog.indexes())

    def testDelIndex(self):
        self._catalog.addIndex('title', 'FieldIndex')
        self.assert_('title' in self._catalog.indexes())
        self._catalog.delIndex('title')
        self.assert_('title' not in self._catalog.indexes())

    def testClearIndex(self):
        self._catalog.addIndex('title', 'FieldIndex')
        idx = self._catalog._catalog.getIndex('title')
        for x in range(10):
            ob = zdummy(x)
            self._catalog.catalog_object(ob, str(x))
        self.assertEquals(len(idx), 10)
        self._catalog.clearIndex('title')
        self.assertEquals(len(idx), 0)

    def testAddColumn(self):
        self._catalog.addColumn('num', default_value=0)
        self.assert_('num' in self._catalog.schema())

    def testDelColumn(self):
        self._catalog.addColumn('title')
        self._catalog.delColumn('title')
        self.assert_('title' not in self._catalog.schema())


class TestZCatalogGetObject(ZCatalogBase, unittest.TestCase):
    # Test what objects are returned by brain.getObject()

    def setUp(self):
        ZCatalogBase.setUp(self)
        self._catalog.addIndex('id', 'FieldIndex')
        root = Folder('')
        root.getPhysicalRoot = lambda: root
        self.root = root
        self.root.catalog = self._catalog

    def tearDown(self):
        ZCatalogBase.tearDown(self)
        noSecurityManager()

    def test_getObject_found(self):
        # Check normal traversal
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults({'id': 'ob'})[0]
        self.assertEqual(brain.getPath(), '/ob')
        self.assertEqual(brain.getObject().getId(), 'ob')

    def test_getObject_missing_raises_NotFound(self):
        # Check that if the object is missing we raise
        from zExceptions import NotFound
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults({'id': 'ob'})[0]
        del root.ob
        self.assertRaises((NotFound, AttributeError, KeyError),
                          brain.getObject)

    def test_getObject_restricted_raises_Unauthorized(self):
        # Check that if the object's security does not allow traversal,
        # None is returned
        root = self.root
        catalog = root.catalog
        root.fold = Folder('fold')
        root.fold.ob = Folder('ob')
        catalog.catalog_object(root.fold.ob)
        brain = catalog.searchResults({'id': 'ob'})[0]
        # allow all accesses
        pickySecurityManager = PickySecurityManager()
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain.getObject().getId(), 'ob')
        # disallow just 'ob' access
        pickySecurityManager = PickySecurityManager(['ob'])
        setSecurityManager(pickySecurityManager)
        self.assertRaises(Unauthorized, brain.getObject)
        # disallow just 'fold' access
        pickySecurityManager = PickySecurityManager(['fold'])
        setSecurityManager(pickySecurityManager)
        ob = brain.getObject()
        self.assertFalse(ob is None)
        self.assertEqual(ob.getId(), 'ob')

    # Now test _unrestrictedGetObject

    def test_unrestrictedGetObject_found(self):
        # Check normal traversal
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults({'id': 'ob'})[0]
        self.assertEqual(brain.getPath(), '/ob')
        self.assertEqual(brain._unrestrictedGetObject().getId(), 'ob')

    def test_unrestrictedGetObject_restricted(self):
        # Check that if the object's security does not allow traversal,
        # it's still is returned
        root = self.root
        catalog = root.catalog
        root.fold = Folder('fold')
        root.fold.ob = Folder('ob')
        catalog.catalog_object(root.fold.ob)
        brain = catalog.searchResults({'id': 'ob'})[0]
        # allow all accesses
        pickySecurityManager = PickySecurityManager()
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain._unrestrictedGetObject().getId(), 'ob')
        # disallow just 'ob' access
        pickySecurityManager = PickySecurityManager(['ob'])
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain._unrestrictedGetObject().getId(), 'ob')
        # disallow just 'fold' access
        pickySecurityManager = PickySecurityManager(['fold'])
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain._unrestrictedGetObject().getId(), 'ob')

    def test_unrestrictedGetObject_missing_raises_NotFound(self):
        # Check that if the object is missing we raise
        from zExceptions import NotFound
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults({'id': 'ob'})[0]
        del root.ob
        self.assertRaises((NotFound, AttributeError, KeyError),
                          brain._unrestrictedGetObject)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZCatalog))
    suite.addTest(unittest.makeSuite(TestAddDelColumnIndex))
    suite.addTest(unittest.makeSuite(TestZCatalogGetObject))
    return suite
