import unittest

from OFS.Cache import CacheManager
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Products.Five.eventconfigure import setDeprecatedManageAddDelete

class DummyCacheManager(CacheManager, SimpleItem):
    def __init__(self, id, *args, **kw):
        self.id = id
setDeprecatedManageAddDelete(DummyCacheManager)

class CacheTests(unittest.TestCase):

    def test_managersExist(self):
        from OFS.Cache import managersExist
        from OFS.DTMLMethod import DTMLMethod
        root = Folder('root')
        root._setObject('root_cache' , DummyCacheManager('root_cache'))
        root._setObject('child', Folder('child'))
        root.child._setObject('child_cache', DummyCacheManager('child_cache'))
        root.child._setObject('child_content', DTMLMethod('child_content'))

        # To begin with, cache managers will be found correctly
        # using managersExist
        self.failUnless(managersExist(root.child.child_content))

        # Now we delete the cache in the child folder
        root.child.manage_delObjects(['child_cache'])

        # The parent_cache should still trigger managersExist
        self.failUnless(managersExist(root.child.child_content))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CacheTests))
    return suite
