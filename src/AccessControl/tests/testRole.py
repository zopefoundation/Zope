import unittest


class TestRoleManager(unittest.TestCase):

    def test_interfaces(self):
        from AccessControl.interfaces import IRoleManager
        from AccessControl.Role import BaseRoleManager
        from zope.interface.verify import verifyClass

        verifyClass(IRoleManager, BaseRoleManager)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestRoleManager),
        ))
