import unittest
import Testing
import Zope2
Zope2.startup()

import transaction

from Testing.makerequest import makerequest

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder


class HookCounter:
    '''Logs calls to old-school hooks'''

    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0
        self.afterAdd = [0]
        self.afterClone = [0]
        self.beforeDelete = [0]

    def manage_afterAdd(self, item, container):
        self.count = self.count + 1
        self.afterAdd.append(self.count)

    def manage_afterClone(self, item):
        self.count = self.count + 1
        self.afterClone.append(self.count)

    def manage_beforeDelete(self, item, container):
        self.count = self.count + 1
        self.beforeDelete.append(self.count)

    def order(self):
        return self.afterAdd[-1], self.afterClone[-1], self.beforeDelete[-1]


class TestItem(HookCounter, SimpleItem):

    def __init__(self, id):
        HookCounter.__init__(self)
        self.id = id


class TestFolder(HookCounter, Folder):

    def __init__(self, id):
        HookCounter.__init__(self)
        self.id = id

    def _verifyObjectPaste(self, object, validate_src=1):
        # Don't verify pastes as our test objects don't have
        # factory methods registered.
        pass

    def manage_afterAdd(self, item, container):
        HookCounter.manage_afterAdd(self, item, container)
        Folder.manage_afterAdd(self, item, container)

    def manage_afterClone(self, item):
        HookCounter.manage_afterClone(self, item)
        Folder.manage_afterClone(self, item)

    def manage_beforeDelete(self, item, container):
        HookCounter.manage_beforeDelete(self, item, container)
        Folder.manage_beforeDelete(self, item, container)


try:
    from Products.Five.eventconfigure import setDeprecatedManageAddDelete
    setDeprecatedManageAddDelete(HookCounter)
except ImportError:
    pass


class HookTest(unittest.TestCase):

    def setUp(self):
        self.app = makerequest(Zope2.app())
        try:
            uf = self.app.acl_users
            uf._doAddUser('manager', 'secret', ['Manager'], [])
            user = uf.getUserById('manager').__of__(uf)
            newSecurityManager(None, user)
        except:
            self.tearDown()
            raise

    def tearDown(self):
        noSecurityManager()
        transaction.abort()
        self.app._p_jar.close()


