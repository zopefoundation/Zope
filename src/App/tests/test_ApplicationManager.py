import unittest

class FakeConnectionTests(unittest.TestCase):

    def _getTargetClass(self):
        from App.ApplicationManager import FakeConnection
        return FakeConnection

    def _makeOne(self, db, parent_jar):
        return self._getTargetClass()(db, parent_jar)

    def test_holds_db(self):
        db = object()
        parent_jar = object()
        fc = self._makeOne(db, parent_jar)
        self.failUnless(fc.db() is db)

class DatabaseChooserTests(unittest.TestCase):

    def setUp(self):
        import App.config
        self._old_config = App.config._config

    def tearDown(self):
        import App.config
        App.config._config = self._old_config

    def _getTargetClass(self):
        from App.ApplicationManager import DatabaseChooser
        return DatabaseChooser

    def _makeOne(self, id):
        return self._getTargetClass()(id)

    def _makeRoot(self):
        from ExtensionClass import Base
        class Root(Base):
            _p_jar = None
            def getPhysicalRoot(self):
                return self
        return Root()

    def _makeConfig(self, **kw):
        import App.config
        class DummyConfig:
            pass
        App.config._config = config = DummyConfig()
        config.dbtab = DummyDBTab(kw)

    def test_getDatabaseNames_sorted(self):
        self._makeConfig(foo=object(), bar=object(), qux=object())
        dc = self._makeOne('test')
        self.assertEqual(list(dc.getDatabaseNames()), ['bar', 'foo', 'qux'])

    def test___getitem___miss(self):
        self._makeConfig(foo=object(), bar=object(), qux=object())
        dc = self._makeOne('test')
        self.assertRaises(KeyError, dc.__getitem__, 'nonesuch')

    def test___getitem___hit(self):
        from App.ApplicationManager import AltDatabaseManager
        from App.ApplicationManager import FakeConnection
        foo=object()
        bar=object()
        qux=object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne('test').__of__(root)
        found = dc['foo']
        self.failUnless(isinstance(found, AltDatabaseManager))
        self.assertEqual(found.id, 'foo')
        self.failUnless(found.aq_parent is dc)
        conn = found._p_jar
        self.failUnless(isinstance(conn, FakeConnection))
        self.failUnless(conn.db() is foo)

    def test___bobo_traverse___miss(self):
        self._makeConfig(foo=object(), bar=object(), qux=object())
        dc = self._makeOne('test')
        self.assertRaises(AttributeError,
                          dc.__bobo_traverse__, None, 'nonesuch')

    def test___bobo_traverse___hit_db(self):
        from App.ApplicationManager import AltDatabaseManager
        from App.ApplicationManager import FakeConnection
        foo=object()
        bar=object()
        qux=object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne('test').__of__(root)
        found = dc.__bobo_traverse__(None, 'foo')
        self.failUnless(isinstance(found, AltDatabaseManager))
        self.assertEqual(found.id, 'foo')
        self.failUnless(found.aq_parent is dc)
        conn = found._p_jar
        self.failUnless(isinstance(conn, FakeConnection))
        self.failUnless(conn.db() is foo)

    def test___bobo_traverse___miss_db_hit_attr(self):
        foo=object()
        bar=object()
        qux=object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne('test').__of__(root)
        dc.spam = spam = object()
        found = dc.__bobo_traverse__(None, 'spam')
        self.failUnless(found is spam)

    def test_tpValues(self):
        from App.ApplicationManager import AltDatabaseManager
        foo=object()
        bar=object()
        qux=object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne('test').__of__(root)
        values = dc.tpValues()
        self.assertEqual(len(values), 3)
        self.failUnless(isinstance(values[0], AltDatabaseManager))
        self.assertEqual(values[0].id, 'bar')
        self.assertEqual(values[0]._p_jar, None)
        self.failUnless(isinstance(values[1], AltDatabaseManager))
        self.assertEqual(values[1].id, 'foo')
        self.assertEqual(values[1]._p_jar, None)
        self.failUnless(isinstance(values[2], AltDatabaseManager))
        self.assertEqual(values[2].id, 'qux')
        self.assertEqual(values[2]._p_jar, None)


class DummyDBTab:
    def __init__(self, databases=None):
        self._databases = databases or {}

    def listDatabaseNames(self):
        return self._databases.keys()

    def hasDatabase(self, name):
        return name in self._databases

    def getDatabase(self, name):
        return self._databases[name]



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FakeConnectionTests),
        unittest.makeSuite(DatabaseChooserTests),
    ))
