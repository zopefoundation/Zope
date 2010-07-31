import unittest


class TestNavigation(unittest.TestCase):

    def test_interfaces(self):
        from App.interfaces import INavigation
        from App.Management import Navigation
        from zope.interface.verify import verifyClass

        verifyClass(INavigation, Navigation)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestNavigation),
        ))
