# Added to test new ObjectManager functions
# for death to index_html implementation
# Not really a complete test suite for OM yet -Casey

import os, sys, unittest

import string, cStringIO, re
import ZODB, Acquisition
from OFS.Application import Application
from OFS.Folder import manage_addFolder
from OFS.Image import manage_addFile
from OFS.ObjectManager import BadRequestException
from Testing.makerequest import makerequest
from webdav.common import rfc1123_date
from AccessControl import SecurityManager
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

class UnitTestUser( Acquisition.Implicit ):
    """
        Stubbed out manager for unit testing purposes.
    """
    def getId( self ):
        return 'unit_tester'
    
    getUserName = getId

    def allowed( self, object, object_roles=None ):
        return 1

def makeConnection():
    import ZODB
    from ZODB.DemoStorage import DemoStorage

    s = DemoStorage(quota=(1<<20))
    return ZODB.DB( s ).open()

def test_browser_default(self, request):
    return self, ('foo.html',)

class TestObjectManager( unittest.TestCase ):
 
    def setUp( self ):

        self.connection = makeConnection()
        try:
            r = self.connection.root()
            a = Application()
            a.manage_addFolder = manage_addFolder
            r['Application'] = a
            self.root = a
            responseOut = self.responseOut = cStringIO.StringIO()
            self.app = makerequest( self.root, stdout=responseOut )
            manage_addFolder( self.app, 'folder1' )
            self.folder1 = folder1 = getattr( self.app, 'folder1' )
            manage_addFolder( folder1, 'folder2' )
            self.folder2 = folder2 = getattr( folder1, 'folder2' )

            folder1.all_meta_types = folder2.all_meta_types = \
                                    ( { 'name'        : 'File'
                                      , 'action'      : 'manage_addFile'
                                      , 'permission'  : 'Add images and files'
                                      },
                                      { 'name':'Some Folderish',
                                        'action':'manage_addFolder', 
                                        'permission':'Add Some Folderish'
                                      },
                                      { 'name':'Folder',
                                        'action':'manage_addFolder', 
                                        'permission':'Add Folders' }
                                    )

            manage_addFile( folder1, 'other_html'
                          , file='', content_type='text/plain')
            manage_addFile( folder1, 'index_html'
                          , file='', content_type='text/plain')

            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one. We use a subtransaction, which means we can rollback
            # later and pretend we didn't touch the ZODB.
            get_transaction().commit()
        except:
            self.connection.close()
            raise
        get_transaction().begin()

        self.policy = UnitTestSecurityPolicy()
        self.oldPolicy = SecurityManager.setSecurityPolicy( self.policy )
        newSecurityManager( None, UnitTestUser().__of__( self.root ) )

    def tearDown( self ):
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        del self.oldPolicy
        del self.policy
        del self.folder2
        del self.folder1
        get_transaction().abort()
        self.app._p_jar.sync()
        self.connection.close()
        del self.app
        del self.responseOut
        del self.root
        del self.connection

    def testSetBrowserDefaultBogus( self ):
        # try to change it to an invalid id
        try:
            self.folder1.setBrowserDefaultId('_bogus')
            self.fail()
        except BadRequestException:
            pass
        # Try to override a custom browser_default
        try:
            self.folder1.browser_default = test_browser_default            
            self.folder1.setBrowserDefaultId('index_html')
            self.fail()
        except BadRequestException:
            del self.folder1.browser_default
    
    def testBrowserDefault( self ):
        # Test setting and acquisition of setting
        self.failUnless( self.folder1.isBrowserDefaultAcquired() )
        self.folder1.setBrowserDefaultId('other_html')
        self.failIf( self.folder1.isBrowserDefaultAcquired() )
        self.assertEqual( self.folder1.getBrowserDefaultId(), 'other_html')
        self.assertEqual( self.folder2.getBrowserDefaultId(), None )
        self.assertEqual( self.folder2.getBrowserDefaultId(1), 'other_html' )
        self.folder1.setBrowserDefaultId(acquire=1)
        self.failUnless( self.folder1.isBrowserDefaultAcquired() )
        self.assertEqual( self.folder1.getBrowserDefaultId(), None )
        default = self.root.getBrowserDefaultId()
        self.assertEqual( self.folder1.getBrowserDefaultId(1), default )
        self.assertEqual( self.folder2.getBrowserDefaultId(1), default )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestObjectManager ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()

