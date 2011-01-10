import unittest

from AccessControl import Unauthorized


def addPythonScript(folder, id, params='', body=''):
    """Add a PythonScript to folder."""
    from Products.PythonScripts.PythonScript import manage_addPythonScript
    # clean up any 'ps' that's already here..
    if id in folder:
        del folder[id]
    manage_addPythonScript(folder, id)
    folder[id].ZPythonScript_edit(params, body)


def checkRestricted(folder, psbody):
    """Perform a check by running restricted Python code."""
    addPythonScript(folder, 'ps', body=psbody)
    try:
        folder.ps()
    except Unauthorized, e:
        raise AssertionError(e)


def checkUnauthorized(folder, psbody):
    """Perform a check by running restricted Python code.  Expect to
    encounter an Unauthorized exception."""
    addPythonScript(folder, 'ps', body=psbody)
    try:
        folder.ps()
    except Unauthorized:
        pass
    else:
        raise AssertionError("Authorized but shouldn't be")


def test_resource_restricted_code():
    """
    Set up the test fixtures:

      >>> import Products.Five.browser.tests
      >>> from Zope2.App import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_config('resource.zcml', package=Products.Five.browser.tests)

      >>> from Products.Five.tests.testing import manage_addFiveTraversableFolder
      >>> manage_addFiveTraversableFolder(self.folder, 'testoid', 'Testoid')

      >>> import os, glob
      >>> _prefix = os.path.dirname(Products.Five.browser.tests.__file__)
      >>> dir_resource_names = [os.path.basename(r) for r in (
      ...     glob.glob('%s/*.png' % _prefix) +
      ...     glob.glob('%s/*.pt' % _prefix) +
      ...     glob.glob('%s/[a-z]*.py' % _prefix) +
      ...     glob.glob('%s/*.css' % _prefix))]

      >>> from Products.Five.browser.tests.test_scriptsecurity import checkRestricted
      >>> from Products.Five.browser.tests.test_scriptsecurity import checkUnauthorized

      >>> resource_names = ['cockatiel.html', 'style.css', 'pattern.png']

    We should get Unauthorized as long as we're unauthenticated:

      >>> for resource in resource_names:
      ...     checkUnauthorized(
      ...         self.folder,
      ...         'context.restrictedTraverse("testoid/++resource++%s")()' % resource)

      >>> base = 'testoid/++resource++fivetest_resources/%s'
      >>> for resource in dir_resource_names:
      ...     path = base % resource
      ...     checkUnauthorized(self.folder, 'context.restrictedTraverse("%s")' % path)

    Now let's create a manager user account and log in:

      >>> uf = self.folder.acl_users
      >>> _ignored = uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')

    We can now view them all:

      >>> for resource in resource_names:
      ...     checkRestricted(
      ...         self.folder,
      ...         'context.restrictedTraverse("testoid/++resource++%s")()' % resource)

      >>> base = 'testoid/++resource++fivetest_resources/%s'
      >>> for resource in dir_resource_names:
      ...     path = base % resource
      ...     checkRestricted(self.folder, 'context.restrictedTraverse("%s")' % path)

    Let's make sure restrictedTraverse() works directly, too. It used to get
    tripped up on subdirectories due to missing security declarations.

      >>> self.folder.restrictedTraverse('++resource++fivetest_resources/resource.txt') is not None
      True
  
      >>> self.folder.restrictedTraverse('++resource++fivetest_resources/resource_subdir/resource.txt') is not None
      True

    Clean up

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """

def test_view_restricted_code():
    """
    Let's register a quite large amount of test pages:

      >>> import Products.Five.browser.tests
      >>> from Zope2.App import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_config('pages.zcml', package=Products.Five.browser.tests)

    Let's add a test object that we view most of the pages off of:

      >>> from Products.Five.tests.testing.simplecontent import manage_addSimpleContent
      >>> manage_addSimpleContent(self.folder, 'testoid', 'Testoid')

    We also need to create a stub user account and login; otherwise we
    wouldn't have all the rights to do traversal etc.:

      >>> uf = self.folder.acl_users
      >>> _ignored = uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')

      >>> protected_view_names = [
      ...     'eagle.txt', 'falcon.html', 'owl.html', 'flamingo.html',
      ...     'condor.html', 'permission_view']
      >>> 
      >>> public_view_names = [
      ...     'public_attribute_page',
      ...     'public_template_page',
      ...     'public_template_class_page',
      ...     'nodoc-method', 'nodoc-function', 'nodoc-object',
      ...     'dirpage1', 'dirpage2']

      >>> from Products.Five.browser.tests.test_scriptsecurity import checkRestricted
      >>> from Products.Five.browser.tests.test_scriptsecurity import checkUnauthorized

    As long as we're not authenticated, we should get Unauthorized for
    protected views, but we should be able to view the public ones:

      >>> self.logout()
      >>> for view_name in protected_view_names:
      ...     checkUnauthorized(
      ...         self.folder,
      ...         'context.restrictedTraverse("testoid/%s")()' % view_name)

      >>> for view_name in public_view_names:
      ...     checkRestricted(
      ...         self.folder,
      ...         'context.restrictedTraverse("testoid/%s")()' % view_name)
      >>> self.login('manager')

    Being logged in as a manager again, we find that the protected pages
    are accessible to us:

      >>> for view_name in protected_view_names:
      ...     checkRestricted(
      ...         self.folder,
      ...         'context.restrictedTraverse("testoid/%s")()' % view_name)

      >>> checkRestricted(
      ...     self.folder,
      ...     'context.restrictedTraverse("testoid/eagle.method").eagle()')

    Even when logged in though the private methods should not be accessible:

      >>> checkUnauthorized( self.folder,
      ...             'context.restrictedTraverse("testoid/eagle.method").mouse()')

    Cleanup:

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """


def test_suite():
    suite = unittest.TestSuite()
    try:
        import Products.PythonScripts
    except ImportError:
        pass
    else:
        from Testing.ZopeTestCase import ZopeDocTestSuite
        from Testing.ZopeTestCase import installProduct
        installProduct('PythonScripts')
        suite.addTest(ZopeDocTestSuite())
    return suite
