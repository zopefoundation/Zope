import os, sys, unittest

import string, cStringIO, re
import ZODB, Acquisition
from OFS.Application import Application
from OFS.Folder import manage_addFolder
from OFS.Image import manage_addFile
from Testing.makerequest import makerequest
from webdav.common import rfc1123_date
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import newSecurityManager

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

class UnitTestUser( Acquisition.Implicit ):
    """
        Stubbed out manager for unit testing purposes.
    """
    def getId( self ):
        return 'unit_tester'
    
    getUserName = getId

    def allowed( self, object, object_roles=None ):
        return 1

_CONNECTION = None
_ROOT = None
_APP = None

def makeConnection():

    global _CONNECTION
    global _ROOT
    global _APP

    if not _CONNECTION:
        import ZODB
        from ZODB.DemoStorage import DemoStorage
        responseOut = cStringIO.StringIO()
        s = DemoStorage(quota=(1<<20))
        _CONNECTION = ZODB.DB( s ).open()
        try:
            r = _CONNECTION.root()
            a = Application()
            r['Application'] = a
            _ROOT = a
            _APP = makerequest( _ROOT, stdout=responseOut )
            manage_addFolder( _APP, 'folder1' )
            manage_addFolder( _APP, 'folder2' )
            folder1 = getattr( _APP, 'folder1' )
            folder2 = getattr( _APP, 'folder2' )

            folder1.all_meta_types = folder2.all_meta_types = \
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
            get_transaction().commit()
        except:
            _CONNECTION.close()
            raise

    return _CONNECTION, _ROOT, _APP

class TestCopySupport( unittest.TestCase ):
 
    def setUp( self ):

        self.connection, self.root, self.app = makeConnection()
        get_transaction().begin()
        self.folder1 = getattr( self.app, 'folder1' )
        self.folder2 = getattr( self.app, 'folder2' )

        self.policy = UnitTestSecurityPolicy()
        SecurityManager.setSecurityPolicy(self.policy)
        newSecurityManager( None, UnitTestUser().__of__( self.root ) )

    def tearDown( self ):
        del self.policy
        del self.folder1
        del self.folder2
        get_transaction().abort()
        del self.app
        del self.root
        del self.connection

    def testRename( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.folder1.manage_renameObject( id='file', new_id='filex' )
        self.failIf( 'file' in self.folder1.objectIds() )
        self.failUnless( 'filex' in self.folder1.objectIds() )

    def testCopy( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failIf( 'file' in self.folder2.objectIds() )
        cookie = self.folder1.manage_copyObjects( ids=('file',) )
        self.folder2.manage_pasteObjects( cookie )
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failUnless( 'file' in self.folder2.objectIds() )

    def testCut( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failIf( 'file' in self.folder2.objectIds() )
        cookie = self.folder1.manage_cutObjects( ids=('file',) )
        self.folder2.manage_pasteObjects( cookie )
        self.failIf( 'file' in self.folder1.objectIds() )
        self.failUnless( 'file' in self.folder2.objectIds() )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestCopySupport ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()

