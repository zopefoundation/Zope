"""Acquisition unit tests."""

import unittest, string
from operator import truth
from Acquisition import Implicit
from Acquisition import Explicit

class AcquisitionTests (unittest.TestCase):

    def testImplicitTruthSemanticsDefault(self):
        """Check wrapper truth semantics against those of python objects
           without __len__ or __nonzero__ definitions."""

        class PyObject:
            # plain object, no __len__ or __nonzero__
            pass

        class AqObject(Implicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 1

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 1


    def testImplicitTruthSemanticsWithNonZero(self):
        """Check wrapper truth semantics against those of python objects
           with __nonzero__ defined."""

        class PyObject:
            def __nonzero__(self):
                return 0

        class AqObject(Implicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 0

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 0


        class PyObject:
            def __nonzero__(self):
                return 1

        class AqObject(Implicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 1

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 1


    def testImplicitTruthSemanticsWithLen(self):
        """Check wrapper truth semantics against those of python objects
           with __len__ defined."""

        class PyObject:
            def __len__(self):
                return 0

        class AqObject(Implicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 0

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 0


        class PyObject:
            def __len__(self):
                return 1

        class AqObject(Implicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 1

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 1


    def testImplicitTruthSemanticsWithNonZeroAndLen(self):
        """Check wrapper truth semantics against those of python objects
           with __nonzero__ and __len__ defined."""

        class PyObject:
            def __nonzero__(self):
                return 0

            def __len__(self):
                return 1

        class AqObject(Implicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 0
        assert len(object) == 1

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 0
        assert len(object) == 1


        class PyObject:
            def __nonzero__(self):
                return 1

            def __len__(self):
                return 0

        class AqObject(Implicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 1
        assert len(object) == 0

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 1
        assert len(object) == 0


    def testExplicitTruthSemanticsDefault(self):
        """Check wrapper truth semantics against those of python objects
           without __len__ or __nonzero__ definitions."""

        class PyObject:
            # plain object, no __len__ or __nonzero__
            pass

        class AqObject(Explicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 1

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 1


    def testExplicitTruthSemanticsWithNonZero(self):
        """Check wrapper truth semantics against those of python objects
           with __nonzero__ defined."""

        class PyObject:
            def __nonzero__(self):
                return 0

        class AqObject(Explicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 0

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 0


        class PyObject:
            def __nonzero__(self):
                return 1

        class AqObject(Explicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 1

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 1


    def testExplicitTruthSemanticsWithLen(self):
        """Check wrapper truth semantics against those of python objects
           with __len__ defined."""

        class PyObject:
            def __len__(self):
                return 0

        class AqObject(Explicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 0

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 0


        class PyObject:
            def __len__(self):
                return 1

        class AqObject(Explicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 1

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 1


    def testExplicitTruthSemanticsWithNonZeroAndLen(self):
        """Check wrapper truth semantics against those of python objects
           with __nonzero__ and __len__ defined."""

        class PyObject:
            def __nonzero__(self):
                return 0

            def __len__(self):
                return 1

        class AqObject(Explicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 0
        assert len(object) == 1

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 0
        assert len(object) == 1


        class PyObject:
            def __nonzero__(self):
                return 1

            def __len__(self):
                return 0

        class AqObject(Explicit, PyObject):
            pass

        object = PyObject()
        assert truth(object) == 1
        assert len(object) == 0

        parent = AqObject()
        parent.object = AqObject()
        object = parent.object
        assert truth(object) == 1
        assert len(object) == 0








def test_suite():
    return unittest.makeSuite(AcquisitionTests)
