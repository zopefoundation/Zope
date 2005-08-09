##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Five tests.

$Id: test_five.py 12915 2005-05-31 10:23:19Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.Five.tests.fivetest import *

import re
import glob
import unittest
import zope

from zope.interface import directlyProvides, Interface, implements
from zope.component import getViewProviding
from zope.schema import Choice, TextLine
from zope.app.form.interfaces import IInputWidget
from zope.app.traversing.browser.interfaces import IAbsoluteURL
from zope.app.traversing.interfaces import IContainmentRoot

from Products.Five.tests.products.FiveTest.classes import Adaptable, Origin
from Products.Five.tests.products.FiveTest.interfaces import IAdapted, IDestination
from Products.Five.tests.products.FiveTest.browser import SimpleContentView
from Products.Five.resource import Resource, PageTemplateResource
from Products.Five.traversable import FakeRequest
from Products.Five.fiveconfigure import classDefaultViewable
from OFS.Traversable import Traversable

from Products.Five.tests.products.FiveTest.simplecontent import manage_addSimpleContent
from Products.Five.tests.products.FiveTest.simplecontent import manage_addCallableSimpleContent
from Products.Five.tests.products.FiveTest.simplecontent import manage_addIndexSimpleContent
from Products.Five.tests.products.FiveTest.fancycontent import manage_addFancyContent

from Products.Five.tests.products import FiveTest
_prefix = os.path.dirname(FiveTest.__file__)
dir_resource_names = [os.path.basename(r)
                      for r in (glob.glob('%s/*.png' % _prefix) +
                                glob.glob('%s/*.pt' % _prefix) +
                                glob.glob('%s/[a-z]*.py' % _prefix) +
                                glob.glob('%s/*.css' % _prefix))]

def normalize_html(s):
    s = re.sub(r"[ \t\n]+", "", s)
    return s


