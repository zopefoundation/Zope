import unittest


class TestItem(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.SimpleItem import Item
        return Item

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_conforms_to_IItem(self):
        from OFS.interfaces import IItem
        from zope.interface.verify import verifyClass

        verifyClass(IItem, self._getTargetClass())

    def test_conforms_to_IManageable(self):
        from OFS.interfaces import IManageable
        from zope.interface.verify import verifyClass

        verifyClass(IManageable, self._getTargetClass())

    def test_raise_StandardErrorMessage_str_errorValue(self):
        class REQUEST(object):
            class RESPONSE(object):
                handle_errors = True
        item = self._makeOne()
        def _raise_during_standard_error_message(*args, **kw):
            raise ZeroDivisionError('testing')
        item.standard_error_message = _raise_during_standard_error_message
        try:
            item.raise_standardErrorMessage(
                            error_type=OverflowError,
                            error_value='simple',
                            REQUEST=REQUEST(),
                            )
        except:
            import sys
            self.assertEqual(sys.exc_info()[0], OverflowError)
            value = sys.exc_info()[1]
            self.assertTrue(value.message.startswith("'simple'"))
            self.assertTrue('full details: testing' in value.message)

    def test_raise_StandardErrorMessage_TaintedString_errorValue(self):
        from AccessControl.tainted import TaintedString
        class REQUEST(object):
            class RESPONSE(object):
                handle_errors = True
        item = self._makeOne()
        def _raise_during_standard_error_message(*args, **kw):
            raise ZeroDivisionError('testing')
        item.standard_error_message = _raise_during_standard_error_message
        try:
            item.raise_standardErrorMessage(
                            error_type=OverflowError,
                            error_value=TaintedString('<simple>'),
                            REQUEST=REQUEST(),
                            )
        except:
            import sys
            self.assertEqual(sys.exc_info()[0], OverflowError)
            value = sys.exc_info()[1]
            self.assertFalse('<' in value.message)


class TestItem_w__name__(unittest.TestCase):

    def test_interfaces(self):
        from OFS.interfaces import IItemWithName
        from OFS.SimpleItem import Item_w__name__
        from zope.interface.verify import verifyClass

        verifyClass(IItemWithName, Item_w__name__)


class TestSimpleItem(unittest.TestCase):

    def test_interfaces(self):
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
