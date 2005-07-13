import unittest


class TestItem(unittest.TestCase):

    def test_z3interfaces(self):
        from OFS.interfaces import IItem
        from OFS.interfaces import IManageable
        from OFS.SimpleItem import Item
        from zope.interface.verify import verifyClass

        verifyClass(IItem, Item)
        verifyClass(IManageable, Item)


class TestItem_w__name__(unittest.TestCase):

    def test_z3interfaces(self):
        from OFS.interfaces import IItemWithName
        from OFS.SimpleItem import Item_w__name__
        from zope.interface.verify import verifyClass

        verifyClass(IItemWithName, Item_w__name__)


class TestSimpleItem(unittest.TestCase):

    def test_z3interfaces(self):
        from OFS.interfaces import ISimpleItem
        from OFS.SimpleItem import SimpleItem
        from zope.interface.verify import verifyClass

        verifyClass(ISimpleItem, SimpleItem)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestItem),
        unittest.makeSuite(TestItem_w__name__),
        unittest.makeSuite(TestSimpleItem),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
