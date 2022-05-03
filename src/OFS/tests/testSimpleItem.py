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
        class REQUEST:
            class RESPONSE:
                handle_errors = True
        item = self._makeOne()

        def _raise_during_standard_error_message(*args, **kw):
            raise ZeroDivisionError('testing')
        item.standard_error_message = _raise_during_standard_error_message
        try:
            item.raise_standardErrorMessage(
                error_type=OverflowError,
                error_value=OverflowError('simple'),
                REQUEST=REQUEST(),
            )
        except Exception:
            import sys
            self.assertEqual(sys.exc_info()[0], OverflowError)
            value = sys.exc_info()[1]
            self.assertTrue(value.message.startswith("'simple'"))
            self.assertTrue('full details: testing' in value.message)

    def test_raise_StandardErrorMessage_TaintedString_errorValue(self):
        from AccessControl.tainted import TaintedString

        class REQUEST:
            class RESPONSE:
                handle_errors = True
        item = self._makeOne()

        def _raise_during_standard_error_message(*args, **kw):
            raise ZeroDivisionError('testing')
        item.standard_error_message = _raise_during_standard_error_message
        try:
            item.raise_standardErrorMessage(
                error_type=OverflowError,
                error_value=OverflowError(TaintedString('<simple>')),
                REQUEST=REQUEST(),
            )
        except Exception:
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

    def test_id(self):
        from OFS.SimpleItem import Item_w__name__
        itm = Item_w__name__()
        # fall back to inherited `id`
        self.assertEqual(itm.id, "")
        itm.id = "id"
        self.assertEqual(itm.id, "id")
        del itm.id
        itm._setId("name")
        self.assertEqual(itm.id, "name")


class TestSimpleItem(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.SimpleItem import SimpleItem
        return SimpleItem

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
        from OFS.interfaces import ISimpleItem
        from zope.interface.verify import verifyClass

        verifyClass(ISimpleItem, self._getTargetClass())

    def test_title_or_id_nonascii(self):
        unencoded_id = '\xfc\xe4\xee\xe9\xdf_id'
        unencoded_title = '\xfc\xe4\xee\xe9\xdf Title'
        item = self._makeOne()

        item.id = unencoded_id
        self.assertEqual(item.title_or_id(), unencoded_id)

        item.title = unencoded_title
        self.assertEqual(item.title_or_id(), unencoded_title)

    def test_title_and_id_nonascii(self):
        unencoded_id = '\xfc\xe4\xee\xe9\xdf_id'
        encoded_id = unencoded_id.encode('UTF-8')
        unencoded_title = '\xfc\xe4\xee\xe9\xdf Title'
        item = self._makeOne()

        item.id = unencoded_id
        self.assertEqual(item.title_and_id(), unencoded_id)

        item.title = unencoded_title
        self.assertIn(unencoded_id, item.title_and_id())
        self.assertIn(unencoded_title, item.title_and_id())

        # Now mix encoded and unencoded. The combination is a native string:
        item.id = encoded_id
        self.assertIn(unencoded_id, item.title_and_id())
        self.assertIn(unencoded_title, item.title_and_id())

    def test_standard_error_message_is_called(self):
        from zExceptions import BadRequest

        # handle_errors should default to True. It is a flag used for
        # functional doctests. See ZPublisher/Test.py and
        # ZPublisher/Publish.py.
        class REQUEST:
            class RESPONSE:
                handle_errors = True

        class StandardErrorMessage:
            def __init__(self):
                self.kw = {}

            def __call__(self, **kw):
                self.kw.clear()
                self.kw.update(kw)

        item = self._makeOne()
        item.standard_error_message = sem = StandardErrorMessage()

        try:
            raise BadRequest("1")
        except Exception:
            item.raise_standardErrorMessage(client=item,
                                            REQUEST=REQUEST())

        self.assertEqual(sem.kw.get('error_type'), 'BadRequest')
