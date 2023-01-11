##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""

import unittest


class UnitTestSecurityPolicy:
    """
        Stub out the existing security policy for unit testing purposes.
    """
    #   Standard SecurityPolicy interface
    def validate(self, accessed=None, container=None, name=None, value=None,
                 context=None, roles=None, *args, **kw):
        return 1

    def checkPermission(self, permission, object, context):
        return 1


class CruelSecurityPolicy:
    """Denies everything
    """
    #   Standard SecurityPolicy interface
    def validate(self, accessed, container, name, value, *args):
        from AccessControl import Unauthorized
        raise Unauthorized(name)

    def checkPermission(self, permission, object, context):
        return 0


class ProtectedMethodSecurityPolicy:
    """Check security strictly on bound methods.
    """
    def validate(self, accessed, container, name, value, *args):
        from AccessControl import Unauthorized
        from Acquisition import aq_base
        if getattr(aq_base(value), '__self__', None) is None:
            return 1

        # Bound method
        if name is None:
            raise Unauthorized
        klass = value.__self__.__class__
        roles = getattr(klass, name + '__roles__', object())
        if roles is None:  # ACCESS_PUBLIC
            return 1

        raise Unauthorized(name)


class TestTraverse(unittest.TestCase):

    def setUp(self):
        import io

        import transaction
        from AccessControl import SecurityManager
        from AccessControl.SecurityManagement import newSecurityManager
        from OFS.Application import Application
        from OFS.Folder import manage_addFolder
        from OFS.Image import manage_addFile
        from Testing.makerequest import makerequest
        from ZODB.DB import DB
        from ZODB.DemoStorage import DemoStorage

        s = DemoStorage()
        self.connection = DB(s).open()

        try:
            r = self.connection.root()
            a = Application()
            r['Application'] = a
            self.root = a
            responseOut = self.responseOut = io.BytesIO()
            self.app = makerequest(self.root, stdout=responseOut)
            manage_addFolder(self.app, 'folder1')
            folder1 = getattr(self.app, 'folder1')
            setattr(folder1, '+something', 'plus')

            folder1.all_meta_types = (
                {'name': 'File',
                 'action': 'manage_addFile',
                 'permission': 'Add images and files'
                 },
            )

            manage_addFile(folder1, 'file',
                           file=b'', content_type='text/plain')

            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one. We use a subtransaction, which means we can rollback
            # later and pretend we didn't touch the ZODB.
            transaction.commit()
        except Exception:
            self.connection.close()
            raise
        transaction.begin()
        self.folder1 = getattr(self.app, 'folder1')

        self.policy = UnitTestSecurityPolicy()
        self.oldPolicy = SecurityManager.setSecurityPolicy(self.policy)
        newSecurityManager(None, self._makeUser().__of__(self.root))

    def tearDown(self):
        import transaction
        self._setupSecurity()
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

    def _makeUser(self):
        from Acquisition import Implicit

        class UnitTestUser(Implicit):
            """
                Stubbed out manager for unit testing purposes.
            """
            def getId(self):
                return 'unit_tester'
            getUserName = getId

            def allowed(self, object, object_roles=None):
                return 1

        return UnitTestUser()

    def _makeBoboTraversable(self):
        from OFS.SimpleItem import SimpleItem

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

        return BoboTraversable()

    def _makeBoboTraversableWithAcquisition(self):
        from OFS.SimpleItem import SimpleItem

        class BoboTraversableWithAcquisition(SimpleItem):
            """ A BoboTraversable which may use acquisition to find objects.

            This is similar to how the __bobo_traverse__ behaves).
            """

            def __bobo_traverse__(self, request, name):
                from Acquisition import aq_get
                return aq_get(self, name)

        return BoboTraversableWithAcquisition()

    def _makeRestricted(self, name='dummy'):
        from OFS.SimpleItem import SimpleItem

        class Restricted(SimpleItem):
            """Instance we'll check with ProtectedMethodSecurityPolicy."""

            getId__roles__ = None  # ACCESS_PUBLIC
            def getId(self):  # NOQA: E306  # pseudo decorator
                return self.id

            private__roles__ = ()  # ACCESS_PRIVATE
            def private(self):  # NOQA: E306  # pseudo decorator
                return 'private!'

            # not protected
            def ohno(self):
                return 'ohno!'

        return Restricted(name)

    def _setupSecurity(self, policy=None):
        from AccessControl import SecurityManager
        from AccessControl.SecurityManagement import noSecurityManager
        if policy is None:
            policy = self.oldPolicy
        noSecurityManager()
        SecurityManager.setSecurityPolicy(policy)

    def test_interfaces(self):
        from OFS.interfaces import ITraversable
        from OFS.Traversable import Traversable
        from zope.interface.verify import verifyClass

        verifyClass(ITraversable, Traversable)

    def testTraversePath(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertTrue(
            self.folder1.unrestrictedTraverse(('', 'folder1', 'file')))
        self.assertTrue(self.folder1.unrestrictedTraverse(('', 'folder1')))

    def testTraverseURLNoSlash(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertTrue(self.folder1.unrestrictedTraverse('/folder1/file'))
        self.assertTrue(self.folder1.unrestrictedTraverse('/folder1'))

    def testTraverseURLSlash(self):
        self.assertTrue('file' in self.folder1.objectIds())
        self.assertTrue(self.folder1.unrestrictedTraverse('/folder1/file/'))
        self.assertTrue(self.folder1.unrestrictedTraverse('/folder1/'))

    def testTraverseToNone(self):
        self.assertRaises(
            KeyError,
            self.folder1.unrestrictedTraverse, ('', 'folder1', 'file2'))
        self.assertRaises(
            KeyError, self.folder1.unrestrictedTraverse, '/folder1/file2')
        self.assertRaises(
            KeyError, self.folder1.unrestrictedTraverse, '/folder1/file2/')

    def testTraverseMethodRestricted(self):
        from AccessControl import Unauthorized
        self.root.my = self._makeRestricted('my')
        my = self.root.my
        my.id = 'my'
        self._setupSecurity(ProtectedMethodSecurityPolicy())
        r = my.restrictedTraverse('getId')
        self.assertEqual(r(), 'my')
        self.assertRaises(Unauthorized, my.restrictedTraverse, 'private')
        self.assertRaises(Unauthorized, my.restrictedTraverse, 'ohno')

    def testBoboTraverseToWrappedSubObj(self):
        # Verify it's possible to use __bobo_traverse__ with the
        # Zope security policy.
        self._setupSecurity()
        bb = self._makeBoboTraversable()
        self.assertRaises(KeyError, bb.restrictedTraverse, 'notfound')
        bb.restrictedTraverse('bb_subitem')

    def testBoboTraverseToMethod(self):
        # Verify it's possible to use __bobo_traverse__ to a method.
        self._setupSecurity()
        bb = self._makeBoboTraversable()
        self.assertTrue(
            bb.restrictedTraverse('bb_method') is not bb.bb_method)

    def testBoboTraverseToSimpleAttrValue(self):
        # Verify it's possible to use __bobo_traverse__ to a simple
        # python value
        self._setupSecurity()
        bb = self._makeBoboTraversable()
        self.assertEqual(bb.restrictedTraverse('bb_status'), 'screechy')

    def testBoboTraverseToNonAttrValue(self):
        # Verify it's possible to use __bobo_traverse__ to an
        # arbitrary manufactured object
        # Default security policy always seems to deny in this case, which
        # is fine, but to test the code branch we sub in the forgiving one
        self._setupSecurity(UnitTestSecurityPolicy())
        bb = self._makeBoboTraversable()
        self.assertTrue(
            bb.restrictedTraverse('manufactured') == 42)

    def testBoboTraverseToAcquiredObject(self):
        # Verify it's possible to use a __bobo_traverse__ which retrieves
        # objects by acquisition
        from Acquisition import aq_inner
        self._setupSecurity()
        bb = self._makeBoboTraversableWithAcquisition()
        bb = bb.__of__(self.root)
        self.assertEqual(
            bb.restrictedTraverse('folder1'), bb.folder1)
        self.assertEqual(
            aq_inner(bb.restrictedTraverse('folder1')),
            self.root.folder1)

    def testBoboTraverseToAcquiredProtectedObject(self):
        # Verify it's possible to use a __bobo_traverse__ which retrieves
        # objects by acquisition
        from AccessControl import Unauthorized
        from AccessControl.Permissions import access_contents_information
        self._setupSecurity()
        folder = self.root.folder1
        # restrict the ability to access the retrieved object itself
        folder.manage_permission(access_contents_information, [], 0)
        bb = self._makeBoboTraversableWithAcquisition()
        bb = bb.__of__(self.root)
        self.assertRaises(Unauthorized,
                          bb.restrictedTraverse, 'folder1')

    def testBoboTraverseToAcquiredAttribute(self):
        # Verify it's possible to use __bobo_traverse__ to an acquired
        # attribute
        self._setupSecurity()
        folder = self.root.folder1
        folder.stuff = 'stuff here'
        bb = self._makeBoboTraversableWithAcquisition()
        bb = bb.__of__(folder)
        self.assertEqual(
            bb.restrictedTraverse('stuff'), 'stuff here')

    def testBoboTraverseToAcquiredProtectedAttribute(self):
        # Verify that using __bobo_traverse__ to get an acquired but
        # protected attribute results in Unauthorized
        from AccessControl import Unauthorized
        from AccessControl.Permissions import access_contents_information
        self._setupSecurity()
        folder = self.root.folder1
        # We protect the the attribute by restricting access to the parent
        folder.manage_permission(access_contents_information, [], 0)
        folder.stuff = 'stuff here'
        bb = self._makeBoboTraversableWithAcquisition()
        bb = bb.__of__(folder)
        self.assertRaises(Unauthorized,
                          self.root.folder1.restrictedTraverse, 'stuff')

    def testBoboTraverseTraversalDefault(self):
        from OFS.SimpleItem import SimpleItem
        from ZPublisher.interfaces import UseTraversalDefault

        class BoboTraversableUseTraversalDefault(SimpleItem):
            """
              A BoboTraversable class which may use "UseTraversalDefault"
              (dependent on "name") to indicate that standard traversal should
              be used.
            """
            default = 'Default'

            def __bobo_traverse__(self, request, name):
                if name == 'normal':
                    return 'Normal'
                raise UseTraversalDefault

        bb = BoboTraversableUseTraversalDefault()
        # normal access -- no traversal default used
        self.assertEqual(bb.unrestrictedTraverse('normal'), 'Normal')
        # use traversal default
        self.assertEqual(bb.unrestrictedTraverse('default'), 'Default')
        # test traversal default with acqires attribute
        si = SimpleItem()
        si.default_acquire = 'Default_Acquire'
        si.bb = bb
        self.assertEqual(si.unrestrictedTraverse('bb/default_acquire'),
                         'Default_Acquire')

    def testAcquiredAttributeDenial(self):
        # Verify that restrictedTraverse raises the right kind of exception
        # on denial of access to an acquired attribute.  If it raises
        # AttributeError instead of Unauthorized, the user may never
        # be prompted for HTTP credentials.
        from AccessControl import Unauthorized
        from AccessControl.SecurityManagement import newSecurityManager
        self._setupSecurity(CruelSecurityPolicy())
        newSecurityManager(None, self._makeUser().__of__(self.root))
        self.root.stuff = 'stuff here'
        self.assertRaises(Unauthorized,
                          self.app.folder1.restrictedTraverse, 'stuff')

    def testDefaultValueWhenUnathorized(self):
        # Test that traversing to an unauthorized object returns
        # the default when provided
        from AccessControl.SecurityManagement import newSecurityManager
        self._setupSecurity(CruelSecurityPolicy())
        newSecurityManager(None, self._makeUser().__of__(self.root))
        self.root.stuff = 'stuff here'
        self.assertEqual(
            self.root.folder1.restrictedTraverse('stuff', 42), 42)

    def testNotFoundIsRaised(self):
        from operator import getitem

        from OFS.SimpleItem import SimpleItem
        from zExceptions import NotFound
        self.folder1._setObject('foo', SimpleItem('foo'))
        self.assertRaises(AttributeError, getitem, self.folder1.foo,
                          'doesntexist')
        self.assertRaises(NotFound, self.folder1.unrestrictedTraverse,
                          'foo/doesntexist')
        self.assertRaises(TypeError, getitem,
                          self.folder1.foo.isPrincipiaFolderish, 'doesntexist')
        self.assertRaises(NotFound, self.folder1.unrestrictedTraverse,
                          'foo/isPrincipiaFolderish/doesntexist')

    def testDefaultValueWhenNotFound(self):
        # Test that traversing to a non-existent object returns
        # the default when provided
        self._setupSecurity()
        self.assertEqual(
            self.root.restrictedTraverse('happy/happy', 'joy'), 'joy')

    def testTraverseUp(self):
        # Test that we can traverse upwards
        from Acquisition import aq_base
        self.assertTrue(
            aq_base(self.root.folder1.file.restrictedTraverse('../..')) is
            aq_base(self.root))

    def testTraverseToNameStartingWithPlus(self):
        # Verify it's possible to traverse to a name such as +something
        self.assertTrue(
            self.folder1.unrestrictedTraverse('+something') == 'plus')

    def testTraverseWrongType(self):
        with self.assertRaises(TypeError):
            self.folder1.unrestrictedTraverse(1)
        with self.assertRaises(TypeError):
            self.folder1.unrestrictedTraverse(b"foo")
        with self.assertRaises(TypeError):
            self.folder1.unrestrictedTraverse(["foo", b"bar"])
        with self.assertRaises(TypeError):
            self.folder1.unrestrictedTraverse(("foo", None))
        with self.assertRaises(TypeError):
            self.folder1.unrestrictedTraverse({1, "foo"})

    def testTraverseEmptyPath(self):
        self.assertEqual(self.folder1.unrestrictedTraverse(None), self.folder1)
        self.assertEqual(self.folder1.unrestrictedTraverse(""), self.folder1)
        self.assertEqual(self.folder1.unrestrictedTraverse([]), self.folder1)
        self.assertEqual(self.folder1.unrestrictedTraverse({}), self.folder1)


class SimpleClass:
    """Class with no __bobo_traverse__."""


def test_traversable():
    """
    Test the behaviour of unrestrictedTraverse and views. The tests don't
    use publishing but do unrestrictedTraverse instead.

      >>> import Products.Five
      >>> from Zope2.App import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> from Testing.makerequest import makerequest
      >>> self.app = makerequest(self.app)  # NOQA: F821
      >>> folder = self.folder  # NOQA: F821

    ``SimpleContent`` is a traversable class by default.  Its fallback
    traverser should raise NotFound when traversal fails.  (Note: If
    we return None in __fallback_traverse__, this test passes but for
    the wrong reason: None doesn't have a docstring so BaseRequest
    raises NotFoundError.)

      >>> from Products.Five.tests.testing import simplecontent
      >>> simplecontent.manage_addSimpleContent(folder, 'testoid', 'Testoid')
      >>> from zExceptions import NotFound
      >>> try:
      ...    folder.testoid.unrestrictedTraverse('doesntexist')
      ... except NotFound:
      ...    pass

    Now let's take class which already has a __bobo_traverse__ method.
    We should correctly use that as a fallback.

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
      ... <!-- an item that can be traversed to via adaptation -->
      ... <browser:page
      ...     for="*"
      ...     class="Products.Five.tests.testing.fancycontent.FancyContent"
      ...     name="acquirer"
      ...     permission="zope2.Public"
      ...     />
      ... </configure>'''
      >>> zcml.load_string(configure_zcml)

      >>> from Products.Five.tests.testing import fancycontent
      >>> info = fancycontent.manage_addFancyContent(folder, 'fancy', '')

    In the following test we let the original __bobo_traverse__ method
    kick in:

      >>> folder.fancy.unrestrictedTraverse('something-else'
      ...                                       ).index_html({})
      'something-else'

    Once we have a custom __bobo_traverse__ method, though, it always
    takes over.  Therefore, unless it raises AttributeError or
    KeyError, it will be the only way traversal is done.

      >>> folder.fancy.unrestrictedTraverse('fancyview').index_html({})
      'fancyview'

    Note that during publishing, if the original __bobo_traverse__ method
    *does* raise AttributeError or KeyError, we can get normal view look-up.
    In unrestrictedTraverse, we don't. Maybe we should? Needs discussing.

      >>> folder.fancy.unrestrictedTraverse(
      ...     'raise-attributeerror')() == 'Fancy, fancy'
      True

      >>> folder.fancy.unrestrictedTraverse(
      ...     'raise-keyerror')() == 'Fancy, fancy'
      True

      >>> try:
      ...     folder.fancy.unrestrictedTraverse('raise-valueerror')
      ... except ValueError:
      ...     pass

    In the Zope 2 ZPublisher, an object with a __bobo_traverse__ will not do
    attribute lookup unless the __bobo_traverse__ method itself does it (i.e.
    the __bobo_traverse__ is the only element used for traversal lookup).
    Let's demonstrate:

      >>> from Products.Five.tests.testing import fancycontent
      >>> info = fancycontent.manage_addNonTraversableFancyContent(
      ...                                      folder, 'fancy_zope2', '')
      >>> folder.fancy_zope2.an_attribute = 'This is an attribute'
      >>> folder.fancy_zope2.unrestrictedTraverse(
      ...                             'an_attribute').index_html({})
      'an_attribute'

    Without a __bobo_traverse__ method this would have returned the attribute
    value 'This is an attribute'.  Let's make sure the same thing happens for
    an object that has been marked traversable:

      >>> folder.fancy.an_attribute = 'This is an attribute'
      >>> folder.fancy.unrestrictedTraverse(
      ...                             'an_attribute').index_html({})
      'an_attribute'

    If we traverse to something via an adapter lookup and it provides
    IAcquirer, it should get acquisition-wrapped so we can acquire
    attributes implicitly:

      >>> acquirer = folder.unrestrictedTraverse('acquirer')
      >>> acquirer.fancy
      <FancyContent ...>

    Clean up:

      >>> from zope.component.testing import tearDown
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
      >>> from Zope2.App import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_string(configure_zcml)
      >>> folder = self.folder  # NOQA: F821

    Then we create a traversable folder...

      >>> from Products.Five.tests.testing import folder as ftf
      >>> ftf.manage_addFiveTraversableFolder(folder, 'ftf')

    and add an object called ``eagle`` to it:

      >>> from Products.Five.tests.testing import simplecontent
      >>> simplecontent.manage_addIndexSimpleContent(folder.ftf,
      ...                                            'eagle', 'Eagle')

    When we publish the ``ftf/eagle`` now, we expect the attribute to
    take precedence over the view during traversal:

      >>> folder.ftf.unrestrictedTraverse('eagle').index_html({})
      'Default index_html called'

    Of course, unless we explicitly want to lookup the view using @@:

      >>> folder.ftf.unrestrictedTraverse(
      ...     '@@eagle')() == 'The eagle has landed'
      True

    Some weird implementations of __bobo_traverse__, like the one
    found in OFS.Application, raise NotFound.  Five still knows how to
    deal with this, hence views work there too:

      >>> res = self.app.unrestrictedTraverse('@@eagle')()  # NOQA: F821
      >>> res == 'The eagle has landed'
      True

    However, acquired attributes *should* be shadowed. See discussion on
    http://codespeak.net/pipermail/z3-five/2006q2/001474.html

      >>> simplecontent.manage_addIndexSimpleContent(folder,
      ...                                            'mouse', 'Mouse')
      >>> folder.ftf.unrestrictedTraverse(
      ...     'mouse')() == 'The mouse has been eaten by the eagle'
      True

    Clean up:

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """


def test_suite():
    from Testing.ZopeTestCase import FunctionalDocTestSuite

    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(TestTraverse),
        FunctionalDocTestSuite(),
    ))
