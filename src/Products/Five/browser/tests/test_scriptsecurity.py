from AccessControl import Unauthorized


def addDTMLMethod(folder, id, body=''):
    from OFS.DTMLMethod import addDTMLMethod
    if id in folder:
        del folder[id]
    addDTMLMethod(folder, id, file=body)


def checkRestricted(folder, path, method=''):
    """Perform a check by running restricted Python code."""
    traverse = "_.this.restrictedTraverse('%s')" % path
    if not method:
        body = '<dtml-call "%s()">' % traverse
    else:
        body = f'<dtml-call "{traverse}.{method}()">'

    addDTMLMethod(folder, 'ps', body=body)
    try:
        folder.ps(client=folder)
    except Unauthorized as e:
        raise AssertionError(e)


def checkUnauthorized(folder, path, method=''):
    """Perform a check by running restricted Python code.  Expect to
    encounter an Unauthorized exception."""
    traverse = "_.this.restrictedTraverse('%s')" % path
    if not method:
        body = '<dtml-call "%s()">' % traverse
    else:
        body = f'<dtml-call "{traverse}.{method}()">'
    addDTMLMethod(folder, 'ps', body=body)
    try:
        folder.ps(client=folder)
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
      >>> zcml.load_config('resource.zcml',
      ...                  package=Products.Five.browser.tests)
      >>> folder = self.folder  # NOQA: F821

      >>> from Products.Five.tests.testing import (
      ... manage_addFiveTraversableFolder)
      >>> manage_addFiveTraversableFolder(folder, 'testoid', 'Testoid')

      >>> import os, glob
      >>> _prefix = os.path.dirname(Products.Five.browser.tests.__file__)
      >>> dir_resource_names = [os.path.basename(r) for r in (
      ...     glob.glob('%s/*.png' % _prefix) +
      ...     glob.glob('%s/*.pt' % _prefix) +
      ...     glob.glob('%s/[a-z]*.py' % _prefix) +
      ...     glob.glob('%s/*.css' % _prefix))]

      >>> from Products.Five.browser.tests.test_scriptsecurity import (
      ... checkRestricted,
      ... checkUnauthorized,
      ... )

      >>> resource_names = ['cockatiel.html', 'style.css', 'pattern.png']

    We should get Unauthorized as long as we're unauthenticated:

      >>> for resource in resource_names:
      ...     checkUnauthorized(folder, 'testoid/++resource++%s' % resource)

      >>> base = 'testoid/++resource++fivetest_resources/%s'
      >>> for resource in dir_resource_names:
      ...     checkUnauthorized(folder, base % resource)

    Now let's create a manager user account and log in:

      >>> uf = folder.acl_users
      >>> _ignored = uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')  # NOQA: F821

    We can now view them all:

      >>> for resource in resource_names:
      ...     checkRestricted(folder, 'testoid/++resource++%s' % resource)

      >>> base = 'testoid/++resource++fivetest_resources/%s'
      >>> for resource in dir_resource_names:
      ...     checkRestricted(folder, base % resource)

    Let's make sure restrictedTraverse() works directly, too. It used to get
    tripped up on subdirectories due to missing security declarations.

      >>> folder.restrictedTraverse(
      ...     '++resource++fivetest_resources/resource.txt') is not None
      True

      >>> folder.restrictedTraverse(
      ...     '++resource++fivetest_resources/resource_subdir/resource.txt'
      ... ) is not None
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
      >>> folder = self.folder  # NOQA: F821

    Let's add a test object that we view most of the pages off of:

      >>> from Products.Five.tests.testing.simplecontent import (
      ... manage_addSimpleContent)
      >>> manage_addSimpleContent(folder, 'testoid', 'Testoid')

    We also need to create a stub user account and login; otherwise we
    wouldn't have all the rights to do traversal etc.:

      >>> uf = folder.acl_users
      >>> _ignored = uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')  # NOQA: F821

      >>> protected_view_names = [
      ...     'eagle.txt', 'falcon.html', 'owl.html', 'flamingo.html',
      ...     'condor.html', 'permission_view']

      >>> public_view_names = [
      ...     'public_attribute_page',
      ...     'public_template_page',
      ...     'public_template_class_page',
      ...     'nodoc-method', 'nodoc-function', 'nodoc-object',
      ...     'dirpage1', 'dirpage2']

      >>> from Products.Five.browser.tests.test_scriptsecurity import (
      ... checkRestricted,
      ... checkUnauthorized,
      ... )

    As long as we're not authenticated, we should get Unauthorized for
    protected views, but we should be able to view the public ones:

      >>> self.logout()  # NOQA: F821
      >>> for view_name in protected_view_names:
      ...     checkUnauthorized(folder, 'testoid/%s' % view_name)

      >>> for view_name in public_view_names:
      ...     checkRestricted(folder, 'testoid/%s' % view_name)

    Being logged in as a manager again, we find that the protected pages
    are accessible to us:

      >>> self.login('manager')  # NOQA: F821
      >>> for view_name in protected_view_names:
      ...     checkRestricted(folder, 'testoid/%s' % view_name)

      >>> checkRestricted(folder, 'testoid/eagle.method', method='eagle')

    Even when logged in though the private methods should not be accessible:

      >>> checkUnauthorized(folder, 'testoid/eagle.method', method='mouse')

    Cleanup:

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """


def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()
