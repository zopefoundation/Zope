import unittest


class TestUndoSupport(unittest.TestCase):

    def test_interfaces(self):
        from App.interfaces import IUndoSupport
        from App.Undo import UndoSupport
        from zope.interface.verify import verifyClass

        verifyClass(IUndoSupport, UndoSupport)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestUndoSupport),
        ))
