##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
"""

Revision information:
$Id: testExternalMethod.py,v 1.3 2002/04/23 13:04:20 jim Exp $
"""

import math, os
from unittest import TestCase, TestSuite, main, makeSuite
import ZODB # dead goat
import Products.ExternalMethod.tests
from Products.ExternalMethod.ExternalMethod import ExternalMethod


class Test(TestCase):

    def setUp(self):
        self._old = __builtins__.__dict__.get('INSTANCE_HOME')
        __builtins__.INSTANCE_HOME = os.path.split(
            Products.ExternalMethod.tests.__file__)[0]

    def tearDown(self):
        if self._old is None:
            del __builtins__.INSTANCE_HOME
        else:
            __builtins__.INSTANCE_HOME = self._old

    def testStorage(self):
        em1 = ExternalMethod('em', 'test method', 'Test', 'testf')
        self.assertEqual(em1(4), math.sqrt(4))
        state = em1.__getstate__()
        em2 = ExternalMethod.__basicnew__()
        em2.__setstate__(state)
        self.assertEqual(em2(9), math.sqrt(9))
        self.failIf(state.has_key('func_defaults'))

    def test_mapply(self):
        from ZPublisher.mapply import mapply
        
        em1 = ExternalMethod('em', 'test method', 'Test', 'testf')
        self.assertEqual(mapply(em1, (), {'arg1': 4}), math.sqrt(4))
        state = em1.__getstate__()
        em2 = ExternalMethod.__basicnew__()
        em2.__setstate__(state)
        self.assertEqual(mapply(em1, (), {'arg1': 9}), math.sqrt(9))
        
        

def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))


def package_home(globals_dict):
    __name__=globals_dict['__name__']
    m=sys.modules[__name__]
    if hasattr(m,'__path__'):
        r=m.__path__[0]
    elif "." in __name__:
        r=sys.modules[__name__[:rfind(__name__,'.')]].__path__[0]
    else:
        r=__name__
    return os.path.join(os.getcwd(), r)


if __name__=='__main__':
    main(defaultTest='test_suite')
