##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

Revision information:
$Id$
"""

import math
import os
import unittest

import ZODB # dead goat
import Products.ExternalMethod.tests
from Products.ExternalMethod.ExternalMethod import ExternalMethod
import App.config

class TestExternalMethod(unittest.TestCase):

    def setUp(self):
        self._old = App.config.getConfiguration()
        cfg = App.config.DefaultConfiguration()
        cfg.instancehome = os.path.dirname(
            Products.ExternalMethod.tests.__file__)
        App.config.setConfiguration(cfg)

    def tearDown(self):
        App.config.setConfiguration(self._old)

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
    return unittest.makeSuite(TestExternalMethod)


def package_home(globals_dict):
    __name__=globals_dict['__name__']
    m=sys.modules[__name__]
    if hasattr(m,'__path__'):
        r=m.__path__[0]
    elif "." in __name__:
        r=sys.modules[__name__.split('.',1)[0]].__path__[0]
    else:
        r=__name__
    return os.path.abspath(r)


if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
