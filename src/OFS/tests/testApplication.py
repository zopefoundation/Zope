import unittest

from AccessControl.tainted import TaintedString
from Testing.ZopeTestCase import FunctionalTestCase


class ApplicationTests(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.Application import Application
        return Application

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_provides_IApplication(self):
        from OFS.interfaces import IApplication
        from zope.interface.verify import verifyClass

        verifyClass(IApplication, self._getTargetClass())

    def test_instance_conforms_to_IApplication(self):
        from OFS.interfaces import IApplication
        from zope.interface.verify import verifyObject

        verifyObject(IApplication, self._makeOne())

    def test_instance_attributes(self):
        app = self._makeOne()
        self.assertTrue(app.isTopLevelPrincipiaApplicationObject)
        self.assertEqual(app.title, 'Zope')

    def test_id_no_request(self):
        app = self._makeOne()
        self.assertEqual(app.getId(), 'Zope')

    def test_id_w_request_no_SCRIPT_NAME(self):
        app = self._makeOne()
        app.REQUEST = {}
        self.assertEqual(app.getId(), 'Zope')

    def test_id_w_request_w_SCRIPT_NAME(self):
        app = self._makeOne()
        app.REQUEST = {'SCRIPT_NAME': '/Dummy'}
        self.assertEqual(app.getId(), 'Dummy')

    def test_title_and_id_plus_title_or_id(self):
        app = self._makeOne()
        app.title = 'Other'
        self.assertEqual(app.title_and_id(), 'Other')
        self.assertEqual(app.title_or_id(), 'Other')

    def test_bobo_traverse_attribute_hit(self):
        app = self._makeOne()
        app.NAME = 'attribute'
        app._getOb = lambda x, y: x
        request = {}
        self.assertEqual(app.__bobo_traverse__(request, 'NAME'), 'attribute')

    def test_bobo_traverse_attribute_miss_key_hit(self):
        app = self._makeOne()
        app._getOb = lambda x, y: x
        app._objects = [{'id': 'OTHER', 'meta_type': None}]
        request = {}
        self.assertEqual(app.__bobo_traverse__(request, 'OTHER'), 'OTHER')

    def test_bobo_traverse_attribute_key_miss_R_M_default_real_request(self):
        from collections import UserDict
        request = UserDict()

        class _Response:
            def notFoundError(self, msg):
                1 / 0

        request.RESPONSE = _Response()
        app = self._makeOne()
        app._getOb = _noWay

        self.assertRaises(ZeroDivisionError,
                          app.__bobo_traverse__, request, 'NONESUCH')

    def test_bobo_traverse_attribute_key_miss_R_M_default_fake_request(self):
        app = self._makeOne()

        app._getOb = _noWay
        request = {}
        self.assertRaises(KeyError, app.__bobo_traverse__, request, 'NONESUCH')

    def test_bobo_traverse_attribute_key_miss_R_M_is_GET(self):
        app = self._makeOne()

        app._getOb = _noWay
        request = {'REQUEST_METHOD': 'GET'}
        self.assertRaises(KeyError, app.__bobo_traverse__, request, 'NONESUCH')

    def test_redirect_regression(self):
        """From code you should still be able to call the Redirect method.

        And its aliases too.
        This is part of PloneHotfix20171128:
        Redirect should not be callable as url, but from code it is fine.
        """
        from zExceptions import Redirect as RedirectException
        app = self._makeOne()
        for name in ('Redirect', 'ZopeRedirect'):
            method = getattr(app, name, None)
            if method is None:
                continue
            self.assertRaises(
                RedirectException,
                method, 'http://google.nl', 'http://other.url')

    def test_ZopeVersion(self):
        from importlib.metadata import distribution

        from App.version_txt import getZopeVersion

        app = self._makeOne()
        pkg_version = distribution('Zope').version
        zversion = getZopeVersion()

        self.assertEqual(app.ZopeVersion(major=True), zversion.major)
        self.assertEqual(app.ZopeVersion(major=True),
                         int(pkg_version.split('.')[0]))

    def test_getZMIMainFrameTarget(self):
        app = self._makeOne()

        for URL1 in ('http://nohost', 'https://nohost/some/path'):
            request = {'URL1': URL1}

            # No came_from at all
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')

            # Empty came_from
            request['came_from'] = ''
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')
            request['came_from'] = None
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')

            # Local (path only) came_from
            request['came_from'] = '/new/path'
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             '/new/path')

            # Tainted local path.  came_from can be marked as 'tainted' if it
            # suspicious contents.  It is not accepted then.
            request['came_from'] = TaintedString('/new/path')
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')

            # came_from URL outside our own server
            request['came_from'] = 'https://www.zope.dev/index.html'
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')

            # came_from with wrong scheme
            request['came_from'] = URL1.replace('http', 'ftp')
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')

            # acceptable came_from
            request['came_from'] = f'{URL1}/added/path'
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/added/path')

            # Anything beginning with '<script>' should already be marked as
            # 'tainted'
            request['came_from'] = TaintedString(
                '<script>alert("hi");</script>'
            )
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')

            # double slashes as path should not be accepted.
            # Try a few forms.
            request['came_from'] = '//www.example.org'
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')
            request['came_from'] = '////www.example.org'
            self.assertEqual(app.getZMIMainFrameTarget(request),
                             f'{URL1}/manage_workspace')


class ApplicationPublishTests(FunctionalTestCase):

    def test_redirect_not_found(self):
        """Accessing Redirect as url should give a 404.

        This is part of PloneHotfix20171128.
        """
        # These are all aliases.
        for name in ('Redirect', 'ZopeRedirect'):
            response = self.publish(
                f'/{name}?destination=http://google.nl')
            # This should *not* return a 302 Redirect.
            self.assertEqual(response.status, 404)


def _noWay(self, key, default=None):
    raise KeyError(key)
