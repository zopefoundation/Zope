##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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

import unittest

import Acquisition
import ExtensionClass
from ZPublisher.mapply import mapply


class MapplyTests(unittest.TestCase):

    def testMethod(self):

        def compute(a, b, c=4):
            return '%d%d%d' % (a, b, c)

        values = {'a': 2, 'b': 3, 'c': 5}
        v = mapply(compute, (), values)
        self.assertEqual(v, '235')

        v = mapply(compute, (7,), values)
        self.assertEqual(v, '735')

    def testClass(self):
        values = {'a': 2, 'b': 3, 'c': 5}

        class c:
            a = 3

            def __call__(self, b, c=4):
                return '%d%d%d' % (self.a, b, c)

            compute = __call__

        cc = c()
        v = mapply(cc, (), values)
        self.assertEqual(v, '335')

        del values['c']
        v = mapply(cc.compute, (), values)
        self.assertEqual(v, '334')

    def testObjectWithCall(self):
        # Make sure that the __call__ of an object can also be another
        # callable object.  mapply will do the right thing and
        # recursive look for __call__ attributes until it finds an
        # actual method:

        class CallableObject:
            def __call__(self, a, b):
                return f'{a}{b}'

        class Container:
            __call__ = CallableObject()

        v = mapply(Container(), (8, 3), {})
        self.assertEqual(v, '83')

    def testUncallableObject(self):
        # Normally, mapply will raise a TypeError if it encounters an
        # uncallable object (e.g. an interger ;))
        self.assertRaises(TypeError, mapply, 2, (), {})

        # Unless you enable the 'maybe' flag, in which case it will
        # only maybe call the object
        self.assertEqual(mapply(2, (), {}, maybe=True), 2)

    def testNoCallButAcquisition(self):
        # Make sure that mapply won't erroneously walk up the
        # Acquisition chain when looking for __call__ attributes:

        class Root(ExtensionClass.Base):
            def __call__(self):
                return 'The root __call__'

        class NoCallButAcquisition(Acquisition.Implicit):
            pass

        ob = NoCallButAcquisition().__of__(Root())
        self.assertRaises(TypeError, mapply, ob, (), {})

    def testFunctionWithSignature(self):
        from inspect import Parameter
        from inspect import Signature

        def f(*args, **kw):
            return args, kw

        f.__signature__ = Signature(
            (Parameter("a", Parameter.POSITIONAL_OR_KEYWORD),
             Parameter("b", Parameter.POSITIONAL_OR_KEYWORD, default="b")))

        self.assertEqual(mapply(f, ("a",), {}), (("a", "b"), {}))
        self.assertEqual(mapply(f, (), {"a": "A", "b": "B"}), (("A", "B"), {}))
