import unittest

from Acquisition import Implicit, aq_base, aq_parent
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.User import User
from AccessControl.SpecialUsers import emergency_user, nobody, system
from AccessControl.Owned import EmergencyUserCannotOwn, Owned
from OFS.ObjectManager import ObjectManager
from OFS.SimpleItem import SimpleItem

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

class ObjectManagerTests( unittest.TestCase ):

    def tearDown( self ):

        noSecurityManager()

    def _getTargetClass( self ):

        from OFS.ObjectManager import ObjectManager

        return ObjectManager

    def _makeOne( self, *args, **kw ):

        return self._getTargetClass()( *args, **kw ).__of__( FauxRoot() )

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

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( ObjectManagerTests ) )
    return suite

if __name__ == "__main__":
    unittest.main()
