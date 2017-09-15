"""This module contains integration tests for AccessControl.safe_formatter."""

from Testing.ZopeTestCase import FunctionalTestCase
from zExceptions import Unauthorized

import unittest


BAD_STR = """<p tal:content="python:'{0}: {0.__class__}'.format(context)" />"""
BAD_UNICODE = """\
<p tal:content="python:u'{0}: {0.__class__}'.format(context)" />"""
GOOD_STR = """<p tal:content="python:('%s' % context).lower()" />"""
GOOD_UNICODE = u"""<p tal:content="python:('%s' % context).lower()" />"""


def noop(context=None):
    return lambda: context


def hack_pt(pt, context=None):
    # hacks to avoid getting error in pt_render.
    pt.getPhysicalRoot = noop()
    pt._getContext = noop(context)
    pt._getContainer = noop(context)
    pt.context = context


class FormatterTest(unittest.TestCase):

    def test_cook_zope2_page_templates_bad_str(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', BAD_STR)
        hack_pt(pt)
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access '__class__' in this context",
            str(err.exception))

    def test_cook_zope2_page_templates_bad_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', BAD_UNICODE)
        hack_pt(pt)
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access '__class__' in this context",
            str(err.exception))

    def test_cook_zope2_page_templates_good_str(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', GOOD_STR)
        hack_pt(pt)
        self.assertEqual(pt.pt_render().strip(), '<p>none</p>')

    def test_cook_zope2_page_templates_good_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', GOOD_UNICODE)
        hack_pt(pt)
        self.assertEqual(pt.pt_render().strip(), '<p>none</p>')


class UnauthorizedSecurityPolicy:
    """Policy which denies every access."""

    def validate(self, *args, **kw):
        from AccessControl.unauthorized import Unauthorized
        raise Unauthorized('Nothing is allowed!')


class FormatterFunctionalTest(FunctionalTestCase):

    def test_access_to_private_content_not_allowed_via_any_attribute(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        # If access to _delObject would be allowed, it would still only say
        # something like 'bound method _delObject', without actually deleting
        # anything, because methods are not executed in str.format, but there
        # may be @properties that give an attacker secret info.
        pt = ZopePageTemplate(
            'mytemplate',
            """<p tal:content="python:'{0._delObject}'.format(context)" />""")
        hack_pt(pt, context=self.app)
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access '_delObject' in this context",
            str(err.exception))

    def assert_is_checked_via_security_manager(self, pt_content):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        from AccessControl.SecurityManager import setSecurityPolicy
        from AccessControl.SecurityManagement import noSecurityManager
        from AccessControl.SecurityManagement import getSecurityManager

        pt = ZopePageTemplate('mytemplate', pt_content)
        noSecurityManager()
        old_security_policy = setSecurityPolicy(UnauthorizedSecurityPolicy())
        getSecurityManager()
        try:
            hack_pt(pt, context=self.app)
            with self.assertRaises(Unauthorized) as err:
                pt.pt_render()
            self.assertEqual("Nothing is allowed!", str(err.exception))
        finally:
            setSecurityPolicy(old_security_policy)

    def test_getattr_access_is_checked_via_security_manager(self):
        self.assert_is_checked_via_security_manager(
            """<p tal:content="python:'{0.acl_users}'.format(context)" />""")

    def test_getitem_access_is_checked_via_security_manager(self):
        self.assert_is_checked_via_security_manager(
            """<p tal:content="python:'{c[acl_users]}'.format(c=context)" />"""
        )

    # Zope 3 templates are always file system templates.  So we actually have
    # no problems allowing str.format there.

    def test_cook_zope3_page_templates_normal(self):
        from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
        pt = ViewPageTemplateFile('normal_zope3_page_template.pt')
        hack_pt(pt)
        # Need to pass a namespace.
        namespace = {'context': self.app}
        self.assertEqual(
            pt.pt_render(namespace).strip(),
            u'<p>&lt;application at &gt;</p>\n'
            u'<p>&lt;APPLICATION AT &gt;</p>')

    def test_cook_zope3_page_templates_using_format(self):
        from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
        pt = ViewPageTemplateFile('using_format_zope3_page_template.pt')
        hack_pt(pt)
        # Need to pass a namespace.
        namespace = {'context': self.app}
        self.assertEqual(
            pt.pt_render(namespace).strip(),
            u"<p>class of &lt;application at &gt; is "
            u"&lt;class 'ofs.application.application'&gt;</p>\n"
            u"<p>CLASS OF &lt;APPLICATION AT &gt; IS "
            u"&lt;CLASS 'OFS.APPLICATION.APPLICATION'&gt;</p>")
