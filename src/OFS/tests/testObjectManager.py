import os
import unittest
from logging import getLogger
from urllib.parse import quote

from AccessControl.owner import EmergencyUserCannotOwn
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from AccessControl.users import User
from AccessControl.users import emergency_user
from AccessControl.users import nobody
from AccessControl.users import system
from Acquisition import Implicit
from Acquisition import aq_self
from App.config import getConfiguration
from OFS.interfaces import IItem
from OFS.metaconfigure import setDeprecatedManageAddDelete
from OFS.ObjectManager import ObjectManager
from OFS.SimpleItem import SimpleItem
from zExceptions import BadRequest
from Zope2.App import zcml
from zope.component.testing import PlacelessSetup
from zope.interface import implementer


logger = getLogger('OFS.subscribers')


class FauxRoot(Implicit):

    id = '/'

    def getPhysicalRoot(self):
        return self

    def getPhysicalPath(self):
        return ()


class FauxUser(Implicit):

    def __init__(self, id, login):

        self._id = id
        self._login = login

    def getId(self):

        return self._id


class DeleteFailed(Exception):
    pass


class ItemForDeletion(SimpleItem):

    def __init__(self, fail_on_delete=False):
        self.id = 'stuff'
        self.before_delete_called = False
        self.fail_on_delete = fail_on_delete

    def manage_beforeDelete(self, item, container):
        self.before_delete_called = True
        if self.fail_on_delete:
            raise DeleteFailed

    def manage_afterAdd(self, item, container):
        pass

    def manage_afterClone(self, item):
        pass


@implementer(IItem)
class ObjectManagerWithIItem(ObjectManager):
    """The event subscribers work on IItem."""


