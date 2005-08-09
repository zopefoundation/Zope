import unittest


class TestEtagSupport(unittest.TestCase):

    def test_z2interfaces(self):
        from Interface.Verify import verifyClass
        from webdav.EtagSupport import EtagBaseInterface
        from webdav.EtagSupport import EtagSupport

        verifyClass(EtagBaseInterface, EtagSupport)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestEtagSupport),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
