import unittest

class ConfigTestBase:

    def setUp(self):
        import App.config
        self._old_config = App.config._config

    def tearDown(self):
        import App.config
        App.config._config = self._old_config

    def _makeConfig(self, **kw):
        import App.config
        class DummyConfig:
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
        foo=object()
        bar=object()
        qux=object()
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
        foo=object()
        bar=object()
        qux=object()
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
        foo=object()
        bar=object()
        qux=object()
        self._makeConfig(foo=foo, bar=bar, qux=qux)
        root = self._makeRoot()
        dc = self._makeOne('test').__of__(root)
        dc.spam = spam = object()
        found = dc.__bobo_traverse__(None, 'spam')
        self.assertTrue(found is spam)

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
        self.assertTrue(isinstance(values[0], AltDatabaseManager))
        self.assertEqual(values[0].id, 'bar')
        self.assertEqual(values[0]._p_jar, None)
        self.assertTrue(isinstance(values[1], AltDatabaseManager))
        self.assertEqual(values[1].id, 'foo')
        self.assertEqual(values[1]._p_jar, None)
        self.assertTrue(isinstance(values[2], AltDatabaseManager))
        self.assertEqual(values[2].id, 'qux')
        self.assertEqual(values[2]._p_jar, None)


class DebugManagerTests(unittest.TestCase):

    def setUp(self):
        import sys
        self._sys = sys
        self._old_sys_modules = sys.modules.copy()

    def tearDown(self):
        self._sys.modules.clear()
        self._sys.modules.update(self._old_sys_modules)

    def _getTargetClass(self):
        from App.ApplicationManager import DebugManager
        return DebugManager

    def _makeOne(self, id):
        return self._getTargetClass()(id)

    def _makeModuleClasses(self):
        import sys
        import types
        from ExtensionClass import Base
        class Foo(Base):
            pass
        class Bar(Base):
            pass
        class Baz(Base):
            pass
        foo = sys.modules['foo'] = types.ModuleType('foo')
        foo.Foo = Foo
        Foo.__module__ = 'foo'
        foo.Bar = Bar
        Bar.__module__ = 'foo'
        qux = sys.modules['qux'] = types.ModuleType('qux')
        qux.Baz = Baz
        Baz.__module__ = 'qux'
        return Foo, Bar, Baz

    def test_refcount_no_limit(self):
        import sys
        dm = self._makeOne('test')
        Foo, Bar, Baz = self._makeModuleClasses()
        pairs = dm.refcount()
        # XXX : Ugly empiricism here:  I don't know why the count is up 1.
        foo_count = sys.getrefcount(Foo)
        self.assertTrue((foo_count+1, 'foo.Foo') in pairs)
        bar_count = sys.getrefcount(Bar)
        self.assertTrue((bar_count+1, 'foo.Bar') in pairs)
        baz_count = sys.getrefcount(Baz)
        self.assertTrue((baz_count+1, 'qux.Baz') in pairs)

    def test_refdict(self):
        import sys
        dm = self._makeOne('test')
        Foo, Bar, Baz = self._makeModuleClasses()
        mapping = dm.refdict()
        # XXX : Ugly empiricism here:  I don't know why the count is up 1.
        foo_count = sys.getrefcount(Foo)
        self.assertEqual(mapping['foo.Foo'], foo_count+1)
        bar_count = sys.getrefcount(Bar)
        self.assertEqual(mapping['foo.Bar'], bar_count+1)
        baz_count = sys.getrefcount(Baz)
        self.assertEqual(mapping['qux.Baz'], baz_count+1)

    def test_rcsnapshot(self):
        import sys
        import App.ApplicationManager
        from DateTime.DateTime import DateTime
        dm = self._makeOne('test')
        Foo, Bar, Baz = self._makeModuleClasses()
        before = DateTime()
        dm.rcsnapshot()
        after = DateTime()
        # XXX : Ugly empiricism here:  I don't know why the count is up 1.
        self.assertTrue(before <= App.ApplicationManager._v_rst <= after)
        mapping = App.ApplicationManager._v_rcs
        foo_count = sys.getrefcount(Foo)
        self.assertEqual(mapping['foo.Foo'], foo_count+1)
        bar_count = sys.getrefcount(Bar)
        self.assertEqual(mapping['foo.Bar'], bar_count+1)
        baz_count = sys.getrefcount(Baz)
        self.assertEqual(mapping['qux.Baz'], baz_count+1)

    def test_rcdate(self):
        import App.ApplicationManager
        dummy = object()
        App.ApplicationManager._v_rst = dummy
        dm = self._makeOne('test')
        found = dm.rcdate()
        App.ApplicationManager._v_rst = None
        self.assertTrue(found is dummy)

    def test_rcdeltas(self):
        dm = self._makeOne('test')
        dm.rcsnapshot()
        Foo, Bar, Baz = self._makeModuleClasses()
        mappings = dm.rcdeltas()
        self.assertTrue(len(mappings))
        mapping = mappings[0]
        self.assertTrue('rc' in mapping)
        self.assertTrue('pc' in mapping)
        self.assertEqual(mapping['delta'], mapping['rc'] - mapping['pc'])

    #def test_dbconnections(self):  XXX -- TOO UGLY TO TEST
    #def test_manage_profile_stats(self):  XXX -- TOO UGLY TO TEST

    def test_manage_profile_reset(self):
        import sys
        from ZPublisher import Publish
        _old_sys__ps_ = getattr(sys, '_ps_', self)
        _old_Publish_pstat = getattr(Publish, '_pstat', self)
        sys._ps_ = Publish._pstat = object()
        try:
            dm = self._makeOne('test')
            dm.manage_profile_reset()
        finally:
            if _old_sys__ps_ is not self:
                sys._ps_ = _old_sys__ps_
            if _old_Publish_pstat is not self:
                Publish._pstat = _old_Publish_pstat
        self.assertTrue(sys._ps_ is None)
        self.assertTrue(Publish._pstat is None)

    def test_manage_getSysPath(self):
        import sys
        dm = self._makeOne('test')
        self.assertEqual(dm.manage_getSysPath(), list(sys.path))


