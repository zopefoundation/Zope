##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Unit tests of makequest.
"""

import unittest

from Acquisition import Implicit
from Testing.makerequest import makerequest
from OFS.SimpleItem import SimpleItem

class MakerequestTests(unittest.TestCase):

    def test_makerequest(self):
        # The argument must support acquisition.
        self.assertRaises(AttributeError, makerequest, object())
        # After the call, it will have a REQUEST attribute.
        item = Implicit()
        self.assertFalse(hasattr(item, 'REQUEST'))
        item = makerequest(item)
        self.assertTrue(hasattr(item, 'REQUEST'))
    
    def test_dont_break_getPhysicalPath(self):
        # see http://www.zope.org/Collectors/Zope/2057.  If you want
        # to call getPhysicalPath() on the wrapped object, be sure
        # that it provides a non-recursive getPhysicalPath().
        class FakeRoot(SimpleItem):
            def getPhysicalPath(self):
                return ('foo',)
        item = FakeRoot()
        self.assertEqual(item.getPhysicalPath(),
                         makerequest(item).getPhysicalPath())

    def test_stdout(self):
        # You can pass a stdout arg and it's used by the response.
        import cStringIO
        out = cStringIO.StringIO()
        item = makerequest(SimpleItem(), stdout=out)
        item.REQUEST.RESPONSE.write('aaa')
        out.seek(0)
        written = out.read()
        self.assertTrue(written.startswith('Status: 200 OK\r\n'))
        self.assertTrue(written.endswith('\naaa'))

    def test_environ(self):
        # You can pass an environ argument to use in the request.
        environ = {'foofoo': 'barbar'}
        item = makerequest(SimpleItem(), environ=environ)
        self.assertEqual(item.REQUEST.environ['foofoo'], 'barbar')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MakerequestTests))
    return suite