class FiveTest(FiveTestCase):

    def afterSetUp(self):
        manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
        manage_addCallableSimpleContent(self.folder, 'testcall', 'TestCall')
        manage_addIndexSimpleContent(self.folder, 'testindex', 'TestIndex')
        uf = self.folder.acl_users
        uf._doAddUser('manager', 'r00t', ['Manager'], [])
        self.login('manager')

    def test_adapters(self):
        obj = Adaptable()
        adapted = IAdapted(obj)
        self.assertEquals(
            "Adapted: The method",
            adapted.adaptedMethod())

    def test_adapters2(self):
        obj = Adaptable()
        adapted = IAdapted(obj)
        self.assertEquals(
            "Adapted: The method",
            adapted.adaptedMethod())

    def test_overrides(self):
        origin = Origin()
        dest = IDestination(origin)
        self.assertEquals(dest.method(), "Overridden")

        view = self.folder.unrestrictedTraverse('testoid/overridden_view')
        self.assertEquals(view(), "The mouse has been eaten by the eagle")

    def test_attribute_view(self):
        view = self.folder.unrestrictedTraverse('testoid/eagle.txt')
        self.assert_(isinstance(view, SimpleContentView))
        self.assertEquals('The eagle has landed', view())

    def test_existing_docstrings_arent_modified(self):
        view = self.folder.unrestrictedTraverse('testoid/eagle.txt')
        self.assertEquals(view.eagle.__doc__, SimpleContentView.eagle.__doc__)

    def test_pages_view(self):
        view = self.folder.unrestrictedTraverse('testoid/eagle-page.txt')
        self.assert_(isinstance(view, SimpleContentView))
        self.assertEquals('The eagle has landed', view())

        view = self.folder.unrestrictedTraverse('testoid/mouse-page.txt')
        self.assert_(isinstance(view, SimpleContentView))
        self.assertEquals('The mouse has been eaten by the eagle', view())

    def test_template_view(self):
        view = self.folder.unrestrictedTraverse('testoid/falcon.html')
        self.assert_(isinstance(view, SimpleContentView))
        self.assertEquals(u'<p>The falcon has taken flight</p>\n', view())

    def test_template_view_without_class(self):
        view = self.folder.unrestrictedTraverse('testoid/owl.html')
        self.assertEquals(u'<p>2</p>\n', view())

    def test_template_view_context(self):
        view = self.folder.unrestrictedTraverse('testoid/flamingo.html')
        self.assertEquals(u'<p>Hello world</p>\n', view())

    def test_template_view_context_path(self):
        view = self.folder.unrestrictedTraverse('testoid/flamingo2.html')
        self.assertEquals(u'<p>Hello world</p>\n', view())

    def test_template_view_resource_traversal(self):
        view = self.folder.unrestrictedTraverse('testoid/parakeet.html')
        expected = """\
        <html>
        <head>
        <title>bird macro</title>
        </head>
        <body>
        Color: green
        <img alt="" src="http://nohost/test_folder_1_/testoid/++resource++pattern.png" />
        </body>
        </html>
        """
        expected = normalize_html(expected)
        self.assertEquals(expected, normalize_html(view()))

    def test_view_backwards_compatibility(self):
        old_view = self.folder.unrestrictedTraverse('testoid/direct')
        self.assertEquals('Direct traversal worked', old_view())

    def test_zpt_things(self):
        view = self.folder.unrestrictedTraverse('testoid/condor.html')
        expected = """\
<p>Hello world</p>
<p>The eagle has landed</p>
<p>Hello world</p>
"""
        self.assertEquals(expected, view())

    def test_repeat(self):
        view = self.folder.unrestrictedTraverse('testoid/ostrich.html')
        expected = """\
<ul>
<li>Alpha</li>
<li>Beta</li>
<li>Gamma</li>
</ul>
"""
        self.assertEquals(expected, view())

    def test_macro_access(self):
        view = self.folder.unrestrictedTraverse('testoid/seagull.html')
        self.assertEquals('<html><head><title>bird macro</title></head><body>Color: gray</body></html>\n', view())

    def test_repeat_iterator(self):
        view = self.folder.unrestrictedTraverse('testoid/ostrich2.html')
        expected = """\
<ul>
<li>0</li>
<li>1</li>
<li>2</li>
</ul>
"""
        self.assertEquals(expected, view())

    def test_tales_traversal(self):
        view = self.folder.unrestrictedTraverse('testoid/tales_traversal.html')
        expected = """\
<p>testoid</p>
<p>test_folder_1_</p>
"""
        self.assertEquals(expected, view())

    def test_zpt_security(self):
        self.logout()
        view = self.folder.unrestrictedTraverse('testoid/security.html')
        expected = """\
<div>NoneType</div>
<div>smtpd</div>
"""
        self.assertEquals(expected, view())

    def test_template_resource(self):
        resource = self.folder.unrestrictedTraverse('testoid/++resource++cockatiel.html')
        self.assert_(isinstance(resource, Resource))
        expected = 'http://nohost/test_folder_1_/testoid/++resource++cockatiel.html'
        self.assertEquals(expected, resource())

    def test_file_resource(self):
        resource = self.folder.unrestrictedTraverse('testoid/++resource++style.css')
        self.assert_(isinstance(resource, Resource))
        expected = 'http://nohost/test_folder_1_/testoid/++resource++style.css'
        self.assertEquals(expected, resource())

    def test_image_resource(self):
        resource = self.folder.unrestrictedTraverse('testoid/++resource++pattern.png')
        expected = 'http://nohost/test_folder_1_/testoid/++resource++pattern.png'
        self.assert_(isinstance(resource, Resource))
        self.assertEquals(expected, resource())

    def test_resource_directory(self):
        base = 'testoid/++resource++fivetest_resources/%s'
        base_url = 'http://nohost/test_folder_1_/' + base

        abs_url = self.folder.unrestrictedTraverse(base % '')()
        self.assertEquals(abs_url + '/', base_url % '')

        for r in dir_resource_names:
            resource = self.folder.unrestrictedTraverse(base % r)
            self.assert_(isinstance(resource, Resource))
            # PageTemplateResource's __call__ renders the template
            if not isinstance(resource, PageTemplateResource):
                self.assertEquals(resource(), base_url % r)

    def test_breadcrumbs(self):
        view = self.folder.unrestrictedTraverse('testoid/@@absolute_url')
        expected = (
            {'url': 'http://nohost', 'name': ''},
            {'url': 'http://nohost/test_folder_1_', 'name': 'test_folder_1_'},
            {'url': 'http://nohost/test_folder_1_/testoid', 'name': 'testoid'})
        self.assertEquals(expected, view.breadcrumbs())

    def test_virtualhost_breadcrumbs(self):
        # Get REQUEST in shape
        request = self.request = self.app.REQUEST
        request['PARENTS'] = [self.folder.test_folder_1_]
        request.setServerURL(
            protocol='http', hostname='foo.bar.com', port='80')
        request.setVirtualRoot('')

        view = self.folder.unrestrictedTraverse('testoid/@@absolute_url')
        expected = (
            {'url': 'http://foo.bar.com', 'name': 'test_folder_1_'},
            {'url': 'http://foo.bar.com/testoid', 'name': 'testoid'})
        self.assertEquals(expected, view.breadcrumbs())

    def test_containement_root_breadcrumbs(self):
        # Should stop breadcrumbs from crumbing
        directlyProvides(self.folder, IContainmentRoot)
        view = self.folder.unrestrictedTraverse('testoid/@@absolute_url')
        expected = (
            {'url': 'http://nohost/test_folder_1_', 'name': 'test_folder_1_'},
            {'url': 'http://nohost/test_folder_1_/testoid', 'name': 'testoid'})
        self.assertEquals(expected, view.breadcrumbs())

    def test_standard_macros(self):
        view = self.folder.unrestrictedTraverse('testoid/@@fivetest_macros')
        self.assertRaises(KeyError, view.__getitem__, 'non-existing-macro')
        self.failUnless(view['birdmacro'])
        self.failUnless(view['dogmacro'])
        # Test aliases
        self.failUnless(view['flying'])
        self.failUnless(view['walking'])
        self.assertEquals(view['flying'], view['birdmacro'])
        self.assertEquals(view['walking'], view['dogmacro'])
        # Test traversal
        base = 'testoid/@@fivetest_macros/%s'
        for macro in ('birdmacro', 'dogmacro',
                      'flying', 'walking'):
            view = self.folder.unrestrictedTraverse(base % macro)
        self.failUnless(view)

    def test_unrestrictedTraverse_non_existing(self):
        self.assertRaises(AttributeError, self.folder.unrestrictedTraverse,
                          'testoid/@@invalid_page')

    def test_get_widgets_for_schema_fields(self):
        salutation = Choice(title=u'Salutation', values=("Mr.", "Mrs.", "Captain", "Don"))
        contactname = TextLine(title=u'Name')
        request = FakeRequest()
        salutation = salutation.bind(request)
        contactname = contactname.bind(request)
        view1 = getViewProviding(contactname, IInputWidget, request)
        self.assertEquals(view1.__class__, zope.app.form.browser.textwidgets.TextWidget)
        view2 = getViewProviding(salutation, IInputWidget, request)
        self.assertEquals(view2.__class__, zope.app.form.browser.itemswidgets.DropdownWidget)

    # Disabled __call__ overriding for now. Causes more trouble
    # than it fixes.
    # def test_existing_call(self):
    #     view = self.folder.unrestrictedTraverse('testcall')
    #     self.assertEquals("Default __call__ called", view())


