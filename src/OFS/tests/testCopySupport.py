import io
import unittest

import transaction
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import Implicit
from Acquisition import aq_base
from OFS.Application import Application
from OFS.Folder import manage_addFolder
from OFS.Image import manage_addFile
from Testing.makerequest import makerequest


ADD_IMAGES_AND_FILES = 'Add images and files'
FILE_META_TYPES = ({
    'name': 'File',
    'action': 'manage_addFile',
    'permission': ADD_IMAGES_AND_FILES
}, )


class UnitTestSecurityPolicy:
    """Stub out the existing security policy for unit testing purposes.
    """

    #   Standard SecurityPolicy interface
    def validate(
        self,
        accessed=None,
        container=None,
        name=None,
        value=None,
        context=None,
        roles=None,
        *args,
        **kw
    ):
        return 1

    def checkPermission(self, permission, object, context):
        return 1


class UnitTestUser(Implicit):
    """Stubbed out manager for unit testing purposes.
    """

    def getId(self):
        return 'unit_tester'

    getUserName = getId

    def allowed(self, object, object_roles=None):
        return 1


def makeConnection():
    import ZODB
    from ZODB.DemoStorage import DemoStorage

    s = DemoStorage()
    return ZODB.DB(s).open()


class CopySupportTestBase(unittest.TestCase):

    def _initFolders(self):
        self.connection = makeConnection()
        try:
            r = self.connection.root()
            a = Application()
            r['Application'] = a
            self.root = a
            responseOut = self.responseOut = io.BytesIO()
            self.app = makerequest(self.root, stdout=responseOut)
            manage_addFolder(self.app, 'folder1')
            manage_addFolder(self.app, 'folder2')
            folder1 = getattr(self.app, 'folder1')

            manage_addFile(
                folder1, 'file', file=b'', content_type='text/plain')

            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one. We use a subtransaction, which means we can rollback
            # later and pretend we didn't touch the ZODB.
            transaction.commit()
        except Exception:
            transaction.abort()
            self.connection.close()
            raise
        transaction.begin()

        return self.app._getOb('folder1'), self.app._getOb('folder2')

    def _cleanApp(self):
        transaction.abort()
        self.app._p_jar.sync()
        self.connection.close()
        del self.app
        del self.responseOut
        del self.root
        del self.connection