class TestCopySupport(HookTest):
    '''Tests the order in which the add/clone/del hooks are called'''

    def setUp(self):
        HookTest.setUp(self)
        # A folder
        self.app._setObject('folder', TestFolder('folder'))
        self.folder = self.app['folder']
        # A subfolder we are going to copy/move to
        self.folder._setObject('subfolder', TestFolder('subfolder'))
        self.subfolder = self.folder['subfolder']
        # A document we are going to copy/move
        self.folder._setObject('mydoc', TestItem('mydoc'))
        # Must have _p_jars
        transaction.savepoint(1)
        # Reset counters
        self.folder.mydoc.reset()

    def test_1_Clone(self):
        # Test clone
        self.subfolder.manage_clone(self.folder.mydoc, 'yourdoc')
        self.assertEqual(self.subfolder.yourdoc.order(), (1, 2, 0)) # add, clone

    def test_2_CopyPaste(self):
        # Test copy/paste
        cb = self.folder.manage_copyObjects(['mydoc'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(self.subfolder.mydoc.order(), (1, 2, 0))   # add, clone

    def test_3_CutPaste(self):
        # Test cut/paste
        cb = self.folder.manage_cutObjects(['mydoc'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(self.subfolder.mydoc.order(), (2, 0, 1))   # del, add

    def test_4_Rename(self):
        # Test rename
        self.folder.manage_renameObject('mydoc', 'yourdoc')
        self.assertEqual(self.folder.yourdoc.order(), (2, 0, 1))    # del, add

    def test_5_COPY(self):
        # Test webdav COPY
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = '%s/subfolder/mydoc' % self.folder.absolute_url()
        self.folder.mydoc.COPY(req, req.RESPONSE)
        self.assertEqual(req.RESPONSE.getStatus(), 201)
        self.assertEqual(self.subfolder.mydoc.order(), (1, 2, 0))   # add, clone

    def test_6_MOVE(self):
        # Test webdav MOVE
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = '%s/subfolder/mydoc' % self.folder.absolute_url()
        old = self.folder.mydoc
        self.folder.mydoc.MOVE(req, req.RESPONSE)
        self.assertEqual(req.RESPONSE.getStatus(), 201)
        self.assertEqual(old.order(), (0, 0, 1))                    # del
        self.assertEqual(self.subfolder.mydoc.order(), (1, 0, 0))   # add


class TestCopySupportSublocation(HookTest):
    '''Tests the order in which the add/clone/del hooks are called'''

    def setUp(self):
        HookTest.setUp(self)
        # A folder
        self.app._setObject('folder', TestFolder('folder'))
        self.folder = self.app['folder']
        # A subfolder we are going to copy/move to
        self.folder._setObject('subfolder', TestFolder('subfolder'))
        self.subfolder = self.folder['subfolder']
        # A folderish object we are going to copy/move
        self.folder._setObject('myfolder', TestFolder('myfolder'))
        self.myfolder = self.folder['myfolder']
        # A "sublocation" inside myfolder we are going to watch
        self.myfolder._setObject('mydoc', TestItem('mydoc'))
        # Must have _p_jars
        transaction.savepoint(1)
        # Reset counters
        self.myfolder.reset()
        self.myfolder.mydoc.reset()

    def test_1_Clone(self):
        # Test clone
        self.subfolder.manage_clone(self.folder.myfolder, 'yourfolder')
        self.assertEqual(self.subfolder.yourfolder.order(), (1, 2, 0))          # add, clone
        self.assertEqual(self.subfolder.yourfolder.mydoc.order(), (1, 2, 0))    # add, clone

    def test_2_CopyPaste(self):
        # Test copy/paste
        cb = self.folder.manage_copyObjects(['myfolder'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(self.subfolder.myfolder.order(), (1, 2, 0))            # add, clone
        self.assertEqual(self.subfolder.myfolder.mydoc.order(), (1, 2, 0))      # add, clone

    def test_3_CutPaste(self):
        # Test cut/paste
        cb = self.folder.manage_cutObjects(['myfolder'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(self.subfolder.myfolder.order(), (2, 0, 1))            # del, add
        self.assertEqual(self.subfolder.myfolder.mydoc.order(), (2, 0, 1))      # del, add

    def test_4_Rename(self):
        # Test rename
        self.folder.manage_renameObject('myfolder', 'yourfolder')
        self.assertEqual(self.folder.yourfolder.order(), (2, 0, 1))             # del, add
        self.assertEqual(self.folder.yourfolder.mydoc.order(), (2, 0, 1))       # del, add

    def test_5_COPY(self):
        # Test webdav COPY
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = '%s/subfolder/yourfolder' % self.folder.absolute_url()
        self.folder.myfolder.COPY(req, req.RESPONSE)
        self.assertEqual(req.RESPONSE.getStatus(), 201)
        self.assertEqual(self.subfolder.yourfolder.order(), (1, 2, 0))          # add, clone
        self.assertEqual(self.subfolder.yourfolder.mydoc.order(), (1, 2, 0))    # add, clone

    def test_6_MOVE(self):
        # Test webdav MOVE
        req = self.app.REQUEST
        req.environ['HTTP_DEPTH'] = 'infinity'
        req.environ['HTTP_DESTINATION'] = '%s/subfolder/yourfolder' % self.folder.absolute_url()
        oldfolder = self.folder.myfolder
        olddoc = self.folder.myfolder.mydoc
        self.folder.myfolder.MOVE(req, req.RESPONSE)
        self.assertEqual(req.RESPONSE.getStatus(), 201)
        self.assertEqual(oldfolder.order(), (0, 0, 1))                          # del
        self.assertEqual(self.subfolder.yourfolder.order(), (1, 0, 0))          # add
        self.assertEqual(olddoc.order(), (0, 0, 1))                             # del
        self.assertEqual(self.subfolder.yourfolder.mydoc.order(), (1, 0, 0))    # add


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCopySupport))
    suite.addTest(unittest.makeSuite(TestCopySupportSublocation))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

