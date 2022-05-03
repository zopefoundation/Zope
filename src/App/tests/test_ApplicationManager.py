import os
import shutil
import sys
import tempfile
import time
import unittest

import Testing.testbrowser
import Testing.ZopeTestCase


class DummyForm:

    def __call__(self, *args, **kw):
        return kw


class DummyConnection:

    def __init__(self, db):
        self.__db = db

    def db(self):
        return self.__db


class DummyDBTab:
    def __init__(self, databases=None):
        self._databases = databases or {}

    def listDatabaseNames(self):
        return list(self._databases.keys())

    def hasDatabase(self, name):
        return name in self._databases

    def getDatabase(self, name):
        return self._databases[name]


class DummyDB:

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

    def undoInfo(self, first_transaction, last_transaction):
        return [{'time': 1,
                 'description': 'Transaction 1',
                 'id': b'id1'}]

    def undoMultiple(self, tids):
        pass


class DummyTransaction:

    def __init__(self, raises=False):
        self.raises = raises
        self.aborted = False

    def note(self, note):
        self._note = note

    def commit(self):
        if self.raises:
            raise RuntimeError('This did not work')

    def abort(self):
        self.aborted = True


class DummyTransactionModule:

    def __init__(self, raises=False):
        self.ts = DummyTransaction(raises=raises)

    def get(self):
        return self.ts


class ConfigTestBase:

    def setUp(self):
        super().setUp()
        import App.config
        self._old_config = App.config._config

    def tearDown(self):
        import App.config
        App.config._config = self._old_config
        super().tearDown()

    def _makeConfig(self, **kw):
        import App.config

        class DummyConfig:
            def __init__(self):
                self.debug_mode = False

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