class TestCopySupport(CopySupportTestBase):

    def setUp(self):
        folder1, folder2 = self._initFolders()
        folder1.all_meta_types = folder2.all_meta_types = FILE_META_TYPES

        self.folder1 = folder1
        self.folder2 = folder2

        self.policy = UnitTestSecurityPolicy()
        self.oldPolicy = SecurityManager.setSecurityPolicy(self.policy)
        newSecurityManager(None, UnitTestUser().__of__(self.root))

    def tearDown(self):
        noSecurityManager()
        SecurityManager.setSecurityPolicy(self.oldPolicy)
        del self.oldPolicy
        del self.policy
        del self.folder2
        del self.folder1

        self._cleanApp()

    def test_interfaces(self):
        from OFS.CopySupport import CopyContainer
        from OFS.CopySupport import CopySource
        from OFS.interfaces import ICopyContainer
        from OFS.interfaces import ICopySource
        from zope.interface.verify import verifyClass

        verifyClass(ICopyContainer, CopyContainer)
        verifyClass(ICopySource, CopySource)

    def testRename(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.folder1.manage_renameObject(id='file', new_id='filex')
        self.assertFalse('file' in self.folder1.objectIds())
        self.assertTrue('filex' in self.folder1.objectIds())

    def testCopy(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertFalse('file' in self.folder2.objectIds())
        cookie = self.folder1.manage_copyObjects(ids=('file',))
        self.folder2.manage_pasteObjects(cookie)
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertTrue('file' in self.folder2.objectIds())

    def testCut(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertFalse('file' in self.folder2.objectIds())
        cookie = self.folder1.manage_cutObjects(ids=('file',))
        self.folder2.manage_pasteObjects(cookie)
        self.assertFalse('file' in self.folder1.objectIds())
        self.assertTrue('file' in self.folder2.objectIds())

    def testCopyNewObject(self):
        self.assertFalse('newfile' in self.folder1.objectIds())
        manage_addFile(self.folder1, 'newfile',
                       file=b'', content_type='text/plain')
        cookie = self.folder1.manage_copyObjects(ids=('newfile',))
        self.folder2.manage_pasteObjects(cookie)
        self.assertTrue('newfile' in self.folder1.objectIds())
        self.assertTrue('newfile' in self.folder2.objectIds())

    def testPasteSingleNotSameID(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertFalse('file' in self.folder2.objectIds())
        cookie = self.folder1.manage_copyObjects(ids=('file',))
        result = self.folder2.manage_pasteObjects(cookie)
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertTrue('file' in self.folder2.objectIds())
        self.assertTrue(result == [{'id': 'file', 'new_id': 'file'}])

    def testPasteSingleSameID(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertFalse('file' in self.folder2.objectIds())
        manage_addFile(self.folder2, 'file',
                       file=b'', content_type='text/plain')
        cookie = self.folder1.manage_copyObjects(ids=('file',))
        result = self.folder2.manage_pasteObjects(cookie)
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertTrue('file' in self.folder2.objectIds())
        self.assertTrue('copy_of_file' in self.folder2.objectIds())
        self.assertTrue(result == [{'id': 'file', 'new_id': 'copy_of_file'}])

    def testPasteSingleSameIDMultipleTimes(self):
        cookie = self.folder1.manage_copyObjects(ids=('file',))
        result = self.folder1.manage_pasteObjects(cookie)
        self.assertEqual(self.folder1.objectIds(), ['file', 'copy_of_file'])
        self.assertEqual(result, [{'id': 'file', 'new_id': 'copy_of_file'}])
        # make another copy of file
        cookie = self.folder1.manage_copyObjects(ids=('file',))
        result = self.folder1.manage_pasteObjects(cookie)
        self.assertEqual(self.folder1.objectIds(),
                         ['file', 'copy_of_file', 'copy2_of_file'])
        self.assertEqual(result, [{'id': 'file', 'new_id': 'copy2_of_file'}])
        # now copy the copy
        cookie = self.folder1.manage_copyObjects(ids=('copy_of_file',))
        result = self.folder1.manage_pasteObjects(cookie)
        self.assertEqual(self.folder1.objectIds(),
                         ['file', 'copy_of_file', 'copy2_of_file',
                         'copy3_of_file'])
        self.assertEqual(result, [{'id': 'copy_of_file',
                                   'new_id': 'copy3_of_file'}])
        # or copy another copy
        cookie = self.folder1.manage_copyObjects(ids=('copy2_of_file',))
        result = self.folder1.manage_pasteObjects(cookie)
        self.assertEqual(self.folder1.objectIds(),
                         ['file', 'copy_of_file', 'copy2_of_file',
                         'copy3_of_file', 'copy4_of_file'])
        self.assertEqual(result, [{'id': 'copy2_of_file',
                                   'new_id': 'copy4_of_file'}])

    def testPasteSpecialName(self):
        manage_addFile(self.folder1, 'copy_of_',
                       file=b'', content_type='text/plain')
        cookie = self.folder1.manage_copyObjects(ids=('copy_of_',))
        result = self.folder1.manage_pasteObjects(cookie)
        self.assertEqual(self.folder1.objectIds(),
                         ['file', 'copy_of_', 'copy2_of_'])
        self.assertEqual(result, [{'id': 'copy_of_', 'new_id': 'copy2_of_'}])

    def testPasteMultiNotSameID(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertFalse('file1' in self.folder1.objectIds())
        manage_addFile(self.folder1, 'file1',
                       file=b'', content_type='text/plain')
        self.assertFalse('file2' in self.folder1.objectIds())
        manage_addFile(self.folder1, 'file2',
                       file=b'', content_type='text/plain')
        self.assertFalse('file' in self.folder2.objectIds())
        self.assertFalse('file1' in self.folder2.objectIds())
        self.assertFalse('file2' in self.folder2.objectIds())
        cookie = self.folder1.manage_copyObjects(
            ids=('file', 'file1', 'file2',))
        result = self.folder2.manage_pasteObjects(cookie)
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertTrue('file1' in self.folder1.objectIds())
        self.assertTrue('file2' in self.folder1.objectIds())
        self.assertTrue('file' in self.folder2.objectIds())
        self.assertTrue('file1' in self.folder2.objectIds())
        self.assertTrue('file2' in self.folder2.objectIds())
        self.assertEqual(result, [
            {'id': 'file', 'new_id': 'file'},
            {'id': 'file1', 'new_id': 'file1'},
            {'id': 'file2', 'new_id': 'file2'},
        ])

    def testPasteMultiSameID(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertFalse('file1' in self.folder1.objectIds())
        manage_addFile(self.folder1, 'file1',
                       file=b'', content_type='text/plain')
        self.assertFalse('file2' in self.folder1.objectIds())
        manage_addFile(self.folder1, 'file2',
                       file=b'', content_type='text/plain')
        self.assertFalse('file' in self.folder2.objectIds())
        manage_addFile(self.folder2, 'file',
                       file=b'', content_type='text/plain')
        self.assertFalse('file1' in self.folder2.objectIds())
        manage_addFile(self.folder2, 'file1',
                       file=b'', content_type='text/plain')
        self.assertFalse('file2' in self.folder2.objectIds())
        manage_addFile(self.folder2, 'file2',
                       file=b'', content_type='text/plain')
        cookie = self.folder1.manage_copyObjects(
            ids=('file', 'file1', 'file2',))
        result = self.folder2.manage_pasteObjects(cookie)
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertTrue('file1' in self.folder1.objectIds())
        self.assertTrue('file2' in self.folder1.objectIds())
        self.assertTrue('file' in self.folder2.objectIds())
        self.assertTrue('file1' in self.folder2.objectIds())
        self.assertTrue('file2' in self.folder2.objectIds())
        self.assertTrue('copy_of_file' in self.folder2.objectIds())
        self.assertTrue('copy_of_file1' in self.folder2.objectIds())
        self.assertTrue('copy_of_file2' in self.folder2.objectIds())
        self.assertEqual(result, [
            {'id': 'file', 'new_id': 'copy_of_file'},
            {'id': 'file1', 'new_id': 'copy_of_file1'},
            {'id': 'file2', 'new_id': 'copy_of_file2'},
        ])

    def testPasteNoData(self):
        from OFS.CopySupport import CopyError
        with self.assertRaises(CopyError):
            self.folder1.manage_pasteObjects()

    def testPasteTooBigData(self):
        from OFS.CopySupport import CopyError
        from OFS.CopySupport import _cb_encode

        def make_data(lenght):
            return _cb_encode(
                (1, ['qwertzuiopasdfghjklyxcvbnm' for x in range(lenght)]))
        # Protect against DoS attack with too big data:
        with self.assertRaises(CopyError) as err:
            self.folder1.manage_pasteObjects(make_data(300))
        self.assertEqual('Clipboard Error', str(err.exception))
        # But not too much data is allowed:
        with self.assertRaises(CopyError) as err:
            self.folder1.manage_pasteObjects(make_data(250))
        self.assertEqual('Item Not Found', str(err.exception))

        # _pasteObjects allows to paste without restriction:
        with self.assertRaises(CopyError) as err:
            self.folder1._pasteObjects(make_data(3000))
        self.assertEqual('Item Not Found', str(err.exception))


class _SensitiveSecurityPolicy:

    def __init__(self, validate_lambda, checkPermission_lambda):
        self._lambdas = (validate_lambda, checkPermission_lambda)

    def validate(self, *args, **kw):
        from zExceptions import Unauthorized

        allowed = self._lambdas[0](*args, **kw)
        if not allowed:
            raise Unauthorized
        return 1

    def checkPermission(self, *args, **kw):
        return self._lambdas[1](*args, **kw)


class _AllowedUser(UnitTestUser):

    def __init__(self, allowed_lambda):
        self._lambdas = (allowed_lambda, )

    def allowed(self, object, object_roles=None):
        return self._lambdas[0](object, object_roles)


class TestCopySupportSecurity(CopySupportTestBase):

    _old_policy = None

    def setUp(self):
        self._scrubSecurity()

    def tearDown(self):

        self._scrubSecurity()
        self._cleanApp()

    def _scrubSecurity(self):

        noSecurityManager()

        if self._old_policy is not None:
            SecurityManager.setSecurityPolicy(self._old_policy)

    def _assertCopyErrorUnauth(self, callable, *args, **kw):

        import re

        from OFS.CopySupport import CopyError
        from zExceptions import Unauthorized

        ce_regex = kw.get('ce_regex')
        if ce_regex is not None:
            del kw['ce_regex']

        try:
            callable(*args, **kw)
        except CopyError as e:
            if ce_regex is not None:
                pattern = re.compile(ce_regex, re.DOTALL)
                if pattern.search(e.args[0]) is None:
                    self.fail("Paste failed; didn't match pattern:\n%s" % e)
            else:
                self.fail("Paste failed; no pattern:\n%s" % e)
        except Unauthorized:
            pass
        else:
            self.fail("Paste allowed unexpectedly.")

    def _initPolicyAndUser(self, a_lambda=None, v_lambda=None, c_lambda=None):
        def _promiscuous(*args, **kw):
            return 1

        if a_lambda is None:
            a_lambda = _promiscuous

        if v_lambda is None:
            v_lambda = _promiscuous

        if c_lambda is None:
            c_lambda = _promiscuous

        scp = _SensitiveSecurityPolicy(v_lambda, c_lambda)
        self._old_policy = SecurityManager.setSecurityPolicy(scp)

        newSecurityManager(None, _AllowedUser(a_lambda).__of__(self.root))

    def test_copy_baseline(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        self._initPolicyAndUser()

        self.assertTrue('file' in folder1.objectIds())
        self.assertFalse('file' in folder2.objectIds())

        cookie = folder1.manage_copyObjects(ids=('file', ))
        folder2.manage_pasteObjects(cookie)

        self.assertTrue('file' in folder1.objectIds())
        self.assertTrue('file' in folder2.objectIds())

    def test_copy_cant_read_source(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        a_file = folder1._getOb('file')

        def _validate(a, c, n, v, *args, **kw):
            return aq_base(v) is not aq_base(a_file)

        self._initPolicyAndUser(v_lambda=_validate)

        cookie = folder1.manage_copyObjects(ids=('file', ))
        self._assertCopyErrorUnauth(
            folder2.manage_pasteObjects,
            cookie,
            ce_regex='Insufficient privileges',
        )

    def test_copy_cant_create_target_metatype_not_supported(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = ()

        self._initPolicyAndUser()

        cookie = folder1.manage_copyObjects(ids=('file', ))
        self._assertCopyErrorUnauth(
            folder2.manage_pasteObjects,
            cookie,
            ce_regex='Not Supported',
        )

    def test_copy_cant_copy_invisible_items(self):
        # User can view folder1.
        # User cannot view private file in folder1.
        # When user copies folder1, the private file should not be copied,
        # because the user would get the Owner role on the copy,
        # and be able to view it anyway.
        from AccessControl.Permissions import add_folders
        from AccessControl.Permissions import view

        folder1, folder2 = self._initFolders()
        manage_addFile(folder1, 'private',
                       file=b'', content_type='text/plain')
        manage_addFile(folder1, 'public',
                       file=b'', content_type='text/plain')
        folder1.private.manage_permission(view, roles=(), acquire=0)
        folder2.manage_permission(add_folders, roles=('Anonymous',), acquire=1)

        copy_info = folder2.manage_pasteObjects(
            self.app.manage_copyObjects('folder1')
        )

        new_id = copy_info[0]['new_id']
        new_folder = folder2[new_id]
        # The private item should not be in the copy.
        self.assertTrue('private' not in new_folder.objectIds())
        # There is nothing wrong with copying the public item.
        self.assertTrue('public' in new_folder.objectIds())

    def test_move_baseline(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        self.assertTrue('file' in folder1.objectIds())
        self.assertFalse('file' in folder2.objectIds())

        self._initPolicyAndUser()

        cookie = folder1.manage_cutObjects(ids=('file', ))
        folder2.manage_pasteObjects(cookie)

        self.assertFalse('file' in folder1.objectIds())
        self.assertTrue('file' in folder2.objectIds())

    def test_move_cant_read_source(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        a_file = folder1._getOb('file')

        def _validate(a, c, n, v, *args, **kw):
            return aq_base(v) is not aq_base(a_file)

        self._initPolicyAndUser(v_lambda=_validate)

        cookie = folder1.manage_cutObjects(ids=('file', ))
        self._assertCopyErrorUnauth(
            folder2.manage_pasteObjects,
            cookie,
            ce_regex='Insufficient privileges',
        )

    def test_move_cant_create_target_metatype_not_supported(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = ()

        self._initPolicyAndUser()

        cookie = folder1.manage_cutObjects(ids=('file', ))
        self._assertCopyErrorUnauth(
            folder2.manage_pasteObjects,
            cookie,
            ce_regex='Not Supported',
        )

    def test_move_cant_create_target_metatype_not_allowed(self):
        folder1, folder2 = self._initFolders()
        folder2.all_meta_types = FILE_META_TYPES

        def _no_add_images_and_files(permission, object, context):
            return permission != ADD_IMAGES_AND_FILES

        self._initPolicyAndUser(c_lambda=_no_add_images_and_files)

        cookie = folder1.manage_cutObjects(ids=('file', ))
        self._assertCopyErrorUnauth(
            folder2.manage_pasteObjects,
            cookie,
            ce_regex='Insufficient privileges',
        )

    def test_move_cant_delete_source(self):
        from AccessControl.Permissions import delete_objects

        folder1, folder2 = self._initFolders()
        folder1.manage_permission(delete_objects, roles=(), acquire=0)
        folder2.all_meta_types = FILE_META_TYPES

        def _no_delete_objects(permission, object, context):
            return permission != delete_objects

        self._initPolicyAndUser(c_lambda=_no_delete_objects)

        cookie = folder1.manage_cutObjects(ids=('file', ))
        self._assertCopyErrorUnauth(
            folder2.manage_pasteObjects,
            cookie,
            ce_regex='Insufficient privileges',
        )
