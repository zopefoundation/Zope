import unittest

import transaction
import Zope2
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from OFS.Folder import Folder
from OFS.metaconfigure import setDeprecatedManageAddDelete
from OFS.SimpleItem import SimpleItem
from Testing.makerequest import makerequest
from Zope2.App import zcml
from zope.testing import cleanup


Zope2.startup_wsgi()


class EventLogger:
    def __init__(self):
        self.reset()

    def reset(self):
        self._called = []

    def trace(self, ob, event):
        self._called.append((ob.getId(), event))

    def called(self):
        return self._called


eventlog = EventLogger()


class TestItem(SimpleItem):
    def __init__(self, id):
        self.id = id

    def manage_afterAdd(self, item, container):
        eventlog.trace(self, 'manage_afterAdd')

    def manage_afterClone(self, item):
        eventlog.trace(self, 'manage_afterClone')

    def manage_beforeDelete(self, item, container):
        eventlog.trace(self, 'manage_beforeDelete')


class TestFolder(Folder):
    def __init__(self, id):
        self.id = id

    def _verifyObjectPaste(self, object, validate_src=1):
        pass  # Always allow

    def manage_afterAdd(self, item, container):
        eventlog.trace(self, 'manage_afterAdd')
        Folder.manage_afterAdd(self, item, container)

    def manage_afterClone(self, item):
        eventlog.trace(self, 'manage_afterClone')
        Folder.manage_afterClone(self, item)

    def manage_beforeDelete(self, item, container):
        eventlog.trace(self, 'manage_beforeDelete')
        Folder.manage_beforeDelete(self, item, container)


class HookLayer:

    @classmethod
    def setUp(cls):
        cleanup.cleanUp()
        zcml.load_site(force=True)
        setDeprecatedManageAddDelete(TestItem)
        setDeprecatedManageAddDelete(TestFolder)

    @classmethod
    def tearDown(cls):
        cleanup.cleanUp()


class HookTest(unittest.TestCase):

    layer = HookLayer

    def setUp(self):
        self.app = makerequest(Zope2.app())
        try:
            uf = self.app.acl_users
            uf._doAddUser('manager', 'secret', ['Manager'], [])
            user = uf.getUserById('manager').__of__(uf)
            newSecurityManager(None, user)
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        noSecurityManager()
        transaction.abort()
        self.app._p_jar.close()


class TestCopySupport(HookTest):
    '''Tests the order in which add/clone/del hooks are called'''

    def setUp(self):
        HookTest.setUp(self)
        # A folder that does not verify pastes
        self.app._setObject('folder', TestFolder('folder'))
        self.folder = getattr(self.app, 'folder')
        # The subfolder we are going to copy/move to
        self.folder._setObject('subfolder', TestFolder('subfolder'))
        self.subfolder = getattr(self.folder, 'subfolder')
        # The document we are going to copy/move
        self.folder._setObject('mydoc', TestItem('mydoc'))
        # Need _p_jars
        transaction.savepoint(1)
        # Reset event log
        eventlog.reset()

    def test_1_Clone(self):
        # Test clone
        self.subfolder.manage_clone(self.folder.mydoc, 'mydoc')
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'manage_afterAdd'),
             ('mydoc', 'manage_afterClone')]
        )

    def test_2_CopyPaste(self):
        # Test copy/paste
        cb = self.folder.manage_copyObjects(['mydoc'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'manage_afterAdd'),
             ('mydoc', 'manage_afterClone')]
        )

    def test_3_CutPaste(self):
        # Test cut/paste
        cb = self.folder.manage_cutObjects(['mydoc'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'manage_beforeDelete'),
             ('mydoc', 'manage_afterAdd')]
        )

    def test_4_Rename(self):
        # Test rename
        self.folder.manage_renameObject('mydoc', 'yourdoc')
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'manage_beforeDelete'),
             ('yourdoc', 'manage_afterAdd')]
        )


class TestCopySupportSublocation(HookTest):
    '''Tests the order in which add/clone/del hooks are called'''

    def setUp(self):
        HookTest.setUp(self)
        # A folder that does not verify pastes
        self.app._setObject('folder', TestFolder('folder'))
        self.folder = getattr(self.app, 'folder')
        # The subfolder we are going to copy/move to
        self.folder._setObject('subfolder', TestFolder('subfolder'))
        self.subfolder = getattr(self.folder, 'subfolder')
        # The folder we are going to copy/move
        self.folder._setObject('myfolder', TestFolder('myfolder'))
        self.myfolder = getattr(self.folder, 'myfolder')
        # The "sublocation" inside our folder we are going to watch
        self.myfolder._setObject('mydoc', TestItem('mydoc'))
        # Need _p_jars
        transaction.savepoint(1)
        # Reset event log
        eventlog.reset()

    def test_1_Clone(self):
        # Test clone
        self.subfolder.manage_clone(self.folder.myfolder, 'myfolder')
        self.assertEqual(
            eventlog.called(),
            [('myfolder', 'manage_afterAdd'),
             ('mydoc', 'manage_afterAdd'),
             ('myfolder', 'manage_afterClone'),
             ('mydoc', 'manage_afterClone')]
        )

    def test_2_CopyPaste(self):
        # Test copy/paste
        cb = self.folder.manage_copyObjects(['myfolder'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(
            eventlog.called(),
            [('myfolder', 'manage_afterAdd'),
             ('mydoc', 'manage_afterAdd'),
             ('myfolder', 'manage_afterClone'),
             ('mydoc', 'manage_afterClone')]
        )

    def test_3_CutPaste(self):
        # Test cut/paste
        cb = self.folder.manage_cutObjects(['myfolder'])
        self.subfolder.manage_pasteObjects(cb)
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'manage_beforeDelete'),
             ('myfolder', 'manage_beforeDelete'),
             ('myfolder', 'manage_afterAdd'),
             ('mydoc', 'manage_afterAdd')]
        )

    def test_4_Rename(self):
        # Test rename
        self.folder.manage_renameObject('myfolder', 'yourfolder')
        self.assertEqual(
            eventlog.called(),
            [('mydoc', 'manage_beforeDelete'),
             ('myfolder', 'manage_beforeDelete'),
             ('yourfolder', 'manage_afterAdd'),
             ('mydoc', 'manage_afterAdd')]
        )
