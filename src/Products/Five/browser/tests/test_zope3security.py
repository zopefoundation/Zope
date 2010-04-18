
def test_check_permission():
    """Code (in Zope 3) often uses
    zope.security.management.checkPermission to determine whether the
    current user has a certain permission in a given context.  Five
    inserts its own interaction that assures that such calls still
    work.
    
      >>> configure_zcml = '''
      ... <configure 
      ...     xmlns="http://namespaces.zope.org/zope"
      ...     xmlns:browser="http://namespaces.zope.org/browser">
      ...   <securityPolicy
      ...       component="Products.Five.security.FiveSecurityPolicy" />
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
      >>> from Products.Five import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_string(configure_zcml)

    In order to be able to traverse to the PageTemplate view, we need
    a traversable object:

      >>> from Products.Five.tests.testing import manage_addFiveTraversableFolder
      >>> manage_addFiveTraversableFolder(self.folder, 'testoid', 'Testoid')

    Now we access a page that uses
    zope.security.management.checkPermission().  We see it works as
    expected:

      >>> from Products.Five.testbrowser import Browser
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

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocTestSuite
    from doctest import ELLIPSIS
    return FunctionalDocTestSuite(optionflags=ELLIPSIS)