class ObjectManagerTests(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.saved_cfg_debug_mode = getConfiguration().debug_mode
        import Zope2.App
        zcml.load_config('meta.zcml', Zope2.App)
        import OFS
        zcml.load_config('configure.zcml', OFS)
        setDeprecatedManageAddDelete(ItemForDeletion)

    def tearDown(self):
        noSecurityManager()
        getConfiguration().debug_mode = self.saved_cfg_debug_mode
        super().tearDown()

    def setDebugMode(self, mode):
        getConfiguration().debug_mode = mode

    def _getTargetClass(self):
        return ObjectManagerWithIItem

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw).__of__(FauxRoot())

    def test_interfaces(self):
        from OFS.interfaces import IObjectManager
        from OFS.ObjectManager import ObjectManager
        from zope.container.interfaces import IContainer
        from zope.interface.verify import verifyClass

        verifyClass(IContainer, ObjectManager)
        verifyClass(IObjectManager, ObjectManager)

    def test_filtered_meta_types(self):

        class _DummySecurityPolicy:

            def checkPermission(self, permission, object, context):
                return permission == 'addFoo'

        om = self._makeOne()
        om.all_meta_types = ({'name': 'Foo', 'permission': 'addFoo'},
                             {'name': 'Bar', 'permission': 'addBar'},
                             {'name': 'Baz'})
        try:
            oldPolicy = setSecurityPolicy(_DummySecurityPolicy())
            self.assertEqual(len(om.filtered_meta_types()), 2)
            self.assertEqual(om.filtered_meta_types()[0]['name'], 'Foo')
            self.assertEqual(om.filtered_meta_types()[1]['name'], 'Baz')
        finally:
            noSecurityManager()
            setSecurityPolicy(oldPolicy)

    def test_all_meta_types_adds_zmi_modal(self):
        om = self._makeOne()
        om.meta_types = ({'name': 'Foo'}, {'name': 'Bar'}, {'name': 'Baz'})
        amt = om.all_meta_types()
        for mt in [x for x in amt if x['name'] in ('foo', 'bar', 'baz')]:
            self.assertEqual(mt['zmi_show_add_dialog'], 'modal')

        # Pick an example that will be different
        for mt in [x for x in amt if x['name'] == 'Virtual Host Monster']:
            self.assertEqual(mt['zmi_show_add_dialog'], '')

    def test_setObject_set_owner_with_no_user(self):
        om = self._makeOne()
        newSecurityManager(None, None)
        si = SimpleItem('no_user')
        om._setObject('no_user', si)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_setObject_set_owner_with_emergency_user(self):
        om = self._makeOne()
        newSecurityManager(None, emergency_user)
        si = SimpleItem('should_fail')
        self.assertEqual(si.__ac_local_roles__, None)
        self.assertRaises(
            EmergencyUserCannotOwn,
            om._setObject, 'should_fail', si)

    def test_setObject_set_owner_with_system_user(self):
        om = self._makeOne()
        newSecurityManager(None, system)
        si = SimpleItem('system')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('system', si)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_setObject_set_owner_with_anonymous_user(self):
        om = self._makeOne()
        newSecurityManager(None, nobody)
        si = SimpleItem('anon')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('anon', si)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_setObject_set_owner_with_user(self):
        om = self._makeOne()
        user = User('user', '123', (), ()).__of__(FauxRoot())
        newSecurityManager(None, user)
        si = SimpleItem('user_creation')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('user_creation', si)
        self.assertEqual(si.__ac_local_roles__, {'user': ['Owner']})

    def test_setObject_set_owner_with_faux_user(self):
        om = self._makeOne()
        user = FauxUser('user_id', 'user_login').__of__(FauxRoot())
        newSecurityManager(None, user)
        si = SimpleItem('faux_creation')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('faux_creation', si)
        self.assertEqual(si.__ac_local_roles__, {'user_id': ['Owner']})

    def test_setObject_no_set_owner_with_no_user(self):
        om = self._makeOne()
        newSecurityManager(None, None)
        si = SimpleItem('should_be_okay')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('should_be_okay', si, set_owner=0)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_setObject_no_set_owner_with_emergency_user(self):
        om = self._makeOne()
        newSecurityManager(None, emergency_user)
        si = SimpleItem('should_be_okay')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('should_be_okay', si, set_owner=0)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_setObject_no_set_owner_with_system_user(self):
        om = self._makeOne()
        newSecurityManager(None, system)
        si = SimpleItem('should_be_okay')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('should_be_okay', si, set_owner=0)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_setObject_no_set_owner_with_anonymous_user(self):
        om = self._makeOne()
        newSecurityManager(None, nobody)
        si = SimpleItem('should_be_okay')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('should_be_okay', si, set_owner=0)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_setObject_no_set_owner_with_user(self):
        om = self._makeOne()
        user = User('user', '123', (), ()).__of__(FauxRoot())
        newSecurityManager(None, user)
        si = SimpleItem('should_be_okay')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('should_be_okay', si, set_owner=0)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_setObject_no_set_owner_with_faux_user(self):
        om = self._makeOne()
        user = FauxUser('user_id', 'user_login').__of__(FauxRoot())
        newSecurityManager(None, user)
        si = SimpleItem('should_be_okay')
        self.assertEqual(si.__ac_local_roles__, None)
        om._setObject('should_be_okay', si, set_owner=0)
        self.assertEqual(si.__ac_local_roles__, None)

    def test_delObject_before_delete(self):
        # Test that manage_beforeDelete is called
        om = self._makeOne()
        ob = ItemForDeletion()
        om._setObject(ob.getId(), ob)
        self.assertEqual(ob.before_delete_called, False)
        om._delObject(ob.getId())
        self.assertEqual(ob.before_delete_called, True)

    def test_delObject_exception_manager(self):
        # Test exception behavior in manage_beforeDelete
        # Manager user
        self.setDebugMode(False)
        newSecurityManager(None, system)  # Manager
        om = self._makeOne()
        ob = ItemForDeletion(fail_on_delete=True)
        om._setObject(ob.getId(), ob)
        try:
            logger.disabled = 1
            om._delObject(ob.getId())
        finally:
            logger.disabled = 0

    def test_delObject_exception(self):
        # Test exception behavior in manage_beforeDelete
        # non-Manager user
        self.setDebugMode(False)
        om = self._makeOne()
        ob = ItemForDeletion(fail_on_delete=True)
        om._setObject(ob.getId(), ob)
        try:
            logger.disabled = 1
            om._delObject(ob.getId())
        finally:
            logger.disabled = 0

    def test_delObject_exception_debug_manager(self):
        # Test exception behavior in manage_beforeDelete in debug mode
        # Manager user
        self.setDebugMode(True)
        newSecurityManager(None, system)  # Manager
        om = self._makeOne()
        ob = ItemForDeletion(fail_on_delete=True)
        om._setObject(ob.getId(), ob)
        try:
            logger.disabled = 1
            om._delObject(ob.getId())
        finally:
            logger.disabled = 0

    def test_delObject_exception_debug(self):
        # Test exception behavior in manage_beforeDelete in debug mode
        # non-Manager user
        # It's the only special case: we let exceptions propagate.
        self.setDebugMode(True)
        om = self._makeOne()
        ob = ItemForDeletion(fail_on_delete=True)
        om._setObject(ob.getId(), ob)
        try:
            logger.disabled = 1
            self.assertRaises(DeleteFailed, om._delObject, ob.getId())
        finally:
            logger.disabled = 0

    def test_delObject_exception_debug_deep(self):
        # Test exception behavior in manage_beforeDelete in debug mode
        # non-Manager user
        # Test for deep subobjects.
        self.setDebugMode(True)
        om1 = self._makeOne()
        om2 = self._makeOne()
        ob = ItemForDeletion(fail_on_delete=True)
        om1._setObject('om2', om2, set_owner=False)
        om2._setObject(ob.getId(), ob)
        try:
            logger.disabled = 1
            self.assertRaises(DeleteFailed, om1._delObject, 'om2')
        finally:
            logger.disabled = 0

    def test_manage_delObjects(self):
        om = self._makeOne()
        ob = ItemForDeletion()
        om._setObject('stuff', ob)
        om.manage_delObjects('stuff')
        self.assertFalse('stuff' in om)

        om._setObject('stuff', ob)
        om.manage_delObjects(['stuff'])
        self.assertFalse('stuff' in om)

        om._setObject('stuff', ob)
        om.manage_delObjects('stuff')
        self.assertFalse('stuff' in om)

    def test_hasObject(self):
        om = self._makeOne()
        self.assertFalse(om.hasObject('_properties'))
        self.assertFalse(om.hasObject('_getOb'))
        self.assertFalse(om.hasObject('__of__'))
        self.assertFalse(om.hasObject('.'))
        self.assertFalse(om.hasObject('..'))
        self.assertFalse(om.hasObject('aq_base'))
        om.zap__ = True
        self.assertFalse(om.hasObject('zap__'))
        self.assertFalse(om.hasObject('foo'))
        si = SimpleItem('foo')
        om._setObject('foo', si)
        self.assertTrue(om.hasObject('foo'))
        om._delObject('foo')
        self.assertFalse(om.hasObject('foo'))

    def test_setObject_checkId_ok(self):
        om = self._makeOne()
        si = SimpleItem('1')
        om._setObject('AB-dash_under0123', si)
        si = SimpleItem('2')
        om._setObject('ho.bak~', si)
        si = SimpleItem('3')
        om._setObject('dot.comma,dollar$(hi)hash# space', si)
        si = SimpleItem('4')
        om._setObject('b@r', si)
        si = SimpleItem('5')
        om._setObject('..haha', si)
        si = SimpleItem('6')
        om._setObject('.bashrc', si)

    def test_setObject_checkId_bad(self):
        om = self._makeOne()
        si = SimpleItem('111')
        om._setObject('111', si)
        si = SimpleItem('2')
        self.assertRaises(BadRequest, om._setObject, 123, si)
        self.assertRaises(BadRequest, om._setObject, 'a\x01b', si)
        self.assertRaises(BadRequest, om._setObject, '.', si)
        self.assertRaises(BadRequest, om._setObject, '..', si)
        self.assertRaises(BadRequest, om._setObject, '_foo', si)
        self.assertRaises(BadRequest, om._setObject, 'aq_me', si)
        self.assertRaises(BadRequest, om._setObject, 'bah__', si)
        self.assertRaises(BadRequest, om._setObject, '111', si)
        self.assertRaises(BadRequest, om._setObject, 'REQUEST', si)
        self.assertRaises(BadRequest, om._setObject, '/', si)
        self.assertRaises(BadRequest, om._setObject, 'get', si)
        self.assertRaises(BadRequest, om._setObject, 'items', si)
        self.assertRaises(BadRequest, om._setObject, 'keys', si)
        self.assertRaises(BadRequest, om._setObject, 'values', si)
        self.assertRaises(BadRequest, om._setObject, 'foo&bar', si)
        self.assertRaises(BadRequest, om._setObject, 'foo>bar', si)
        self.assertRaises(BadRequest, om._setObject, 'foo<bar', si)
        self.assertRaises(BadRequest, om._setObject, 'foo/bar', si)
        self.assertRaises(BadRequest, om._setObject, '@@ohno', si)
        self.assertRaises(BadRequest, om._setObject, '++ohno', si)

    def test_getsetitem(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        si2 = SimpleItem('2')
        om['1'] = si1
        self.assertTrue('1' in om)
        self.assertTrue(si1 in om.objectValues())
        self.assertTrue('1' in om.objectIds())
        om['2'] = si2
        self.assertTrue('2' in om)
        self.assertTrue(si2 in om.objectValues())
        self.assertTrue('2' in om.objectIds())
        self.assertRaises(BadRequest, om._setObject, '1', si2)
        self.assertRaises(BadRequest, om.__setitem__, '1', si2)

    def test_delitem(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        si2 = SimpleItem('2')
        om['1'] = si1
        om['2'] = si2
        self.assertTrue('1' in om)
        self.assertTrue('2' in om)
        del om['1']
        self.assertFalse('1' in om)
        self.assertTrue('2' in om)
        om._delObject('2')
        self.assertFalse('2' in om)

    def test_iterator(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        si2 = SimpleItem('2')
        om['1'] = si1
        om['2'] = si2
        iterator = iter(om)
        self.assertTrue(hasattr(iterator, '__iter__'))
        self.assertTrue(hasattr(iterator, '__next__'))
        result = [i for i in iterator]
        self.assertTrue('1' in result)
        self.assertTrue('2' in result)

    def test_len(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        si2 = SimpleItem('2')
        om['1'] = si1
        om['2'] = si2
        self.assertTrue(len(om) == 2)

    def test_nonzero(self):
        om = self._makeOne()
        self.assertTrue(om)

    def test___getitem___miss(self):
        om = self._makeOne()
        self.assertRaises(KeyError, om.__getitem__, 'nonesuch')

    def test___getitem___miss_w_non_instance_attr(self):
        om = self._makeOne()
        self.assertRaises(KeyError, om.__getitem__, 'get')

    def test___getitem___hit(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        got = om['1']
        self.assertTrue(aq_self(got) is si1)
        self.assertTrue(got.__parent__ is om)

    def test_get_miss_wo_default(self):
        om = self._makeOne()
        self.assertEqual(om.get('nonesuch'), None)

    def test_get_miss_w_default(self):
        om = self._makeOne()
        obj = object()
        self.assertTrue(om.get('nonesuch', obj) is obj)

    def test_get_miss_w_non_instance_attr(self):
        om = self._makeOne()
        self.assertEqual(om.get('get'), None)

    def test_get_hit(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        got = om.get('1')
        self.assertTrue(aq_self(got) is si1)
        self.assertTrue(got.__parent__ is om)

    def test_items(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        self.assertTrue(('1', si1) in list(om.items()))

    def test_keys(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        self.assertTrue('1' in list(om.keys()))

    def test_values(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        self.assertTrue(si1 in list(om.values()))

    def test_list_imports(self):
        om = self._makeOne()
        # This must work whether we've done "make instance" or not.
        # So list_imports() may return an empty list, or whatever's
        # in skel/import. Tolerate both cases.
        self.assertIsInstance(om.list_imports(), list)
        for filename in om.list_imports():
            self.assertTrue(os.path.splitext(filename)[1] in ('.zexp', '.xml'))

    def test_manage_get_sortedObjects_quote_id(self):
        # manage_get_sortedObjects now returns a urlquoted version
        # of the object ID to create correct links in the ZMI
        om = self._makeOne()
        hash_id = '#999'
        om._setObject(hash_id, SimpleItem(hash_id))

        result = om.manage_get_sortedObjects('id', 'asc')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], hash_id)
        self.assertEqual(result[0]['quoted_id'], quote(hash_id))

    def test_getBookmarkableURLs(self):
        saved_state = getattr(getConfiguration(),
                              'zmi_bookmarkable_urls',
                              True)
        om = self._makeOne()

        # Configuration flag OFF
        getConfiguration().zmi_bookmarkable_urls = False
        self.assertFalse(om.getBookmarkableURLs())

        # Configuration flag ON
        getConfiguration().zmi_bookmarkable_urls = True
        self.assertTrue(om.getBookmarkableURLs())

        # Cleanup
        getConfiguration().zmi_bookmarkable_urls = saved_state

    def test_findChildren(self):
        from OFS.Folder import Folder
        from OFS.Image import File
        from OFS.ObjectManager import findChildren
        top = Folder("top")
        f1 = File("f1", "", b"")
        top._setObject(f1.getId(), f1)
        fo = Folder("fo")
        top._setObject(fo.getId(), fo)
        f2 = File("f2", "", b"")
        fo._setObject(f2.getId(), f2)
        self.assertEqual(
            [ci[0] for ci in findChildren(top)],
            ["top/f1",
             # surprisingly, `findChildren` ignores folderish children
             # "top/fo",
             "top/fo/f2"])

    def test_export_import(self):
        import tempfile
        from os import mkdir
        from os import rmdir
        from os import unlink
        from os.path import join
        from os.path import split

        from OFS.Folder import Folder
        from OFS.Image import File
        from transaction import commit
        from ZODB.DB import DB
        from ZODB.DemoStorage import DemoStorage
        try:
            tf = None  # temporary file required for export/import
            # export/import needs the object manager in ZODB
            s = DemoStorage()
            db = DB(s)
            c = db.open()
            root = c.root()
            top = Folder("top")
            f = File("f", "", b"")
            top._setObject(f.getId(), f)
            root["top"] = top
            tmp = Folder("tmp")
            top._setObject(tmp.getId(), tmp)
            commit()
            exported = top.manage_exportObject("f", True)
            tdir = tempfile.mkdtemp()
            idir = join(tdir, "import")
            mkdir(idir)
            tf = tempfile.NamedTemporaryFile(
                dir=idir, delete=False)
            tf.write(exported)
            tf.close()
            unused, tname = split(tf.name)
            tmp._getImportPaths = _CallResult((tdir,))
            tmp.manage_importObject(tname, set_owner=False,
                                    suppress_events=True)
            imp_f = tmp["f"]  # exception if import unsuccessful
            self.assertIsInstance(imp_f, File)
            commit()
        finally:
            if tf is not None:  # pragma: no cover
                unlink(tf.name)
                rmdir(idir)
                rmdir(tdir)
            c.close()
            db.close()
            s.close()


class _CallResult:
    """Auxiliary class to provide defined call results."""
    def __init__(self, result):
        self.result = result

    def __call__(self):
        return self.result


_marker = object()


class TestCheckValidId(unittest.TestCase):

    def _callFUT(self, container, id, allow_dup=_marker):
        from OFS.ObjectManager import checkValidId
        if allow_dup is _marker:
            return checkValidId(container, id)
        return checkValidId(container, id, allow_dup)

    def _makeContainer(self):
        return object()

    def assertBadRequest(self, id, allow_dup=_marker):
        from zExceptions import BadRequest
        try:
            if allow_dup is not _marker:
                self._callFUT(self._makeContainer(), id, allow_dup)
            else:
                self._callFUT(self._makeContainer(), id)
        except BadRequest as e:
            return e
        self.fail("Didn't raise")

    def test_empty_string(self):
        e = self.assertBadRequest('')
        self.assertEqual(str(e),
                         "('Empty or invalid id specified', '')")

    def test_unicode(self):
        self._callFUT(self._makeContainer(), 'abc☃')

    def test_encoded_unicode(self):
        e = self.assertBadRequest('abcö'.encode())
        self.assertEqual(str(e),
                         "('Empty or invalid id specified', "
                         "b'abc\\xc3\\xb6')")

    def test_unprintable_characters(self):
        # We do not allow the first 31 ASCII characters. \x00-\x19
        # We do not allow the DEL character. \x7f
        e = self.assertBadRequest('abc\x10')
        self.assertEqual(str(e),
                         'The id "abc\x10" contains characters illegal'
                         ' in URLs.')
        e = self.assertBadRequest('abc\x7f')
        self.assertEqual(str(e),
                         'The id "abc\x7f" contains characters illegal'
                         ' in URLs.')

    def test_fail_on_brackets_and_ampersand(self):
        # We do not allow this characters as they result in TaintedString (for
        # < and >) which are not allowed in hasattr.
        e = self.assertBadRequest('<abc>&def')
        self.assertEqual(str(e),
                         'The id "&lt;abc&gt;&amp;def" contains characters '
                         'illegal in URLs.')

    def test_one_dot(self):
        e = self.assertBadRequest('.')
        self.assertEqual(str(e),
                         'The id "." is invalid because it is not '
                         'traversable.')

    def test_two_dots(self):
        e = self.assertBadRequest('..')
        self.assertEqual(str(e),
                         'The id ".." is invalid because it is not '
                         'traversable.')

    def test_underscore(self):
        e = self.assertBadRequest('_abc')
        self.assertEqual(str(e),
                         'The id "_abc" is invalid because it begins with '
                         'an underscore.')

    def test_aq_(self):
        e = self.assertBadRequest('aq_abc')
        self.assertEqual(str(e),
                         'The id "aq_abc" is invalid because it begins with '
                         '"aq_".')

    def test_dunder_suffix(self):
        e = self.assertBadRequest('abc__')
        self.assertEqual(str(e),
                         'The id "abc__" is invalid because it ends with '
                         'two underscores.')
