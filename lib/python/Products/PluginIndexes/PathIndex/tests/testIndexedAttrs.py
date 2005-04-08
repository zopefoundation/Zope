#
# IndexedAttrs tests
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase


from Products.ZCatalog.ZCatalog import ZCatalog
from OFS.SimpleItem import SimpleItem


class Record:
    def __init__(self, **kw):
        self.__dict__.update(kw)

class Dummy(SimpleItem):
    def __init__(self, id):
        self.id = id
    def getCustomPath(self):
        return ('', 'custom', 'path')
    def getStringPath(self):
        return '/string/path'


class TestIndexedAttrs(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.catalog = ZCatalog('catalog')
        self.folder._setObject('dummy', Dummy('dummy'))
        self.dummy = self.folder.dummy
        self.physical_path = '/'.join(self.dummy.getPhysicalPath())
        self.custom_path = '/'.join(self.dummy.getCustomPath())
        self.string_path = self.dummy.getStringPath()

    def addIndex(self, id='path', extra=None):
        self.catalog.addIndex(id, 'PathIndex', extra)
        return self.catalog.Indexes[id]

    def testAddIndex(self):
        self.catalog.addIndex('path', 'PathIndex')
        try:
            self.catalog.Indexes['path']
        except KeyError:
            self.fail('Failed to create index')

    def testDefaultIndexedAttrs(self):
        # By default we don't have indexed_attrs at all
        idx = self.addIndex()
        self.failIf(hasattr(idx, 'indexed_attrs'))

    def testDefaultIndexSourceNames(self):
        # However, getIndexSourceName returns 'getPhysicalPath'
        idx = self.addIndex()
        self.assertEqual(idx.getIndexSourceNames(), ('getPhysicalPath',))

    def testDefaultIndexObject(self):
        # By default PathIndex indexes getPhysicalPath
        idx = self.addIndex()
        idx.index_object(123, self.dummy)
        self.assertEqual(idx.getEntryForObject(123), self.physical_path)

    def testDefaultSearchObject(self):
        # We can find the object in the catalog by physical path
        self.addIndex()
        self.catalog.catalog_object(self.dummy)
        self.assertEqual(len(self.catalog(path=self.physical_path)), 1)

    def testDefaultSearchDictSyntax(self):
        # PathIndex supports dictionary syntax for queries
        self.addIndex()
        self.catalog.catalog_object(self.dummy)
        self.assertEqual(len(self.catalog(path={'query': self.physical_path})), 1)

    def testExtraAsRecord(self):
        # 'extra' can be a record type object
        idx = self.addIndex(extra=Record(indexed_attrs='getCustomPath'))
        self.assertEqual(idx.indexed_attrs, ('getCustomPath',))

    def testExtraAsMapping(self):
        # or a dictionary
        idx = self.addIndex(extra={'indexed_attrs': 'getCustomPath'})
        self.assertEqual(idx.indexed_attrs, ('getCustomPath',))

    def testCustomIndexSourceNames(self):
        # getIndexSourceName returns the indexed_attrs
        idx = self.addIndex(extra={'indexed_attrs': 'getCustomPath'})
        self.assertEqual(idx.getIndexSourceNames(), ('getCustomPath',))

    def testCustomIndexObject(self):
        # PathIndex indexes getCustomPath
        idx = self.addIndex(extra={'indexed_attrs': 'getCustomPath'})
        idx.index_object(123, self.dummy)
        self.assertEqual(idx.getEntryForObject(123), self.custom_path)

    def testCustomSearchObject(self):
        # We can find the object in the catalog by custom path
        self.addIndex(extra={'indexed_attrs': 'getCustomPath'})
        self.catalog.catalog_object(self.dummy)
        self.assertEqual(len(self.catalog(path=self.custom_path)), 1)

    def testStringIndexObject(self):
        # PathIndex accepts a path as tuple or string
        idx = self.addIndex(extra={'indexed_attrs': 'getStringPath'})
        idx.index_object(123, self.dummy)
        self.assertEqual(idx.getEntryForObject(123), self.string_path)

    def testStringSearchObject(self):
        # And we can find the object in the catalog again
        self.addIndex(extra={'indexed_attrs': 'getStringPath'})
        self.catalog.catalog_object(self.dummy)
        self.assertEqual(len(self.catalog(path=self.string_path)), 1)

    def testIdIndexObject(self):
        # PathIndex prefers an attribute matching its id over getPhysicalPath
        idx = self.addIndex(id='getId')
        idx.index_object(123, self.dummy)
        self.assertEqual(idx.getEntryForObject(123), 'dummy')

    def testIdIndexObject(self):
        # Using indexed_attr overrides this behavior
        idx = self.addIndex(id='getId', extra={'indexed_attrs': 'getCustomPath'})
        idx.index_object(123, self.dummy)
        self.assertEqual(idx.getEntryForObject(123), self.custom_path)

    def testListIndexedAttr(self):
        # indexed_attrs can be a list
        idx = self.addIndex(id='getId', extra={'indexed_attrs': ['getCustomPath', 'foo']})
        # only the first attribute is used
        self.assertEqual(idx.getIndexSourceNames(), ('getCustomPath',))

    def testStringIndexedAttr(self):
        # indexed_attrs can also be a comma separated string
        idx = self.addIndex(id='getId', extra={'indexed_attrs': 'getCustomPath, foo'})
        # only the first attribute is used
        self.assertEqual(idx.getIndexSourceNames(), ('getCustomPath',))

    def testEmtpyListAttr(self):
        # Empty indexed_attrs falls back to defaults
        idx = self.addIndex(extra={'indexed_attrs': []})
        self.assertEqual(idx.getIndexSourceNames(), ('getPhysicalPath',))

    def testEmtpyStringAttr(self):
        # Empty indexed_attrs falls back to defaults
        idx = self.addIndex(extra={'indexed_attrs': ''})
        self.assertEqual(idx.getIndexSourceNames(), ('getPhysicalPath',))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestIndexedAttrs))
    return suite

if __name__ == '__main__':
    framework()
