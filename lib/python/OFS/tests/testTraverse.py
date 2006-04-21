##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os, sys, unittest
import string, cStringIO, re

import ZODB, Acquisition, transaction
import transaction
from Acquisition import aq_base
from OFS.Application import Application
from OFS.Folder import manage_addFolder
from OFS.Image import manage_addFile
from OFS.SimpleItem import SimpleItem
from Testing.makerequest import makerequest
from AccessControl import SecurityManager, Unauthorized
from AccessControl.Permissions import access_contents_information
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

from mimetools import Message
from multifile import MultiFile


class UnitTestSecurityPolicy:
    """
        Stub out the existing security policy for unit testing purposes.
    """
    #
    #   Standard SecurityPolicy interface
    #
    def validate( self
                , accessed=None
                , container=None
                , name=None
                , value=None
                , context=None
                , roles=None
                , *args
                , **kw):
        return 1

    def checkPermission( self, permission, object, context) :
        return 1


class CruelSecurityPolicy:
    """Denies everything
    """
    #
    #   Standard SecurityPolicy interface
    #
    def validate(self, accessed, container, name, value, *args):
        raise Unauthorized, name

    def checkPermission( self, permission, object, context) :
        return 0


class UnitTestUser( Acquisition.Implicit ):
    """
        Stubbed out manager for unit testing purposes.
    """
    def getId( self ):
        return 'unit_tester'

    getUserName = getId

    def allowed( self, object, object_roles=None ):
        return 1


class BoboTraversable(SimpleItem):
    __allow_access_to_unprotected_subobjects__ = 1

    def __bobo_traverse__(self, request, name):
        if name == 'bb_subitem':
            return BoboTraversable().__of__(self)
        elif name == 'bb_method':
            return self.bb_method
        elif name == 'bb_status':
            return self.bb_status
        elif name == 'manufactured':
            return 42
        else:
            raise KeyError
    
    def bb_method(self):
        """Test Method"""
        pass
        
    bb_status = 'screechy'


class BoboTraversableWithAcquisition(SimpleItem):
    """
       A BoboTraversable class which may use acquisition to find objects.
       This is similar to how the __bobo_traverse__ added by Five behaves).
    """

    def __bobo_traverse__(self, request, name):
        return Acquisition.aq_get(self, name)


def makeConnection():
    import ZODB
    from ZODB.DemoStorage import DemoStorage

    s = DemoStorage(quota=(1<<20))
    return ZODB.DB( s ).open()


