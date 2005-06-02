import unittest


class TestRoleManager(unittest.TestCase):

    def test_z3interfaces(self):
        from AccessControl.interfaces import IRoleManager
        from AccessControl.Role import RoleManager
        from zope.interface.verify import verifyClass

        verifyClass(IRoleManager, RoleManager)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestRoleManager),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
