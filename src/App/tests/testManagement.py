import unittest


class TestNavigation(unittest.TestCase):

    def test_z3interfaces(self):
        from App.interfaces import INavigation
        from App.Management import Navigation
        from zope.interface.verify import verifyClass

        verifyClass(INavigation, Navigation)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestNavigation),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