class PublishTest(Functional, FiveTestCase):
    """Test a few publishing features"""

    def afterSetUp(self):
        manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
        manage_addCallableSimpleContent(self.folder, 'testcall', 'TestCall')
        manage_addIndexSimpleContent(self.folder, 'testindex', 'TestIndex')
        uf = self.folder.acl_users
        uf._doAddUser('viewer', 'secret', [], [])
        uf._doAddUser('manager', 'r00t', ['Manager'], [])

    def test_no_doc_string(self):
        for view_name in ['nodoc-function', 'nodoc-method', 'nodoc-object']:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name)
            self.assertEquals("No docstring", response.getBody())

    def test_fallback_raises_notfound(self):
        # If we return None in __fallback_traverse__, this test passes
        # but for the wrong reason: None doesn't have a docstring so
        # BaseRequest raises NotFoundError. A functional test would be
        # perfect here.
        response = self.publish('/test_folder_1_/testoid/doesntexist')
        self.assertEquals(404, response.getStatus())

    def test_existing_bobo_traverse(self):
        manage_addFancyContent(self.folder, 'fancy', '')

        # check if the old bobo_traverse method can still kick in
        response = self.publish('/test_folder_1_/fancy/something-else')
        self.assertEquals('something-else', response.getBody())

        # check if z3-based view lookup works
        response = self.publish('/test_folder_1_/fancy/fancy')
        self.assertEquals("Fancy, fancy", response.getBody())

    def test_publish_image_resource(self):
        url = '/test_folder_1_/testoid/++resource++pattern.png'
        response = self.publish(url, basic='manager:r00t')
        self.assertEquals(200, response.getStatus())

    def test_publish_file_resource(self):
        url = '/test_folder_1_/testoid/++resource++style.css'
        response = self.publish(url, basic='manager:r00t')
        self.assertEquals(200, response.getStatus())

    def test_publish_template_resource(self):
        url = '/test_folder_1_/testoid/++resource++cockatiel.html'
        response = self.publish(url, basic='manager:r00t')
        self.assertEquals(200, response.getStatus())
    # Disabled __call__ overriding for now. Causes more trouble
    # than it fixes.
    # def test_existing_call(self):
    #     response = self.publish('/test_folder_1_/testcall')
    #     self.assertEquals("Default __call__ called", response.getBody())

    def test_publish_resource_directory(self):
        base_url = '/test_folder_1_/testoid/++resource++fivetest_resources/%s'
        for r in dir_resource_names:
            if r.endswith('.pt'):
                # page templates aren't guaranteed to render
                continue
            response = self.publish(base_url % r, basic='manager:r00t')
            self.assertEquals(200, response.getStatus())

    def test_existing_index(self):
        response = self.publish('/test_folder_1_/testindex')
        self.assertEquals("Default index_html called", response.getBody())

    def test_default_view(self):
        response = self.publish('/test_folder_1_/testoid', basic='manager:r00t')
        self.assertEquals("The eagle has landed", response.getBody())

    def test_pages_from_directory(self):
        response = self.publish('/test_folder_1_/testoid/dirpage1')
        self.assert_('page 1' in response.getBody())
        response = self.publish('/test_folder_1_/testoid/dirpage2')
        self.assert_('page 2' in response.getBody())