class DBProxyTestsBase:

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
        am.manage_pack(1, _when=86400*2)
        self.assertEqual(jar._db._packed, 86400)

class ApplicationManagerTests(ConfigTestBase,
                              DBProxyTestsBase,
                              unittest.TestCase,
                             ):

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

    def test_ctor_initializes_Products(self):
        from App.Product import ProductFolder
        am = self._makeOne()
        self.assertTrue(isinstance(am.Products, ProductFolder))

    def test__canCopy(self):
        am = self._makeOne()
        self.assertFalse(am._canCopy())

    def test_manage_app(self):
        from zExceptions import Redirect
        am = self._makeOne()
        try:
            am.manage_app('http://example.com/foo')
        except Redirect, v:
            self.assertEqual(v.args, ('http://example.com/foo/manage',))
        else:
            self.fail('Redirect not raised')

    def test_process_time_seconds(self):
        am = self._makeOne()
        am.process_start = 0
        self.assertEqual(am.process_time(0).strip(), '0 sec')
        self.assertEqual(am.process_time(1).strip(), '1 sec')
        self.assertEqual(am.process_time(2).strip(), '2 sec')

    def test_process_time_minutes(self):
        am = self._makeOne()
        am.process_start = 0
        self.assertEqual(am.process_time(60).strip(), '1 min 0 sec')
        self.assertEqual(am.process_time(61).strip(), '1 min 1 sec')
        self.assertEqual(am.process_time(62).strip(), '1 min 2 sec')
        self.assertEqual(am.process_time(120).strip(), '2 min 0 sec')
        self.assertEqual(am.process_time(121).strip(), '2 min 1 sec')
        self.assertEqual(am.process_time(122).strip(), '2 min 2 sec')

    def test_process_time_hours(self):
        am = self._makeOne()
        am.process_start = 0
        n1 = 60 * 60
        n2 = n1 * 2
        self.assertEqual(am.process_time(n1).strip(),
                         '1 hour  0 sec')
        self.assertEqual(am.process_time(n1 + 61).strip(),
                         '1 hour 1 min 1 sec')
        self.assertEqual(am.process_time(n2 + 1).strip(),
                         '2 hours  1 sec')
        self.assertEqual(am.process_time(n2 + 122).strip(),
                         '2 hours 2 min 2 sec')

    def test_process_time_days(self):
        am = self._makeOne()
        am.process_start = 0
        n1 = 60 * 60 * 24
        n2 = n1 * 2
        self.assertEqual(am.process_time(n1).strip(),
                         '1 day   0 sec')
        self.assertEqual(am.process_time(n1 + 3661).strip(),
                         '1 day 1 hour 1 min 1 sec')
        self.assertEqual(am.process_time(n2 + 1).strip(),
                         '2 days   1 sec')
        self.assertEqual(am.process_time(n2 + 7322).strip(),
                         '2 days 2 hours 2 min 2 sec')

    def test_thread_get_ident(self):
        import thread
        am = self._makeOne()
        self.assertEqual(am.thread_get_ident(), thread.get_ident())

    #def test_manage_restart(self):  XXX -- TOO UGLY TO TEST
    #def test_manage_restart(self):  XXX -- TOO UGLY TO TEST

    def test_revert_points(self):
        am = self._makeOne()
        self.assertEqual(list(am.revert_points()), [])

    def test_version_list(self):
        # XXX this method is too stupid to live:  returning a bare list
        #     of versions without even tying them to the products?
        #     and what about products living outside SOFTWARE_HOME?
        #     Nobody calls it, either
        import os
        am = self._makeOne()
        config = self._makeConfig()
        swdir = config.softwarehome = self._makeTempdir()
        foodir = os.path.join(swdir, 'Products', 'foo')
        self._makeFile(foodir, 'VERSION.TXT', '1.2')
        bardir = os.path.join(swdir, 'Products', 'bar')
        self._makeFile(bardir, 'VERSION.txt', '3.4')
        bazdir = os.path.join(swdir, 'Products', 'baz')
        self._makeFile(bazdir, 'version.txt', '5.6')
        versions = am.version_list()
        self.assertEqual(versions, ['3.4', '5.6', '1.2'])

    def test_getSOFTWARE_HOME_missing(self):
        am = self._makeOne()
        config = self._makeConfig()
        self.assertEqual(am.getSOFTWARE_HOME(), None)

    def test_getSOFTWARE_HOME_present(self):
        am = self._makeOne()
        config = self._makeConfig()
        swdir = config.softwarehome = self._makeTempdir()
        self.assertEqual(am.getSOFTWARE_HOME(), swdir)

    def test_getZOPE_HOME_missing(self):
        am = self._makeOne()
        config = self._makeConfig()
        self.assertEqual(am.getZOPE_HOME(), None)

    def test_getZOPE_HOME_present(self):
        am = self._makeOne()
        config = self._makeConfig()
        zopedir = config.zopehome = self._makeTempdir()
        self.assertEqual(am.getZOPE_HOME(), zopedir)

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

    def test_getServers(self):
        from asyncore import socket_map

        class DummySocketServer:
            def __init__(self, port):
                self.port = port

        class AnotherSocketServer(DummySocketServer):
            pass

        class NotAServer:
            pass

        am = self._makeOne()
        _old_socket_map = socket_map.copy()
        socket_map.clear()
        socket_map['foo'] = DummySocketServer(45)
        socket_map['bar'] = AnotherSocketServer(57)
        socket_map['qux'] = NotAServer()

        try:
            pairs = am.getServers()
        finally:
            socket_map.clear()
            socket_map.update(_old_socket_map)

        self.assertEqual(len(pairs), 2)
        self.assertTrue((str(DummySocketServer), 'Port: 45') in pairs)
        self.assertTrue((str(AnotherSocketServer), 'Port: 57') in pairs)

    #def test_objectIds(self):  XXX -- TOO UGLY TO TEST (BBB for Zope 2.3!!)


class AltDatabaseManagerTests(DBProxyTestsBase,
                              unittest.TestCase,
                             ):

    def _getTargetClass(self):
        from App.ApplicationManager import AltDatabaseManager
        return AltDatabaseManager


class DummyDBTab:
    def __init__(self, databases=None):
        self._databases = databases or {}

    def listDatabaseNames(self):
        return self._databases.keys()

    def hasDatabase(self, name):
        return name in self._databases

    def getDatabase(self, name):
        return self._databases[name]

class DummyDB:

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

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FakeConnectionTests),
        unittest.makeSuite(DatabaseChooserTests),
        unittest.makeSuite(DebugManagerTests),
        unittest.makeSuite(ApplicationManagerTests),
        unittest.makeSuite(AltDatabaseManagerTests),
    ))
