import unittest


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

    def _makeOne(self, id):
        return self._getTargetClass()(id)

    def _makeRoot(self):
        from ExtensionClass import Base

        class Root(Base):
            _p_jar = None

            def getPhysicalRoot(self):
                return self
        return Root()

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
        foo = object()
        bar = object()
        qux = object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne('test').__of__(root)
        found = dc['foo']
        self.assertTrue(isinstance(found, AltDatabaseManager))
        self.assertEqual(found.id, 'foo')
        self.assertTrue(found.aq_parent is dc)
        conn = found._p_jar
        self.assertTrue(isinstance(conn, FakeConnection))
        self.assertTrue(conn.db() is foo)

    def test___bobo_traverse___miss(self):
        self._makeConfig(foo=object(), bar=object(), qux=object())
        dc = self._makeOne('test')
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
        dc = self._makeOne('test').__of__(root)
        found = dc.__bobo_traverse__(None, 'foo')
        self.assertTrue(isinstance(found, AltDatabaseManager))
        self.assertEqual(found.id, 'foo')
        self.assertTrue(found.aq_parent is dc)
        conn = found._p_jar
        self.assertTrue(isinstance(conn, FakeConnection))
        self.assertTrue(conn.db() is foo)

    def test___bobo_traverse___miss_db_hit_attr(self):
        foo = object()
        bar = object()
        qux = object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne('test').__of__(root)
        dc.spam = spam = object()
        found = dc.__bobo_traverse__(None, 'spam')
        self.assertTrue(found is spam)

    def test_tpValues(self):
        from App.ApplicationManager import AltDatabaseManager
        foo = object()
        bar = object()
        qux = object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne('test').__of__(root)
        values = dc.tpValues()
        self.assertEqual(len(values), 3)
        self.assertTrue(isinstance(values[0], AltDatabaseManager))
        self.assertEqual(values[0].id, 'bar')
        self.assertEqual(values[0]._p_jar, None)
        self.assertTrue(isinstance(values[1], AltDatabaseManager))
        self.assertEqual(values[1].id, 'foo')
        self.assertEqual(values[1]._p_jar, None)
        self.assertTrue(isinstance(values[2], AltDatabaseManager))
        self.assertEqual(values[2].id, 'qux')
        self.assertEqual(values[2]._p_jar, None)


class DBProxyTestsBase(object):

    def _makeOne(self):
        return self._getTargetClass()()

    def _makeJar(self, dbname, dbsize):
        class Jar:
            def db(self):
                return self._db
        jar = Jar()
        jar._db = DummyDB(dbname, dbsize)
        return jar

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

    def test_manage_pack(self):
        am = self._makeOne()
        jar = am._p_jar = self._makeJar('foo', '')
        am.manage_pack(1, _when=86400 * 2)
        self.assertEqual(jar._db._packed, 86400)


class ApplicationManagerTests(ConfigTestBase,
                              DBProxyTestsBase,
                              unittest.TestCase):

    def setUp(self):
        ConfigTestBase.setUp(self)
        self._tempdirs = ()

    def tearDown(self):
        import shutil
        for tempdir in self._tempdirs:
            shutil.rmtree(tempdir)
        ConfigTestBase.tearDown(self)

    def _getTargetClass(self):
        from App.ApplicationManager import ApplicationManager
        return ApplicationManager

    def _makeTempdir(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        self._tempdirs += (tmp,)
        return tmp

    def _makeFile(self, dir, name, text):
        import os
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
        import sys
        am = self._makeOne()
        self.assertEqual(am.sys_version(), sys.version)

    def test_sys_platform(self):
        import sys
        am = self._makeOne()
        self.assertEqual(am.sys_platform(), sys.platform)

    def test__canCopy(self):
        am = self._makeOne()
        self.assertFalse(am._canCopy())

    def test_manage_app(self):
        from zExceptions import Redirect
        am = self._makeOne()
        try:
            am.manage_app('http://example.com/foo')
        except Redirect as v:
            self.assertEqual(v.args, ('http://example.com/foo/manage',))
        else:
            self.fail('Redirect not raised')

    def test_thread_get_ident(self):
        import thread
        am = self._makeOne()
        self.assertEqual(am.thread_get_ident(), thread.get_ident())

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


class AltDatabaseManagerTests(DBProxyTestsBase,
                              unittest.TestCase):

    def _getTargetClass(self):
        from App.ApplicationManager import AltDatabaseManager
        return AltDatabaseManager


class DummyDBTab(object):
    def __init__(self, databases=None):
        self._databases = databases or {}

    def listDatabaseNames(self):
        return self._databases.keys()

    def hasDatabase(self, name):
        return name in self._databases

    def getDatabase(self, name):
        return self._databases[name]


class DummyDB(object):

    _packed = None

    def __init__(self, name, size):
        self._name = name
        self._size = size

    def getName(self):
        return self._name

    def getSize(self):
        return self._size

    def pack(self, when):
        self._packed = when
