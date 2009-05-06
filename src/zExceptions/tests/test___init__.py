import unittest

class Test_convertExceptionType(unittest.TestCase):

    def _callFUT(self, name):
        from zExceptions import convertExceptionType
        return convertExceptionType(name)

    def test_name_in___builtins__(self):
        self.failUnless(self._callFUT('SyntaxError') is SyntaxError)

    def test_name_in___builtins___not_an_exception_returns_None(self):
        self.failUnless(self._callFUT('unichr') is None)

    def test_name_in_zExceptions(self):
        from zExceptions import Redirect
        self.failUnless(self._callFUT('Redirect') is Redirect)

    def test_name_in_zExceptions_not_an_exception_returns_None(self):
        self.failUnless(self._callFUT('convertExceptionType') is None)

class Test_upgradeException(unittest.TestCase):

    def _callFUT(self, t, v):
        from zExceptions import upgradeException
        return upgradeException(t, v)

    def test_non_string(self):
        t, v = self._callFUT(SyntaxError, 'TEST')
        self.assertEqual(t, SyntaxError)
        self.assertEqual(v, 'TEST')

    def test_string_in___builtins__(self):
        t, v = self._callFUT('SyntaxError', 'TEST')
        self.assertEqual(t, SyntaxError)
        self.assertEqual(v, 'TEST')

    def test_string_in_zExceptions(self):
        from zExceptions import Redirect
        t, v = self._callFUT('Redirect', 'http://example.com/')
        self.assertEqual(t, Redirect)
        self.assertEqual(v, 'http://example.com/')

    def test_string_miss_returns_InternalError(self):
        from zExceptions import InternalError
        t, v = self._callFUT('Nonesuch', 'TEST')
        self.assertEqual(t, InternalError)
        self.assertEqual(v, ('Nonesuch', 'TEST'))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test_convertExceptionType),
        unittest.makeSuite(Test_upgradeException),
        ))
