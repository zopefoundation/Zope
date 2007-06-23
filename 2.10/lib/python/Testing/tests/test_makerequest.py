##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors. All Rights Reserved.
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

$Id$
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
        self.failIf(hasattr(item, 'REQUEST'))
        item = makerequest(item)
        self.failUnless(hasattr(item, 'REQUEST'))
    
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
        self.failUnless(written.startswith('Status: 200 OK\n'))
        self.failUnless(written.endswith('\naaa'))

    def test_environ(self):
        # You can pass an environ argument to use in the request.
        environ = {'foofoo': 'barbar'}
        item = makerequest(SimpleItem(), environ=environ)
        self.assertEqual(item.REQUEST.environ['foofoo'], 'barbar')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MakerequestTests))
    return suite

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