class ConfigurationViewerTests(ConfigTestBase, unittest.TestCase):

    def _getTargetClass(self):
        from App.ApplicationManager import ConfigurationViewer
        return ConfigurationViewer

    def _makeOne(self):
        return self._getTargetClass()()

    def test_defaults(self):
        cv = self._makeOne()
        self.assertEqual(cv.id, 'Configuration')
        self.assertEqual(cv.meta_type, 'Configuration Viewer')
        self.assertEqual(cv.title, 'Configuration Viewer')

    def test_manage_getSysPath(self):
        cv = self._makeOne()
        self.assertEqual(cv.manage_getSysPath(), sorted(sys.path))

    def test_manage_getConfiguration(self):
        from App.config import getConfiguration
        cv = self._makeOne()
        cfg = getConfiguration()

        for info_dict in cv.manage_getConfiguration():
            self.assertEqual(info_dict['value'],
                             str(getattr(cfg, info_dict['name'])))


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

    def test_process_time(self):
        am = self._makeOne()
        now = time.time()

        measure, unit = am.process_time(_when=now).strip().split()
        self.assertEqual(unit, 'sec')

        ret_str = am.process_time(_when=now + 90061).strip()
        secs = 1 + int(measure)
        self.assertEqual(ret_str, '1 day 1 hour 1 min %i sec' % secs)

        ret_str = am.process_time(_when=now + 180122).strip()
        secs = 2 + int(measure)
        self.assertEqual(ret_str, '2 days 2 hours 2 min %i sec' % secs)


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

    def test_manage_pack(self):
        am = self._makeOne()
        am._p_jar = self._makeJar('foo', '')

        # The default value for days is 0, meaning pack to now
        pack_to = time.time()
        am.manage_pack()
        self.assertAlmostEqual(am._getDB()._packed, pack_to, delta=1)

        # Try a float value
        pack_to = time.time() - 10800  # 3 hrs, 0.125 days
        packed_to = am.manage_pack(days=.125)
        self.assertAlmostEqual(am._getDB()._packed, pack_to, delta=1)
        self.assertAlmostEqual(packed_to, pack_to, delta=1)

        # Try an integer
        pack_to = time.time() - 86400  # 1 day
        packed_to = am.manage_pack(days=1)
        self.assertAlmostEqual(am._getDB()._packed, pack_to, delta=1)
        self.assertAlmostEqual(packed_to, pack_to, delta=1)

        # Pass a string
        pack_to = time.time() - 97200  # 27 hrs, 1.125 days
        packed_to = am.manage_pack(days='1.125')
        self.assertAlmostEqual(am._getDB()._packed, pack_to, delta=1)
        self.assertAlmostEqual(packed_to, pack_to, delta=1)

        # Set the dummy storage pack indicator manually
        am._getDB()._packed = None
        # Pass an invalid value
        self.assertIsNone(am.manage_pack(days='foo'))
        # The dummy storage value should not change because pack was not called
        self.assertIsNone(am._getDB()._packed)

    def test_manage_undoTransactions_raises(self):
        # Patch in fake transaction module that will raise RuntimeError
        # on transaction commit
        try:
            import App.Undo
            trs_module = App.Undo.transaction
            App.Undo.transaction = DummyTransactionModule(raises=True)

            am = self._makeOne()
            am._p_jar = self._makeJar('foo', '')
            am.manage_UndoForm = DummyForm()
            undoable_tids = [x['id'] for x in am.undoable_transactions()]
            current_transaction = App.Undo.transaction.get()

            # If no REQUEST is passed in, the exception is re-raised unchanged
            # and the current transaction is left unchanged.
            self.assertRaises(RuntimeError,
                              am.manage_undo_transactions,
                              transaction_info=undoable_tids)
            self.assertFalse(current_transaction.aborted)

            # If a REQUEST is passed in, the transaction will be aborted and
            # the exception is caught. The DummyForm instance shows the
            # call arguments so the exception data is visible.
            res = am.manage_undo_transactions(transaction_info=undoable_tids,
                                              REQUEST={})
            expected = {
                'manage_tabs_message': 'RuntimeError: This did not work',
                'manage_tabs_type': 'danger'}
            self.assertDictEqual(res, expected)
            self.assertTrue(current_transaction.aborted)

        finally:
            # Cleanup
            App.Undo.transaction = trs_module


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
        self.assertTrue((foo_count + 1, 'foo.Foo') in pairs)
        bar_count = sys.getrefcount(Bar)
        self.assertTrue((bar_count + 1, 'foo.Bar') in pairs)
        baz_count = sys.getrefcount(Baz)
        self.assertTrue((baz_count + 1, 'qux.Baz') in pairs)

    def test_refdict(self):
        import sys
        dm = self._makeOne('test')
        Foo, Bar, Baz = self._makeModuleClasses()
        mapping = dm.refdict()
        # XXX : Ugly empiricism here:  I don't know why the count is up 1.
        foo_count = sys.getrefcount(Foo)
        self.assertEqual(mapping['foo.Foo'], foo_count + 1)
        bar_count = sys.getrefcount(Bar)
        self.assertEqual(mapping['foo.Bar'], bar_count + 1)
        baz_count = sys.getrefcount(Baz)
        self.assertEqual(mapping['qux.Baz'], baz_count + 1)

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
        self.assertEqual(mapping['foo.Foo'], foo_count + 1)
        bar_count = sys.getrefcount(Bar)
        self.assertEqual(mapping['foo.Bar'], bar_count + 1)
        baz_count = sys.getrefcount(Baz)
        self.assertEqual(mapping['qux.Baz'], baz_count + 1)

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

    # def test_dbconnections(self):  XXX -- TOO UGLY TO TEST

    def test_manage_getSysPath(self):
        import sys
        dm = self._makeOne('test')
        self.assertEqual(dm.manage_getSysPath(), list(sys.path))


class MenuDtmlTests(ConfigTestBase, Testing.ZopeTestCase.FunctionalTestCase):
    """Browser testing ..dtml.menu.dtml."""

    def setUp(self):
        super().setUp()
        uf = self.app.acl_users
        uf.userFolderAddUser('manager', 'manager_pass', ['Manager'], [])
        self.browser = Testing.testbrowser.Browser()
        self.browser.login('manager', 'manager_pass')

    def test_menu_dtml__1(self):
        """It contains the databases in navigation."""
        self._makeConfig(foo=object(), bar=object(), qux=object())
        self.browser.open('http://localhost/manage_menu')
        links = [
            self.browser.getLink('ZODB foo'),
            self.browser.getLink('ZODB bar'),
            self.browser.getLink('ZODB qux'),
        ]
        for link in links:
            self.assertEqual(
                link.attrs['title'], 'Zope Object Database Manager')

    def test_menu_dtml__2(self):
        """It still shows the navigation in case no database is configured."""
        # This effect can happen in tests, e.g. with `plone.testing`. There a
        # `Control_Panel` is not configured in the standard setup, so we will
        # get a `NameError` while trying to get the databases.
        self.browser.open('http://localhost/manage_menu')
        self.assertTrue(self.browser.isHtml)
        self.assertIn('Control Panel', self.browser.contents)
        self.assertNotIn('ZODB', self.browser.contents)
