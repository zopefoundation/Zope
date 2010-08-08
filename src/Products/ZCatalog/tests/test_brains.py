##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Unittests for Catalog brains
"""

import unittest

import Acquisition
from Acquisition import aq_base
from zExceptions import Unauthorized
from ZODB.POSException import ConflictError

_marker = object()


class Happy(Acquisition.Implicit):
    """Happy content"""

    def __init__(self, id):
        self.id = id

    def check(self):
        pass


class Secret(Happy):
    """Object that raises Unauthorized when accessed"""

    def check(self):
        raise Unauthorized


class Conflicter(Happy):
    """Object that raises ConflictError when accessed"""

    def check(self):
        raise ConflictError


class DummyRequest(object):

    def physicalPathToURL(self, path, relative=False):
        if not relative:
            path = 'http://superbad.com' + path
        return path


class DummyCatalog(Acquisition.Implicit):

    _objs = {'/happy': Happy('happy'),
             '/secret': Secret('secret'),
             '/conflicter': Conflicter('conflicter')}
    _paths = _objs.keys() + ['/zonked']
    _paths.sort()

    # This is sooooo ugly

    def unrestrictedTraverse(self, path, default=None):
        assert path in ['', ('', ), ['']], path
        return self

    def restrictedTraverse(self, path, default=_marker):
        if not path.startswith('/'):
            path = '/'+path
        try:
            ob = self._objs[path].__of__(self)
            ob.check()
            return ob
        except KeyError:
            if default is not _marker:
                return default
            raise

    def getpath(self, rid):
        return self._paths[rid]

    def getobject(self, rid):
        return self.restrictedTraverse(self._paths[rid])

    def resolve_url(self, path, REQUEST):
        # strip server part
        path = path[path.find('/', path.find('//') + 1):]
        return self.restrictedTraverse(path)


class ConflictingCatalog(DummyCatalog):

    def getpath(self, rid):
        raise ConflictError


class TestBrains(unittest.TestCase):

    def setUp(self):
        self.cat = DummyCatalog()
        self.cat.REQUEST = DummyRequest()

    def _makeBrain(self, rid):
        from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain

        class Brain(AbstractCatalogBrain):
            __record_schema__ = {'test_field': 0, 'data_record_id_': 1}

        return Brain(('test', rid)).__of__(self.cat)

    def testHasKey(self):
        b = self._makeBrain(1)
        self.assertTrue('test_field' in b)
        self.assertTrue('data_record_id_' in b)
        self.assertFalse('godel' in b)

    def testGetPath(self):
        b = [self._makeBrain(rid) for rid in range(3)]
        self.assertEqual(b[0].getPath(), '/conflicter')
        self.assertEqual(b[1].getPath(), '/happy')
        self.assertEqual(b[2].getPath(), '/secret')

    def testGetPathPropagatesConflictErrors(self):
        self.cat = ConflictingCatalog()
        b = self._makeBrain(0)
        self.assertRaises(ConflictError, b.getPath)

    def testGetURL(self):
        b = self._makeBrain(0)
        self.assertEqual(b.getURL(), 'http://superbad.com/conflicter')

    def testGetRID(self):
        b = self._makeBrain(42)
        self.assertEqual(b.getRID(), 42)

    def testGetObjectHappy(self):
        b = self._makeBrain(1)
        self.assertEqual(b.getPath(), '/happy')
        self.assertTrue(aq_base(b.getObject()) is
                        aq_base(self.cat.getobject(1)))

    def testGetObjectPropagatesConflictErrors(self):
        b = self._makeBrain(0)
        self.assertEqual(b.getPath(), '/conflicter')
        self.assertRaises(ConflictError, b.getObject)

    def testGetObjectRaisesUnauthorized(self):
        from zExceptions import Unauthorized
        b = self._makeBrain(2)
        self.assertEqual(b.getPath(), '/secret')
        self.assertRaises(Unauthorized, b.getObject)

    def testGetObjectRaisesNotFoundForMissing(self):
        from zExceptions import NotFound
        b = self._makeBrain(3)
        self.assertEqual(b.getPath(), '/zonked')
        self.assertRaises(KeyError, self.cat.getobject, 3)
        self.assertRaises((NotFound, AttributeError, KeyError), b.getObject)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBrains))
    return suite
