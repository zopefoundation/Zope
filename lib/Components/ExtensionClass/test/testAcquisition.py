"""Acquisition unit tests."""

from testExtensionClass import MagicMethodTests
from Acquisition import Implicit
from Acquisition import Explicit
from operator import truth
import unittest, string


class ImplicitWrapperTests(MagicMethodTests):
    """Implicit acquisition wrapper tests."""

    BaseClass = Implicit

    def fixup_inst(self, object):
        """Create a simple acquisition chain."""
        class GenericWrapper(self.BaseClass):
            pass
        parent = GenericWrapper()
        parent.object = object
        return parent.object


class ExplicitWrapperTests(ImplicitWrapperTests):
    """Explicit acquisition wrapper tests."""

    BaseClass = Explicit






def test_suite():
    suite_01 = unittest.makeSuite(ImplicitWrapperTests)
    suite_02 = unittest.makeSuite(ExplicitWrapperTests)
    return unittest.TestSuite((suite_01, suite_02))

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