class IRecurse(Interface):
    pass

class Recurse(Traversable):

    implements(IRecurse)

    def view(self):
        return self()

    def __call__(self):
        return 'foo'

classDefaultViewable(Recurse)

class RecursionTest(unittest.TestCase):

    def setUp(self):
        self.ob = Recurse()

    def test_recursive_call(self):
        from zope.app import zapi
        from zope.publisher.interfaces.browser import IBrowserRequest
        pres = zapi.getGlobalService('Presentation')
        type = IBrowserRequest
        pres.setDefaultViewName(IRecurse, type, 'view')
        self.assertEquals(self.ob.view(), 'foo')
        self.assertEquals(self.ob(), 'foo')


from zope.app.publisher.browser.globalbrowsermenuservice import \
     globalBrowserMenuService

class MenuTest(FiveTestCase):

    def afterSetUp(self):
        manage_addIndexSimpleContent(self.folder, 'test', 'Test')

    def test_menu(self):
        request = FakeRequest()
        # XXX not sure why we need this..
        request.getURL = lambda: 'http://www.infrae.com'
        menu = globalBrowserMenuService.getMenu('testmenu',
                                                self.folder.test,
                                                request)
        self.assertEquals(3, len(menu))
        # sort menu items by title so we get a stable testable result
        menu.sort(lambda x, y: cmp(x['title'], y['title']))
        self.assertEquals('Test Menu Item', menu[0]['title'])
        self.assertEquals('seagull.html', menu[0]['action'])
        self.assertEquals('Test Menu Item 2', menu[1]['title'])
        self.assertEquals('parakeet.html', menu[1]['action'])

class SizeTest(FiveTestCase):

    def test_no_get_size_on_original(self):
        manage_addSimpleContent(self.folder, 'simple', 'Simple')
	obj = self.folder.simple
	self.assertEquals(obj.get_size(), 42)

    def test_get_size_on_original_and_fallback(self):
	manage_addFancyContent(self.folder, 'fancy', 'Fancy')
	obj = self.folder.fancy
	self.assertEquals(obj.get_size(), 43)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(RecursionTest))
    suite.addTest(makeSuite(FiveTest))
    suite.addTest(makeSuite(PublishTest))
    suite.addTest(makeSuite(MenuTest))
    suite.addTest(makeSuite(SizeTest))
    return suite

if __name__ == '__main__':
    framework()
