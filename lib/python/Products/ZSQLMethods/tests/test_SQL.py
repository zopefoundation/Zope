import unittest

class SQLMethodTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.ZSQLMethods.SQL import SQL
        return SQL

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_class_conforms_to_IWriteLock(self):
        from zope.interface.verify import verifyClass
        from webdav.interfaces import IWriteLock
        verifyClass(IWriteLock, self._getTargetClass())


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SQLMethodTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
