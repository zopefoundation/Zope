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
        item = self._makeOne()
        def _raise_during_standard_error_message(*args, **kw):
            raise ZeroDivisionError('testing')
        item.standard_error_message = _raise_during_standard_error_message
        try:
            item.raise_standardErrorMessage(
                            error_type=OverflowError,
                            error_value='simple',
                            REQUEST={'dummy': ''},
                            )
        except:
            import sys
            self.assertEqual(sys.exc_info()[0], 'OverflowError')
            value = sys.exc_info()[1]
            self.failUnless(value.startswith("'simple'"))
            self.failUnless('full details: testing' in value)

    def test_raise_StandardErrorMessage_TaintedString_errorValue(self):
        from ZPublisher.TaintedString import TaintedString
        item = self._makeOne()
        def _raise_during_standard_error_message(*args, **kw):
            raise ZeroDivisionError('testing')
        item.standard_error_message = _raise_during_standard_error_message
        try:
            item.raise_standardErrorMessage(
                            error_type=OverflowError,
                            error_value=TaintedString('<simple>'),
                            REQUEST={'dummy': ''},
                            )
        except:
            import sys
            self.assertEqual(sys.exc_info()[0], 'OverflowError')
            value = sys.exc_info()[1]
            self.failIf('<' in value)


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
