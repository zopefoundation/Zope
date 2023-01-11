##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests ZODB behavior in ZopeTestCase

Demonstrates that cut/copy/paste/clone/rename and import/export
work if a savepoint is made before performing the respective operation.
"""

import os
import tempfile
import unittest

from AccessControl.Permissions import add_documents_images_and_files
from AccessControl.Permissions import delete_objects
from OFS.SimpleItem import SimpleItem
from Testing import ZopeTestCase
from Testing.ZopeTestCase import layer
from Testing.ZopeTestCase import transaction
from Testing.ZopeTestCase import utils


folder_name = ZopeTestCase.folder_name
cutpaste_permissions = [add_documents_images_and_files, delete_objects]


def make_request_response(environ=None):
    from io import StringIO

    from ZPublisher.HTTPRequest import HTTPRequest
    from ZPublisher.HTTPResponse import HTTPResponse

    if environ is None:
        environ = {}

    stdout = StringIO()
    stdin = StringIO()
    resp = HTTPResponse(stdout=stdout)
    environ.setdefault('SERVER_NAME', 'foo')
    environ.setdefault('SERVER_PORT', '80')
    environ.setdefault('REQUEST_METHOD', 'GET')
    req = HTTPRequest(stdin, environ, resp)
    return req, resp


class DummyObject(SimpleItem):
    id = 'dummy'
    foo = None
    _v_foo = None
    _p_foo = None


class ZODBCompatLayer(layer.ZopeLite):

    @classmethod
    def setUp(cls):
        def setup(app):
            app._setObject('dummy1', DummyObject())
            app._setObject('dummy2', DummyObject())
            transaction.commit()
        utils.appcall(setup)

    @classmethod
    def tearDown(cls):
        def cleanup(app):
            app._delObject('dummy1')
            app._delObject('dummy2')
            transaction.commit()
        utils.appcall(cleanup)


class TestCopyPaste(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.setPermissions(cutpaste_permissions)
        self.folder.addDTMLMethod('doc', file='foo')
        # _p_oids are None until we create a savepoint
        self.assertEqual(self.folder._p_oid, None)
        transaction.savepoint(optimistic=True)
        self.assertNotEqual(self.folder._p_oid, None)

    def testCutPaste(self):
        cb = self.folder.manage_cutObjects(['doc'])
        self.folder.manage_pasteObjects(cb)
        self.assertTrue(hasattr(self.folder, 'doc'))
        self.assertFalse(hasattr(self.folder, 'copy_of_doc'))

    def testCopyPaste(self):
        cb = self.folder.manage_copyObjects(['doc'])
        self.folder.manage_pasteObjects(cb)
        self.assertTrue(hasattr(self.folder, 'doc'))
        self.assertTrue(hasattr(self.folder, 'copy_of_doc'))

    def testClone(self):
        self.folder.manage_clone(self.folder.doc, 'new_doc')
        self.assertTrue(hasattr(self.folder, 'doc'))
        self.assertTrue(hasattr(self.folder, 'new_doc'))

    def testRename(self):
        self.folder.manage_renameObjects(['doc'], ['new_doc'])
        self.assertFalse(hasattr(self.folder, 'doc'))
        self.assertTrue(hasattr(self.folder, 'new_doc'))


class TestImportExport(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.setupLocalEnvironment()
        self.folder.addDTMLMethod('doc', file='foo')
        # please note the usage of the turkish i
        self.folder.addDTMLMethod('ıq', file='foo')
        # _p_oids are None until we create a savepoint
        self.assertEqual(self.folder._p_oid, None)
        transaction.savepoint(optimistic=True)
        self.assertNotEqual(self.folder._p_oid, None)

    def testExport(self):
        self.folder.manage_exportObject('doc')
        self.assertTrue(os.path.exists(self.zexp_file))

    def testExportNonLatinFileNames(self):
        """Test compatibility of the export with unicode characters.

        Since Zope 4 also unicode ids can be used."""
        _, response = make_request_response()
        # please note the usage of a turkish `i`
        self.folder.manage_exportObject(
            'ıq', download=1, RESPONSE=response)

        found = False
        for header in response.listHeaders():
            if header[0] == 'Content-Disposition':
                # value needs to be `us-ascii` compatible
                assert header[1].encode("us-ascii")
                found = True
        self.assertTrue(found)

    def testImport(self):
        self.folder.manage_exportObject('doc')
        self.folder._delObject('doc')
        self.folder.manage_importObject('doc.zexp')
        self.assertTrue(hasattr(self.folder, 'doc'))

    # To make export and import happy, we have to provide a file-
    # system 'import' directory and adapt the configuration a bit:

    local_home = tempfile.gettempdir()
    import_dir = os.path.join(local_home, 'import')
    zexp_file = os.path.join(import_dir, 'doc.zexp')

    def setupLocalEnvironment(self):
        # Create the 'import' directory
        os.mkdir(self.import_dir)
        import App.config
        config = App.config.getConfiguration()
        self._ih = config.instancehome
        config.instancehome = self.local_home
        self._ch = config.clienthome
        config.clienthome = self.import_dir
        App.config.setConfiguration(config)

    def afterClear(self):
        # Remove external resources
        try:
            os.remove(self.zexp_file)
        except OSError:
            pass
        try:
            os.rmdir(self.import_dir)
        except OSError:
            pass
        import App.config
        config = App.config.getConfiguration()
        if hasattr(self, '_ih'):
            config.instancehome = self._ih
        if hasattr(self, '_ch'):
            config.clienthome = self._ch
        App.config.setConfiguration(config)


class TestAttributesOfCleanObjects(ZopeTestCase.ZopeTestCase):
    '''This testcase shows that _v_ and _p_ attributes are NOT bothered
       by transaction boundaries, if the respective object is otherwise
       left untouched (clean). This means that such variables will keep
       their values across tests.

       The only use case yet encountered in the wild is portal_memberdata's
       _v_temps attribute. Test authors are cautioned to watch out for
       occurrences of _v_ and _p_ attributes of objects that are not recreated
       for every test method execution, but preexist in the test ZODB.

       It is therefore deemed essential to initialize any _v_ and _p_
       attributes of such objects in afterSetup(), as otherwise test results
       will be distorted!

       Note that _v_ attributes used to be transactional in Zope < 2.6.

       This testcase exploits the fact that test methods are sorted by name.
    '''

    layer = ZODBCompatLayer

    def afterSetUp(self):
        self.dummy = self.app.dummy1  # See above

    def testNormal_01(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)
        self.dummy.foo = 'foo'

    def testNormal_02(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)
        self.dummy.foo = 'bar'

    def testNormal_03(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)

    def testPersistent_01(self):
        # _p_foo is initially None
        self.assertEqual(self.dummy._p_foo, None)
        self.dummy._p_foo = 'foo'

    def testPersistent_02(self):
        # _p_foo retains value assigned by previous test
        self.assertEqual(self.dummy._p_foo, 'foo')
        self.dummy._p_foo = 'bar'

    def testPersistent_03(self):
        # _p_foo retains value assigned by previous test
        self.assertEqual(self.dummy._p_foo, 'bar')

    def testVolatile_01(self):
        # _v_foo is initially None
        self.assertEqual(self.dummy._v_foo, None)
        self.dummy._v_foo = 'foo'

    def testVolatile_02(self):
        if hasattr(self.app._p_jar, 'register'):
            # _v_foo retains value assigned by previous test
            self.assertEqual(self.dummy._v_foo, 'foo')
        else:
            # XXX: _v_foo is transactional in Zope < 2.6
            self.assertEqual(self.dummy._v_foo, None)
        self.dummy._v_foo = 'bar'

    def testVolatile_03(self):
        if hasattr(self.app._p_jar, 'register'):
            # _v_foo retains value assigned by previous test
            self.assertEqual(self.dummy._v_foo, 'bar')
        else:
            # XXX: _v_foo is transactional in Zope < 2.6
            self.assertEqual(self.dummy._v_foo, None)


class TestAttributesOfDirtyObjects(ZopeTestCase.ZopeTestCase):
    '''This testcase shows that _v_ and _p_ attributes of dirty objects
       ARE removed on abort.

       This testcase exploits the fact that test methods are sorted by name.
    '''

    layer = ZODBCompatLayer

    def afterSetUp(self):
        self.dummy = self.app.dummy2  # See above
        self.dummy.touchme = 1  # Tag, you're dirty

    def testDirtyNormal_01(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)
        self.dummy.foo = 'foo'

    def testDirtyNormal_02(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)
        self.dummy.foo = 'bar'

    def testDirtyNormal_03(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)

    def testDirtyPersistent_01(self):
        # _p_foo is alwas None
        self.assertEqual(self.dummy._p_foo, None)
        self.dummy._p_foo = 'foo'

    def testDirtyPersistent_02(self):
        # _p_foo is alwas None
        self.assertEqual(self.dummy._p_foo, None)
        self.dummy._p_foo = 'bar'

    def testDirtyPersistent_03(self):
        # _p_foo is alwas None
        self.assertEqual(self.dummy._p_foo, None)

    def testDirtyVolatile_01(self):
        # _v_foo is always None
        self.assertEqual(self.dummy._v_foo, None)
        self.dummy._v_foo = 'foo'

    def testDirtyVolatile_02(self):
        # _v_foo is always None
        self.assertEqual(self.dummy._v_foo, None)
        self.dummy._v_foo = 'bar'

    def testDirtyVolatile_03(self):
        # _v_foo is always None
        self.assertEqual(self.dummy._v_foo, None)


class TestTransactionAbort(ZopeTestCase.ZopeTestCase):

    def _getfolder(self):
        return getattr(self.app, folder_name, None)

    def testTransactionAbort(self):
        folder = self._getfolder()
        self.assertTrue(folder is not None)
        self.assertTrue(folder._p_jar is None)
        transaction.savepoint()
        self.assertTrue(folder._p_jar is not None)
        transaction.abort()
        del folder
        folder = self._getfolder()
        self.assertTrue(folder is None)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(TestCopyPaste),
        unittest.defaultTestLoader.loadTestsFromTestCase(TestImportExport),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestAttributesOfCleanObjects),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestAttributesOfDirtyObjects),
        unittest.defaultTestLoader.loadTestsFromTestCase(TestTransactionAbort),
    ))
