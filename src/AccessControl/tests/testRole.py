import unittest


class TestRoleManager(unittest.TestCase):

    def test_interfaces(self):
        from AccessControl.interfaces import IRoleManager
        from AccessControl.rolemanager import RoleManager
        from zope.interface.verify import verifyClass

        verifyClass(IRoleManager, RoleManager)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestRoleManager),
        ))
