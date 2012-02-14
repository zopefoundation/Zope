import unittest

from zope.component.testing import PlacelessSetup

from AccessControl.Owned import EmergencyUserCannotOwn
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.User import User # before SpecialUsers
from AccessControl.SpecialUsers import emergency_user, nobody, system
from Acquisition import aq_base
from Acquisition import Implicit
from App.config import getConfiguration
from logging import getLogger
from OFS.ObjectManager import ObjectManager
from OFS.SimpleItem import SimpleItem
import Products.Five
from Products.Five import zcml
from Products.Five.eventconfigure import setDeprecatedManageAddDelete
from zExceptions import BadRequest

logger = getLogger('OFS.subscribers')            

class FauxRoot( Implicit ):

    id = '/'

    def getPhysicalRoot( self ):
        return self

    def getPhysicalPath( self ):
        return ()

class FauxUser( Implicit ):

    def __init__( self, id, login ):

        self._id = id
        self._login = login

    def getId( self ):

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

from zope.interface import implements
from OFS.interfaces import IItem
class ObjectManagerWithIItem(ObjectManager):
    """The event subscribers work on IItem."""
    implements(IItem)

class ObjectManagerTests(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(ObjectManagerTests, self).setUp()
        self.saved_cfg_debug_mode = getConfiguration().debug_mode
        zcml.load_config('meta.zcml', Products.Five)
        zcml.load_config('event.zcml', Products.Five)
        zcml.load_config('deprecated.zcml', Products.Five)
        setDeprecatedManageAddDelete(ItemForDeletion)

    def tearDown( self ):
        noSecurityManager()
        getConfiguration().debug_mode = self.saved_cfg_debug_mode
        super(ObjectManagerTests, self).tearDown()

    def setDebugMode(self, mode):
        getConfiguration().debug_mode = mode

    def _getTargetClass( self ):
        return ObjectManagerWithIItem

    def _makeOne( self, *args, **kw ):
        return self._getTargetClass()( *args, **kw ).__of__( FauxRoot() )

    def test_z3interfaces(self):
        from OFS.interfaces import IObjectManager
        from OFS.ObjectManager import ObjectManager
        from zope.interface.verify import verifyClass

        verifyClass(IObjectManager, ObjectManager)

    def test_setObject_set_owner_with_no_user( self ):
        om = self._makeOne()
        newSecurityManager( None, None )
        si = SimpleItem( 'no_user' )
        om._setObject( 'no_user', si )
        self.assertEqual( si.__ac_local_roles__, None )

    def test_setObject_set_owner_with_emergency_user( self ):
        om = self._makeOne()
        newSecurityManager( None, emergency_user )
        si = SimpleItem( 'should_fail' )
        self.assertEqual( si.__ac_local_roles__, None )
        self.assertRaises( EmergencyUserCannotOwn
                         , om._setObject, 'should_fail', si )

    def test_setObject_set_owner_with_system_user( self ):
        om = self._makeOne()
        newSecurityManager( None, system )
        si = SimpleItem( 'system' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'system', si )
        self.assertEqual( si.__ac_local_roles__, None )

    def test_setObject_set_owner_with_anonymous_user( self ):
        om = self._makeOne()
        newSecurityManager( None, nobody )
        si = SimpleItem( 'anon' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'anon', si )
        self.assertEqual( si.__ac_local_roles__, None )

    def test_setObject_set_owner_with_user( self ):
        om = self._makeOne()
        user = User( 'user', '123', (), () ).__of__( FauxRoot() )
        newSecurityManager( None, user )
        si = SimpleItem( 'user_creation' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'user_creation', si )
        self.assertEqual( si.__ac_local_roles__, { 'user': ['Owner'] } )

    def test_setObject_set_owner_with_faux_user( self ):
        om = self._makeOne()
        user = FauxUser( 'user_id', 'user_login' ).__of__( FauxRoot() )
        newSecurityManager( None, user )
        si = SimpleItem( 'faux_creation' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'faux_creation', si )
        self.assertEqual( si.__ac_local_roles__, { 'user_id': ['Owner'] } )

    def test_setObject_no_set_owner_with_no_user( self ):
        om = self._makeOne()
        newSecurityManager( None, None )
        si = SimpleItem( 'should_be_okay' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'should_be_okay', si, set_owner=0 )
        self.assertEqual( si.__ac_local_roles__, None )

    def test_setObject_no_set_owner_with_emergency_user( self ):
        om = self._makeOne()
        newSecurityManager( None, emergency_user )
        si = SimpleItem( 'should_be_okay' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'should_be_okay', si, set_owner=0 )
        self.assertEqual( si.__ac_local_roles__, None )

    def test_setObject_no_set_owner_with_system_user( self ):
        om = self._makeOne()
        newSecurityManager( None, system )
        si = SimpleItem( 'should_be_okay' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'should_be_okay', si, set_owner=0 )
        self.assertEqual( si.__ac_local_roles__, None )

    def test_setObject_no_set_owner_with_anonymous_user( self ):
        om = self._makeOne()
        newSecurityManager( None, nobody )
        si = SimpleItem( 'should_be_okay' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'should_be_okay', si, set_owner=0 )
        self.assertEqual( si.__ac_local_roles__, None )

    def test_setObject_no_set_owner_with_user( self ):
        om = self._makeOne()
        user = User( 'user', '123', (), () ).__of__( FauxRoot() )
        newSecurityManager( None, user )
        si = SimpleItem( 'should_be_okay' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'should_be_okay', si, set_owner=0 )
        self.assertEqual( si.__ac_local_roles__, None )

    def test_setObject_no_set_owner_with_faux_user( self ):
        om = self._makeOne()
        user = FauxUser( 'user_id', 'user_login' ).__of__( FauxRoot() )
        newSecurityManager( None, user )
        si = SimpleItem( 'should_be_okay' )
        self.assertEqual( si.__ac_local_roles__, None )
        om._setObject( 'should_be_okay', si, set_owner=0 )
        self.assertEqual( si.__ac_local_roles__, None )

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
        newSecurityManager(None, system) # Manager
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
        newSecurityManager(None, system) # Manager
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

    def test_hasObject(self):
        om = self._makeOne()
        self.failIf(om.hasObject('_properties'))
        self.failIf(om.hasObject('_getOb'))
        self.failIf(om.hasObject('__of__'))
        self.failIf(om.hasObject('.'))
        self.failIf(om.hasObject('..'))
        self.failIf(om.hasObject('aq_base'))
        om.zap__ = True
        self.failIf(om.hasObject('zap__'))
        self.failIf(om.hasObject('foo'))
        si = SimpleItem('foo')
        om._setObject('foo', si)
        self.assert_(om.hasObject('foo'))
        om._delObject('foo')
        self.failIf(om.hasObject('foo'))

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
        self.assertRaises(BadRequest, om._setObject, 'a\\b', si)
        self.assertRaises(BadRequest, om._setObject, 'a:b', si)
        self.assertRaises(BadRequest, om._setObject, 'a;b', si)
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

    def test_getsetitem(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        si2 = SimpleItem('2')
        om['1'] = si1
        self.failUnless('1' in om)
        self.failUnless(si1 in om.objectValues())
        self.failUnless('1' in om.objectIds())
        om['2'] = si2
        self.failUnless('2' in om)
        self.failUnless(si2 in om.objectValues())
        self.failUnless('2' in om.objectIds())
        self.assertRaises(BadRequest, om._setObject, '1', si2)
        self.assertRaises(BadRequest, om.__setitem__, '1', si2)

    def test_delitem(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        si2 = SimpleItem('2')
        om['1'] = si1
        om['2'] = si2
        self.failUnless('1' in om)
        self.failUnless('2' in om)
        del om['1']
        self.failIf('1' in om)
        self.failUnless('2' in om)
        om._delObject('2')
        self.failIf('2' in om)

    def test_iterator(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        si2 = SimpleItem('2')
        om['1'] = si1
        om['2'] = si2
        iterator = iter(om)
        self.failUnless(hasattr(iterator, '__iter__'))
        self.failUnless(hasattr(iterator, 'next'))
        result = [i for i in iterator]
        self.failUnless('1' in result)
        self.failUnless('2' in result)

    def test_len(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        si2 = SimpleItem('2')
        om['1'] = si1
        om['2'] = si2
        self.failUnless(len(om) == 2)

    def test_nonzero(self):
        om = self._makeOne()
        self.failUnless(om)

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
        self.failUnless(got.aq_self is si1)
        self.failUnless(got.aq_parent is om)

    def test_get_miss_wo_default(self):
        om = self._makeOne()
        self.assertEqual(om.get('nonesuch'), None)

    def test_get_miss_w_default(self):
        om = self._makeOne()
        obj = object()
        self.failUnless(om.get('nonesuch', obj) is obj)

    def test_get_miss_w_non_instance_attr(self):
        om = self._makeOne()
        self.assertEqual(om.get('get'), None)

    def test_get_hit(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        got = om.get('1')
        self.failUnless(got.aq_self is si1)
        self.failUnless(got.aq_parent is om)

    def test_items(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        self.failUnless(('1', si1) in om.items())

    def test_keys(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        self.failUnless('1' in om.keys())

    def test_values(self):
        om = self._makeOne()
        si1 = SimpleItem('1')
        om['1'] = si1
        self.failUnless(si1 in om.values())

    def test_list_imports(self):
        om = self._makeOne()
        # This must work whether we've done "make instance" or not.
        # So list_imports() may return an empty list, or whatever's
        # in skel/import. Tolerate both cases.
        self.failUnless(isinstance(om.list_imports(), list))
        for filename in om.list_imports():
            self.failUnless(filename.endswith('.zexp') or
                            filename.endswith('.xml'))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( ObjectManagerTests ) )
    return suite

if __name__ == "__main__":
    unittest.main()
