import os
import shutil
import sys
import tempfile
import unittest


class DummyConnection(object):

    def __init__(self, db):
        self.__db = db

    def db(self):
        return self.__db


class DummyDBTab(object):
    def __init__(self, databases=None):
        self._databases = databases or {}

    def listDatabaseNames(self):
        return list(self._databases.keys())

    def hasDatabase(self, name):
        return name in self._databases

    def getDatabase(self, name):
        return self._databases[name]


class DummyDB(object):

    _packed = None

    def __init__(self, name, size, cache_size):
        self._name = name
        self._size = size
        self._cache_size = cache_size

    def getName(self):
        return self._name

    def getSize(self):
        return self._size

    def getCacheSize(self):
        return self._cache_size

    def pack(self, when):
        self._packed = when


class ConfigTestBase(object):

    def setUp(self):
        import App.config
        self._old_config = App.config._config

    def tearDown(self):
        import App.config
        App.config._config = self._old_config

    def _makeConfig(self, **kw):
        import App.config

        class DummyConfig(object):
            pass
        App.config._config = config = DummyConfig()
        config.dbtab = DummyDBTab(kw)
        return config


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
        self.assertTrue(fc.db() is db)


class DatabaseChooserTests(ConfigTestBase, unittest.TestCase):

    def _getTargetClass(self):
        from App.ApplicationManager import DatabaseChooser
        return DatabaseChooser

    def _makeOne(self):
        return self._getTargetClass()()

    def _makeRoot(self):
        from ExtensionClass import Base

        class Root(Base):
            _p_jar = None

            def getPhysicalRoot(self):
                return self
        return Root()

    def test_getDatabaseNames_sorted(self):
        self._makeConfig(foo=object(), bar=object(), qux=object())
        dc = self._makeOne()
        self.assertEqual(list(dc.getDatabaseNames()), ['bar', 'foo', 'qux'])

    def test___getitem___miss(self):
        self._makeConfig(foo=object(), bar=object(), qux=object())
        dc = self._makeOne()
        self.assertRaises(KeyError, dc.__getitem__, 'nonesuch')

    def test___getitem___hit(self):
        from App.ApplicationManager import AltDatabaseManager
        from App.ApplicationManager import FakeConnection
        foo = object()
        bar = object()
        qux = object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne().__of__(root)
        found = dc['foo']
        self.assertIsInstance(found, AltDatabaseManager)
        self.assertEqual(found.id, 'foo')
        self.assertTrue(found.__parent__ is dc)
        conn = found._p_jar
        self.assertIsInstance(conn, FakeConnection)
        self.assertTrue(conn.db() is foo)

    def test___bobo_traverse___miss(self):
        self._makeConfig(foo=object(), bar=object(), qux=object())
        dc = self._makeOne()
        self.assertRaises(AttributeError,
                          dc.__bobo_traverse__, None, 'nonesuch')

    def test___bobo_traverse___hit_db(self):
        from App.ApplicationManager import AltDatabaseManager
        from App.ApplicationManager import FakeConnection
        foo = object()
        bar = object()
        qux = object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne().__of__(root)
        found = dc.__bobo_traverse__(None, 'foo')
        self.assertIsInstance(found, AltDatabaseManager)
        self.assertEqual(found.id, 'foo')
        self.assertTrue(found.__parent__ is dc)
        conn = found._p_jar
        self.assertIsInstance(conn, FakeConnection)
        self.assertTrue(conn.db() is foo)

    def test___bobo_traverse___miss_db_hit_attr(self):
        foo = object()
        bar = object()
        qux = object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne().__of__(root)
        dc.spam = spam = object()
        found = dc.__bobo_traverse__(None, 'spam')
        self.assertTrue(found is spam)


class ApplicationManagerTests(ConfigTestBase, unittest.TestCase):

    def setUp(self):
        ConfigTestBase.setUp(self)
        self._tempdirs = ()

    def tearDown(self):
        for tempdir in self._tempdirs:
            shutil.rmtree(tempdir)
        ConfigTestBase.tearDown(self)

    def _getTargetClass(self):
        from App.ApplicationManager import ApplicationManager
        return ApplicationManager

    def _makeOne(self):
        return self._getTargetClass()()

    def _makeTempdir(self):
        tmp = tempfile.mkdtemp()
        self._tempdirs += (tmp,)
        return tmp

    def _makeFile(self, dir, name, text):
        os.makedirs(dir)
        fqn = os.path.join(dir, name)
        f = open(fqn, 'w')
        f.write(text)
        f.flush()
        f.close()
        return fqn

    def test_version_txt(self):
        from App.version_txt import version_txt
        am = self._makeOne()
        self.assertEqual(am.version_txt(), version_txt())

    def test_sys_version(self):
        am = self._makeOne()
        self.assertEqual(am.sys_version(), sys.version)

    def test_sys_platform(self):
        am = self._makeOne()
        self.assertEqual(am.sys_platform(), sys.platform)

    def test_getINSTANCE_HOME(self):
        am = self._makeOne()
        config = self._makeConfig()
        instdir = config.instancehome = self._makeTempdir()
        self.assertEqual(am.getINSTANCE_HOME(), instdir)

    def test_getCLIENT_HOME(self):
        am = self._makeOne()
        config = self._makeConfig()
        cldir = config.clienthome = self._makeTempdir()
        self.assertEqual(am.getCLIENT_HOME(), cldir)


class AltDatabaseManagerTests(unittest.TestCase):

    def _getTargetClass(self):
        from App.ApplicationManager import AltDatabaseManager
        return AltDatabaseManager

    def _makeOne(self):
        return self._getTargetClass()()

    def _makeJar(self, dbname, dbsize):
        class Jar:
            def db(self):
                return self._db
        jar = Jar()
        jar._db = DummyDB(dbname, dbsize, 0)
        return jar

    def _getManagerClass(self):
        adm = self._getTargetClass()

        class TestCacheManager(adm):
            # Derived CacheManager that fakes enough of the DatabaseManager to
            # make it possible to test at least some parts of the CacheManager.
            def __init__(self, connection):
                self._p_jar = connection
        return TestCacheManager

    def test_cache_size(self):
        db = DummyDB('db', 0, 42)
        connection = DummyConnection(db)
        manager = self._getManagerClass()(connection)
        self.assertEqual(manager.cache_size(), 42)
        db._cache_size = 12
        self.assertEqual(manager.cache_size(), 12)

    def test_db_name(self):
        am = self._makeOne()
        am._p_jar = self._makeJar('foo', '')
        self.assertEqual(am.db_name(), 'foo')

    def test_db_size_string(self):
        am = self._makeOne()
        am._p_jar = self._makeJar('foo', 'super')
        self.assertEqual(am.db_size(), 'super')

    def test_db_size_lt_1_meg(self):
        am = self._makeOne()
        am._p_jar = self._makeJar('foo', 4497)
        self.assertEqual(am.db_size(), '4.4K')

    def test_db_size_gt_1_meg(self):
        am = self._makeOne()
        am._p_jar = self._makeJar('foo', (2048 * 1024) + 123240)
        self.assertEqual(am.db_size(), '2.1M')
