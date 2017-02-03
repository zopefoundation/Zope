# -*- coding: iso8859-1 -*-
##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
import os
import tempfile
import transaction
from StringIO import StringIO

try:
    here = os.path.dirname(os.path.abspath(__file__))
except:
    here = os.path.dirname(os.path.abspath(sys.argv[0]))

imagedata = os.path.join(here, 'test.gif')
xmldata = os.path.join(here, 'export.xml')

_LONG_DTML = ''.join([('<dtml-var foo%d' % x) for x in xrange(1000)])

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
        self.assertTrue(isinstance(newobj, DTMLMethod))
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

        handle, path = tempfile.mkstemp(suffix='.xml')
        try:
            ostream = os.fdopen(handle,'wb')
            data = exportXML(connection, oid, ostream)
            ostream.close()
            newobj = importXML(connection, path)
            self.assertTrue(isinstance(newobj, DTMLMethod))
            self.assertEqual(newobj.read(), dm.read())
        finally:
            # if this operaiton fails with a 'Permission Denied' error,
            # then comment it out as it's probably masking a failure in
            # the block above.
            os.remove(path)


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

        handle, path = tempfile.mkstemp(suffix='.xml')
        try:
            ostream = os.fdopen(handle,'wb')
            data = exportXML(connection, oid, ostream)
            ostream.close()
            sub._importObjectFromFile(path, 0, 0)
        finally:
            # if this operaiton fails with a 'Permission Denied' error,
            # then comment it out as it's probably masking a failure in
            # the block above.
            os.remove(path)

    def test_exportXML(self):
        from OFS.Folder import Folder
        from OFS.Image import Image
        from OFS.XMLExportImport import exportXML

        connection, app = self._makeJarAndRoot()
        data = open(imagedata, 'rb')

        sub = Folder('sub')
        app._setObject('sub', sub)
        img = Image('image', '', data, 'image/gif')
        sub._setObject('image', img)
        img._setProperty('prop1', 3.14159265359, 'float')
        img._setProperty('prop2', 1, 'int')
        img._setProperty('prop3', 2L**31-1, 'long')
        img._setProperty('prop4', 'xxx', 'string')
        img._setProperty('prop5', ['xxx', 'zzz'], 'lines')
        img._setProperty('prop6', u'xxx', 'unicode')
        img._setProperty('prop7', [u'xxx', u'zzz'], 'ulines')
        img._setProperty('prop8', '<&>', 'string')
        img._setProperty('prop9', u'<&>', 'unicode')
        img._setProperty('prop10', '<]]>', 'string')
        img._setProperty('prop11', u'<]]>', 'unicode')
        img._setProperty('prop12', u'£', 'unicode')
        transaction.savepoint(optimistic=True)
        oid = sub._p_oid

        handle, path = tempfile.mkstemp(suffix='.xml')
        try:
            ostream = os.fdopen(handle,'wb')
            data = exportXML(connection, oid, ostream)
            ostream.close()
        finally:
            os.remove(path)

    def test_importXML(self):
        from OFS.XMLExportImport import importXML

        connection, app = self._makeJarAndRoot()
        newobj = importXML(connection, xmldata)
        img = newobj._getOb('image')
        data = open(imagedata, 'rb').read()

        self.assertEqual(img.data, data)
        self.assertEqual(repr(img.getProperty('prop1')),
                         repr(3.14159265359))
        self.assertEqual(repr(img.getProperty('prop2')),
                         repr(1))
        self.assertEqual(repr(img.getProperty('prop3')),
                         repr(2L**31-1))
        self.assertEqual(repr(img.getProperty('prop4')),
                         repr('xxx'))
        self.assertEqual(repr(img.getProperty('prop5')),
                         repr(('xxx', 'zzz')))
        self.assertEqual(repr(img.getProperty('prop6')),
                         repr(u'xxx'))
        self.assertEqual(repr(img.getProperty('prop7')),
                         repr((u'xxx', u'zzz')))
        self.assertEqual(repr(img.getProperty('prop8')),
                         repr('<&>'))
        self.assertEqual(repr(img.getProperty('prop9')),
                         repr(u'<&>'))
        self.assertEqual(repr(img.getProperty('prop10')),
                         repr('<]]>'))
        self.assertEqual(repr(img.getProperty('prop11')),
                         repr(u'<]]>'))
        self.assertEqual(repr(img.getProperty('prop12')),
                         repr(u'£'))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(XMLExportImportTests),
        ))
