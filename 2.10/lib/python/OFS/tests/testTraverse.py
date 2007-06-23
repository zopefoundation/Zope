##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Traverse unit tests.

$Id$
"""

import unittest

import cStringIO

import transaction
import ZODB, Acquisition, transaction
from AccessControl import SecurityManager, Unauthorized
from AccessControl.Permissions import access_contents_information
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_base
from OFS.Application import Application
from OFS.Folder import manage_addFolder
from OFS.Image import manage_addFile
from OFS.SimpleItem import SimpleItem
from Testing.makerequest import makerequest


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


class ProtectedMethodSecurityPolicy:
    """Check security strictly on bound methods.
    """
    def validate(self, accessed, container, name, value, *args):
        if getattr(aq_base(value), 'im_self', None) is None:
            return 1

        # Bound method
        if name is None:
            raise Unauthorized
        klass = value.im_self.__class__
        roles = getattr(klass, name+'__roles__', object())
        if roles is None: # ACCESS_PUBLIC
            return 1

        raise Unauthorized(name)


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


class Restricted(SimpleItem):
    """Instance we'll check with ProtectedMethodSecurityPolicy
    """
    getId__roles__ = None # ACCESS_PUBLIC
    def getId(self):
        return self.id

    private__roles__ = () # ACCESS_PRIVATE
    def private(self):
        return 'private!'

    # not protected
    def ohno(self):
        return 'ohno!'


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

    def test_z3interfaces(self):
        from OFS.interfaces import ITraversable
        from OFS.Traversable import Traversable
        from zope.interface.verify import verifyClass

        verifyClass(ITraversable, Traversable)

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

    def testTraverseMethodRestricted(self):
        self.root.my = Restricted('my')
        my = self.root.my
        my.id = 'my'
        noSecurityManager()
        SecurityManager.setSecurityPolicy(ProtectedMethodSecurityPolicy())
        r = my.restrictedTraverse('getId')
        self.assertEquals(r(), 'my')
        self.assertRaises(Unauthorized, my.restrictedTraverse, 'private')
        self.assertRaises(Unauthorized, my.restrictedTraverse, 'ohno')

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
                              bb.restrictedTraverse, 'folder1')

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
                              self.app.folder1.restrictedTraverse, 'stuff')

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


import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))


class SimpleClass(object):
    """Class with no __bobo_traverse__."""


def test_traversable():
    """
    Test the behaviour of unrestrictedTraverse and views. The tests are copies
    from Five.browser.tests.test_traversable, but instead of publishing they
    do unrestrictedTraverse.

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> from Testing.makerequest import makerequest
      >>> self.app = makerequest(self.app)
      
    ``SimpleContent`` is a traversable class by default.  Its fallback
    traverser should raise NotFound when traversal fails.  (Note: If
    we return None in __fallback_traverse__, this test passes but for
    the wrong reason: None doesn't have a docstring so BaseRequest
    raises NotFoundError.)

      >>> from Products.Five.tests.testing.simplecontent import manage_addSimpleContent
      >>> manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
      >>> from zExceptions import NotFound
      >>> try:
      ...    self.folder.testoid.unrestrictedTraverse('doesntexist')
      ... except NotFound:
      ...    pass
      
    Now let's take class which already has a __bobo_traverse__ method.
    Five should correctly use that as a fallback.

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            xmlns:meta="http://namespaces.zope.org/meta"
      ...            xmlns:browser="http://namespaces.zope.org/browser"
      ...            xmlns:five="http://namespaces.zope.org/five">
      ... 
      ... <!-- make the zope2.Public permission work -->
      ... <meta:redefinePermission from="zope2.Public" to="zope.Public" />
      ...
      ... <!-- this view will never be found -->
      ... <browser:page
      ...     for="Products.Five.tests.testing.fancycontent.IFancyContent"
      ...     class="Products.Five.browser.tests.pages.FancyView"
      ...     attribute="view"
      ...     name="fancyview"
      ...     permission="zope2.Public"
      ...     />
      ... <!-- these two will -->
      ... <browser:page
      ...     for="Products.Five.tests.testing.fancycontent.IFancyContent"
      ...     class="Products.Five.browser.tests.pages.FancyView"
      ...     attribute="view"
      ...     name="raise-attributeerror"
      ...     permission="zope2.Public"
      ...     />
      ... <browser:page
      ...     for="Products.Five.tests.testing.fancycontent.IFancyContent"
      ...     class="Products.Five.browser.tests.pages.FancyView"
      ...     attribute="view"
      ...     name="raise-keyerror"
      ...     permission="zope2.Public"
      ...     />
      ... </configure>'''
      >>> zcml.load_string(configure_zcml)

      >>> from Products.Five.tests.testing.fancycontent import manage_addFancyContent
      >>> info = manage_addFancyContent(self.folder, 'fancy', '')

    In the following test we let the original __bobo_traverse__ method
    kick in:

      >>> self.folder.fancy.unrestrictedTraverse('something-else').index_html({})
      'something-else'

    Once we have a custom __bobo_traverse__ method, though, it always
    takes over.  Therefore, unless it raises AttributeError or
    KeyError, it will be the only way traversal is done.

      >>> self.folder.fancy.unrestrictedTraverse('fancyview').index_html({})
      'fancyview'
      

    Note that during publishing, if the original __bobo_traverse__ method
    *does* raise AttributeError or KeyError, we can get normal view look-up.
    In unrestrictedTraverse, we don't. Maybe we should? Needs discussing.

      >>> self.folder.fancy.unrestrictedTraverse('raise-attributeerror')()
      u'Fancy, fancy'

      >>> self.folder.fancy.unrestrictedTraverse('raise-keyerror')()
      u'Fancy, fancy'

      >>> try:
      ...     self.folder.fancy.unrestrictedTraverse('raise-valueerror')
      ... except ValueError:
      ...     pass

    In the Zope 2 ZPublisher, an object with a __bobo_traverse__ will not do
    attribute lookup unless the __bobo_traverse__ method itself does it (i.e.
    the __bobo_traverse__ is the only element used for traversal lookup).
    Let's demonstrate:

      >>> from Products.Five.tests.testing.fancycontent import manage_addNonTraversableFancyContent
      >>> info = manage_addNonTraversableFancyContent(self.folder, 'fancy_zope2', '')
      >>> self.folder.fancy_zope2.an_attribute = 'This is an attribute'
      >>> self.folder.fancy_zope2.unrestrictedTraverse('an_attribute').index_html({})
      'an_attribute'

    Without a __bobo_traverse__ method this would have returned the attribute
    value 'This is an attribute'.  Let's make sure the same thing happens for
    an object that has been marked traversable by Five:

      >>> self.folder.fancy.an_attribute = 'This is an attribute'
      >>> self.folder.fancy.unrestrictedTraverse('an_attribute').index_html({})
      'an_attribute'


    Clean up:

      >>> from zope.app.testing.placelesssetup import tearDown
      >>> tearDown()

    Verify that after cleanup, there's no cruft left from five:traversable::

      >>> from Products.Five.browser.tests.test_traversable import SimpleClass
      >>> hasattr(SimpleClass, '__bobo_traverse__')
      False
      >>> hasattr(SimpleClass, '__fallback_traverse__')
      False

      >>> from Products.Five.tests.testing.fancycontent import FancyContent
      >>> hasattr(FancyContent, '__bobo_traverse__')
      True
      >>> hasattr(FancyContent.__bobo_traverse__, '__five_method__')
      False
      >>> hasattr(FancyContent, '__fallback_traverse__')
      False
    """

def test_view_doesnt_shadow_attribute():
    """
    Test that views don't shadow attributes, e.g. items in a folder.

    Let's first define a browser page for object managers called
    ``eagle``:

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            xmlns:meta="http://namespaces.zope.org/meta"
      ...            xmlns:browser="http://namespaces.zope.org/browser"
      ...            xmlns:five="http://namespaces.zope.org/five">
      ...   <!-- make the zope2.Public permission work -->
      ...   <meta:redefinePermission from="zope2.Public" to="zope.Public" />
      ...   <browser:page
      ...       name="eagle"
      ...       for="OFS.interfaces.IObjectManager"
      ...       class="Products.Five.browser.tests.pages.SimpleView"
      ...       attribute="eagle"
      ...       permission="zope2.Public"
      ...       />
      ...   <browser:page
      ...       name="mouse"
      ...       for="OFS.interfaces.IObjectManager"
      ...       class="Products.Five.browser.tests.pages.SimpleView"
      ...       attribute="mouse"
      ...       permission="zope2.Public"
      ...       />
      ... </configure>'''
      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_string(configure_zcml)

    Then we create a traversable folder...

      >>> from Products.Five.tests.testing.folder import manage_addFiveTraversableFolder
      >>> manage_addFiveTraversableFolder(self.folder, 'ftf')

    and add an object called ``eagle`` to it:

      >>> from Products.Five.tests.testing.simplecontent import manage_addIndexSimpleContent
      >>> manage_addIndexSimpleContent(self.folder.ftf, 'eagle', 'Eagle')

    When we publish the ``ftf/eagle`` now, we expect the attribute to
    take precedence over the view during traversal:

      >>> self.folder.ftf.unrestrictedTraverse('eagle').index_html({})
      'Default index_html called'

    Of course, unless we explicitly want to lookup the view using @@:

      >>> self.folder.ftf.unrestrictedTraverse('@@eagle')()
      u'The eagle has landed'


    Some weird implementations of __bobo_traverse__, like the one
    found in OFS.Application, raise NotFound.  Five still knows how to
    deal with this, hence views work there too:

      >>> self.app.unrestrictedTraverse('@@eagle')()
      u'The eagle has landed'

    However, acquired attributes *should* be shadowed. See discussion on
    http://codespeak.net/pipermail/z3-five/2006q2/001474.html

      >>> manage_addIndexSimpleContent(self.folder, 'mouse', 'Mouse')
      >>> self.folder.ftf.unrestrictedTraverse('mouse')()
      u'The mouse has been eaten by the eagle'

    Head requests have some unusual behavior in Zope 2, in particular, a failed
    item lookup on an ObjectManager returns a NullResource, rather
    than raising a KeyError.  We need to make sure that this doesn't
    result in acquired attributes being shadowed by the NullResource,
    but that unknown names still give NullResources:

      >>> self.app.REQUEST.maybe_webdav_client = True
      >>> self.app.REQUEST['REQUEST_METHOD'] = 'HEAD'
      >>> self.folder.ftf.unrestrictedTraverse('mouse')()
      u'The mouse has been eaten by the eagle'
      >>> self.folder.ftf.unrestrictedTraverse('nonsense')
      <webdav.NullResource.NullResource object at ...>


    Clean up:

      >>> from zope.app.testing.placelesssetup import tearDown
      >>> tearDown()
    """

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestTraverse ) )
    from Testing.ZopeTestCase import FunctionalDocTestSuite
    suite.addTest( FunctionalDocTestSuite() )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
