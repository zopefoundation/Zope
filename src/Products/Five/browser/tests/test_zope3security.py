
def test_check_permission():
    """Code (in Zope packages) often uses
    zope.security.management.checkPermission to determine whether the
    current user has a certain permission in a given context. Five
    inserts its own interaction that assures that such calls still
    work.

      >>> configure_zcml = '''
      ... <configure 
      ...     xmlns="http://namespaces.zope.org/zope"
      ...     xmlns:browser="http://namespaces.zope.org/browser">
      ...   <securityPolicy
      ...       component="AccessControl.security.SecurityPolicy" />
      ...   <configure package="Products.Five.browser.tests">
      ...     <browser:page
      ...         for="OFS.interfaces.IFolder"
      ...         class=".zope3security.Zope3SecurityView"
      ...         name="zope3security.html"
      ...         permission="zope2.View"
      ...         />
      ...   </configure>
      ... </configure>'''

      >>> import Products.Five
      >>> from Zope2.App import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_string(configure_zcml)

    In order to be able to traverse to the PageTemplate view, we need
    a traversable object:

      >>> from Products.Five.tests.testing import manage_addFiveTraversableFolder
      >>> manage_addFiveTraversableFolder(self.folder, 'testoid', 'Testoid')

    Now we access a page that uses
    zope.security.management.checkPermission().  We see it works as
    expected:

      >>> from Testing.testbrowser import Browser
      >>> browser = Browser()
      >>> browser.open('http://localhost/test_folder_1_/testoid/@@zope3security.html?permission=zope2.View')
      >>> print browser.contents
      Yes, you have the 'zope2.View' permission.
      >>> browser.open('http://localhost/test_folder_1_/testoid/@@zope3security.html?permission=zope2.DeleteObjects')
      >>> print browser.contents
      No, you don't have the 'zope2.DeleteObjects' permission.

    Clean up:

      >>> from zope.component.testing import tearDown
      >>> tearDown()

    """

def test_allowed_interface():
    """This test demonstrates that allowed_interface security declarations work
    as expected.

      >>> from zope.component.testing import setUp, tearDown
      >>> setUp()

    Before we can make security declarations through ZCML, we need to
    register the directive and the permission:

      >>> import AccessControl
      >>> from zope.configuration.xmlconfig import XMLConfig
      >>> XMLConfig('meta.zcml', AccessControl)()
      >>> import Products.Five.browser
      >>> XMLConfig('meta.zcml', Products.Five.browser)()
      >>> XMLConfig('permissions.zcml', AccessControl)()

    Now we provide some ZCML declarations for ``Dummy1``:

      >>> from StringIO import StringIO
      >>> configure_zcml = StringIO('''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            xmlns:browser="http://namespaces.zope.org/browser">
      ...   <browser:page
      ...       for="*"
      ...       name="testview"
      ...       permission="zope2.ViewManagementScreens"
      ...       class="AccessControl.tests.testZCML.Dummy1"
      ...       allowed_interface="AccessControl.tests.testZCML.IDummy" />
      ... </configure>
      ... ''')
      >>> from zope.configuration.xmlconfig import xmlconfig
      >>> xmlconfig(configure_zcml)

    We are going to check that roles are correctly setup, so we need getRoles.

      >>> from AccessControl.ZopeSecurityPolicy import getRoles
      >>> from AccessControl import ACCESS_PRIVATE

    Due to the nasty voodoo involved in Five's handling of view classes,
    browser:page doesn't apply security to Dummy1, but rather to the "magic"
    view class that is created at ZCML parse time.  That means we can't just
    instanciate with Dummy1() directly and expect a security-aware instance :(.
    Instead, we'll have to actually lookup the view.  The view was declared for
    "*", so we just use an instance of Dummy1 ;-).

    Instanciate a Dummy1 object to test with.

      >>> from AccessControl.tests.testZCML import Dummy1
      >>> dummy1 = Dummy1()
      >>> from zope.component import getMultiAdapter
      >>> from zope.publisher.browser import TestRequest
      >>> request = TestRequest()
      >>> view = getMultiAdapter((dummy1, request), name="testview")

    As 'foo' is defined in IDummy, it should have the 'Manager' role.

      >>> getRoles(view, 'foo', view.foo, ('Def',))
      ('Manager',)

    As 'wot' is not defined in IDummy, it should be private.

      >>> getRoles(view, 'wot', view.wot, ('Def',)) is ACCESS_PRIVATE
      True

    But 'superMethod' is defined on IDummy by inheritance from ISuperDummy, and
    so should have the 'Manager' role setup.

      >>> getRoles(view, 'superMethod', view.superMethod, ('Def',))
      ('Manager',)

      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocTestSuite
    from doctest import ELLIPSIS
    return FunctionalDocTestSuite(optionflags=ELLIPSIS)
