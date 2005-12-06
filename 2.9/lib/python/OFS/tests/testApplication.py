import unittest


class TestApplication(unittest.TestCase):

    def test_z3interfaces(self):
        from OFS.interfaces import IApplication
        from OFS.Application import Application
        from zope.interface.verify import verifyClass

        verifyClass(IApplication, Application)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestApplication),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
