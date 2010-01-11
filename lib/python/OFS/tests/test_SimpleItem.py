import unittest

class ItemTests(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.SimpleItem import Item
        return Item

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

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

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ItemTests),
        ))