class TestTraverse( unittest.TestCase ):

    def setUp( self ):

        self.connection = makeConnection()
        try:
            r = self.connection.root()
            a = Application()
            r['Application'] = a
            self.root = a
            responseOut = self.responseOut = cStringIO.StringIO()
            self.app = makerequest( self.root, stdout=responseOut )
            manage_addFolder( self.app, 'folder1' )
            folder1 = getattr( self.app, 'folder1' )

            folder1.all_meta_types = \
                                    ( { 'name'        : 'File'
                                      , 'action'      : 'manage_addFile'
                                      , 'permission'  : 'Add images and files'
                                      }
                                    ,
                                    )

            manage_addFile( folder1, 'file'
                          , file='', content_type='text/plain')

            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one. We use a subtransaction, which means we can rollback
            # later and pretend we didn't touch the ZODB.
            transaction.commit()
        except:
            self.connection.close()
            raise
        transaction.begin()
        self.folder1 = getattr( self.app, 'folder1' )

        self.policy = UnitTestSecurityPolicy()
        self.oldPolicy = SecurityManager.setSecurityPolicy( self.policy )
        newSecurityManager( None, UnitTestUser().__of__( self.root ) )

    def tearDown( self ):
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        del self.oldPolicy
        del self.policy
        del self.folder1
        transaction.abort()
        self.app._p_jar.sync()
        self.connection.close()
        del self.app
        del self.responseOut
        del self.root
        del self.connection

    def testTraversePath( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failUnless( 
            self.folder1.unrestrictedTraverse( ('', 'folder1', 'file' ) ))
        self.failUnless( 
            self.folder1.unrestrictedTraverse( ('', 'folder1' ) ))

    def testTraverseURLNoSlash( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failUnless( 
            self.folder1.unrestrictedTraverse( '/folder1/file' ))
        self.failUnless( 
            self.folder1.unrestrictedTraverse( '/folder1' ))

    def testTraverseURLSlash( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failUnless( self.folder1.unrestrictedTraverse( '/folder1/file/' ))
        self.failUnless( self.folder1.unrestrictedTraverse( '/folder1/' ))

    def testTraverseToNone( self ):
        self.failUnlessRaises( 
            KeyError, 
            self.folder1.unrestrictedTraverse, ('', 'folder1', 'file2' ) )
        self.failUnlessRaises( 
            KeyError, self.folder1.unrestrictedTraverse,  '/folder1/file2' )
        self.failUnlessRaises( 
            KeyError, self.folder1.unrestrictedTraverse,  '/folder1/file2/' )

    def testBoboTraverseToWrappedSubObj(self):
        # Verify it's possible to use __bobo_traverse__ with the
        # Zope security policy.
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        bb = BoboTraversable()
        self.failUnlessRaises(KeyError, bb.restrictedTraverse, 'notfound')
        bb.restrictedTraverse('bb_subitem')

    def testBoboTraverseToMethod(self):
        # Verify it's possible to use __bobo_traverse__ to a method.
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        bb = BoboTraversable()
        self.failUnless(
            bb.restrictedTraverse('bb_method') is not bb.bb_method)

    def testBoboTraverseToSimpleAttrValue(self):
        # Verify it's possible to use __bobo_traverse__ to a simple
        # python value
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        bb = BoboTraversable()
        self.assertEqual(bb.restrictedTraverse('bb_status'), 'screechy')

    def testBoboTraverseToNonAttrValue(self):
        # Verify it's possible to use __bobo_traverse__ to an
        # arbitrary manufactured object
        noSecurityManager()
        # Default security policy always seems to deny in this case, which
        # is fine, but to test the code branch we sub in the forgiving one
        SecurityManager.setSecurityPolicy(UnitTestSecurityPolicy())
        bb = BoboTraversable()
        self.failUnless(
            bb.restrictedTraverse('manufactured') is 42)

    def testBoboTraverseToAcquiredObject(self):
        # Verify it's possible to use a __bobo_traverse__ which retrieves
        # objects by acquisition
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        bb = BoboTraversableWithAcquisition()
        bb = bb.__of__(self.root)
        self.assertEqual(
            bb.restrictedTraverse('folder1'), bb.folder1)
        self.assertEqual(
            Acquisition.aq_inner(bb.restrictedTraverse('folder1')),
            self.root.folder1)

    def testBoboTraverseToAcquiredProtectedObject(self):
        # Verify it's possible to use a __bobo_traverse__ which retrieves
        # objects by acquisition
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        folder = self.root.folder1
        # restrict the ability to access the retrieved object itself
        folder.manage_permission(access_contents_information, [], 0)
        bb = BoboTraversableWithAcquisition()
        bb = bb.__of__(self.root)
        self.failUnlessRaises(Unauthorized,
                              self.root.folder1.restrictedTraverse, 'folder1')

    def testBoboTraverseToAcquiredAttribute(self):
        # Verify it's possible to use __bobo_traverse__ to an acquired
        # attribute
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        folder = self.root.folder1
        folder.stuff = 'stuff here'
        bb = BoboTraversableWithAcquisition()
        bb = bb.__of__(folder)
        self.assertEqual(
            bb.restrictedTraverse('stuff'), 'stuff here')

    def testBoboTraverseToAcquiredProtectedAttribute(self):
        # Verify that using __bobo_traverse__ to get an acquired but
        # protected attribute results in Unauthorized
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        folder = self.root.folder1
        # We protect the the attribute by restricting access to the parent
        folder.manage_permission(access_contents_information, [], 0)
        folder.stuff = 'stuff here'
        bb = BoboTraversableWithAcquisition()
        bb = bb.__of__(folder)
        self.failUnlessRaises(Unauthorized,
                              self.root.folder1.restrictedTraverse, 'stuff')

    def testAcquiredAttributeDenial(self):
        # Verify that restrictedTraverse raises the right kind of exception
        # on denial of access to an acquired attribute.  If it raises
        # AttributeError instead of Unauthorized, the user may never
        # be prompted for HTTP credentials.
        noSecurityManager()
        SecurityManager.setSecurityPolicy(CruelSecurityPolicy())
        newSecurityManager( None, UnitTestUser().__of__( self.root ) )
        self.root.stuff = 'stuff here'
        self.failUnlessRaises(Unauthorized,
                              self.root.folder1.restrictedTraverse, 'stuff')
    
    def testDefaultValueWhenUnathorized(self):
        # Test that traversing to an unauthorized object returns
        # the default when provided
        noSecurityManager()
        SecurityManager.setSecurityPolicy(CruelSecurityPolicy())
        newSecurityManager( None, UnitTestUser().__of__( self.root ) )
        self.root.stuff = 'stuff here'
        self.assertEqual(
            self.root.folder1.restrictedTraverse('stuff', 42), 42)
    
    def testDefaultValueWhenNotFound(self):
        # Test that traversing to a non-existent object returns
        # the default when provided
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        self.assertEqual(
            self.root.restrictedTraverse('happy/happy', 'joy'), 'joy')
            
    def testTraverseUp(self):
        # Test that we can traverse upwards
        self.failUnless(
            aq_base(self.root.folder1.file.restrictedTraverse('../..')) is
            aq_base(self.root))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestTraverse ) )
    return suite

def main():
    unittest.main(defaultTest='test_suite')

if __name__ == '__main__':
    main()
