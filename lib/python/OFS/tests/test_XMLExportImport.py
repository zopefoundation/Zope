##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors. All Rights Reserved.
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
import tempfile
import transaction
from StringIO import StringIO

_LONG_DTML = '\n'.join([('<dtml-var foo%d' % x) for x in xrange(1000)])

class XMLExportImportTests(unittest.TestCase):

    def _makeJarAndRoot(self):
        import ZODB
        from OFS.Folder import Folder
        from ZODB.DemoStorage import DemoStorage

        CACHESIZE = 5  # something tiny
        LOOPCOUNT = CACHESIZE * 10
        storage = DemoStorage("Test")
        db = ZODB.DB(storage, cache_size=CACHESIZE)
        connection = db.open()
        root = connection.root()
        app = Folder('app')
        root['app'] = app

        return connection, app

    def test_export_import_as_string_idempotent(self):
        from OFS.DTMLMethod import DTMLMethod
        from OFS.XMLExportImport import exportXML
        from OFS.XMLExportImport import importXML

        connection, app = self._makeJarAndRoot()
        dm = DTMLMethod('test')
        dm.munge(_LONG_DTML)
        app._setObject('test', dm)
        transaction.savepoint(optimistic=True) # need an OID!
        oid = dm._p_oid

        stream = StringIO()

        data = exportXML(connection, oid, stream)
        stream.seek(0)

        newobj = importXML(connection, stream)
        self.failUnless(isinstance(newobj, DTMLMethod))
        self.assertEqual(newobj.read(), dm.read())

    def test_export_import_as_file_idempotent(self):
        from OFS.DTMLMethod import DTMLMethod
        from OFS.XMLExportImport import exportXML
        from OFS.XMLExportImport import importXML

        connection, app = self._makeJarAndRoot()
        dm = DTMLMethod('test')
        dm.munge(_LONG_DTML)
        app._setObject('test', dm)
        transaction.savepoint(optimistic=True) # need an OID!
        oid = dm._p_oid

        ostream = tempfile.NamedTemporaryFile(suffix='.xml')
        try:
            data = exportXML(connection, oid, ostream)
            ostream.flush()
            newobj = importXML(connection, ostream.name)
        finally:
            ostream.close()

        self.failUnless(isinstance(newobj, DTMLMethod))
        self.assertEqual(newobj.read(), dm.read())

    def test_OFS_ObjectManager__importObjectFromFile_xml(self):
        from OFS.DTMLMethod import DTMLMethod
        from OFS.Folder import Folder
        from OFS.XMLExportImport import exportXML

        connection, app = self._makeJarAndRoot()
        dm = DTMLMethod('test')
        dm._setId('test')
        dm.munge(_LONG_DTML)
        app._setObject('test', dm)
        sub = Folder('sub')
        app._setObject('sub', sub)
        transaction.savepoint(optimistic=True) # need an OID!
        oid = dm._p_oid
        sub = app._getOb('sub')

        ostream = tempfile.NamedTemporaryFile(suffix='.xml')
        try:
            data = exportXML(connection, oid, ostream)
            ostream.flush()
            sub._importObjectFromFile(ostream.name, 0, 0)
        finally:
            ostream.close()

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(XMLExportImportTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
