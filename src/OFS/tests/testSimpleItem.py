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

    def test_standard_error_message_is_called(self):
        from zExceptions import BadRequest
        from OFS.SimpleItem import SimpleItem

        # handle_errors should default to True. It is a flag used for
        # functional doctests. See ZPublisher/Test.py and
        # ZPublisher/Publish.py.
        class REQUEST(object):
            class RESPONSE(object):
                handle_errors = True

        class StandardErrorMessage(object):
            def __init__(self):
                self.kw = {}

            def __call__(self, **kw):
                self.kw.clear()
                self.kw.update(kw)

        item = SimpleItem()
        item.standard_error_message = sem = StandardErrorMessage()

        try:
            raise BadRequest("1")
        except:
            item.raise_standardErrorMessage(client=item,
                                            REQUEST=REQUEST())

        self.assertEquals(sem.kw.get('error_type'), 'BadRequest')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestItem),
        unittest.makeSuite(TestItem_w__name__),
        unittest.makeSuite(TestSimpleItem),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
