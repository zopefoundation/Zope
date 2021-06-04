"""This module contains integration tests for AccessControl.safe_formatter."""

from Testing.ZopeTestCase import FunctionalTestCase
from zExceptions import Unauthorized


BAD_ATTR_STR = """
<p tal:content="python:'class of {0} is {0.__class__}'.format(context)" />
"""
BAD_ATTR_UNICODE = """
<p tal:content="python:u'class of {0} is {0.__class__}'.format(context)" />
"""
BAD_KEY_STR = """
<p tal:content="python:'access by key: {0[test_folder_1_]}'.format(context)" />
"""
BAD_KEY_UNICODE = """
<p tal:content="python:u'access by key:
{0[test_folder_1_]}'.format(context)" />
"""
BAD_ITEM_STR = """
<p tal:content="python:'access by item: {0[0]}'.format(context)" />
"""
BAD_ITEM_UNICODE = """
<p tal:content="python:u'access by item: {0[0]}'.format(context)" />
"""
GOOD_STR = '<p tal:content="python:(\'%s\' % context).lower()" />'
GOOD_UNICODE = '<p tal:content="python:(\'%s\' % context).lower()" />'
# Attribute access is not completely forbidden, it is simply checked.
GOOD_FORMAT_ATTR_STR = """
<p tal:content="python:'title of {0} is {0.title}'.format(context)" />
"""
GOOD_FORMAT_ATTR_UNICODE = """
<p tal:content="python:u'title of {0} is {0.title}'.format(context)" />
"""


def noop(context=None):
    return lambda: context


def hack_pt(pt, context=None):
    # hacks to avoid getting error in pt_render.
    pt.getPhysicalRoot = noop()
    pt._getContext = noop(context)
    pt._getContainer = noop(context)
    pt.context = context


class UnauthorizedSecurityPolicy:
    """Policy which denies every access."""

    def validate(self, *args, **kw):
        from AccessControl.unauthorized import Unauthorized
        raise Unauthorized('Nothing is allowed!')


class FormatterFunctionalTest(FunctionalTestCase):

    maxDiff = None

    def test_cook_zope2_page_templates_bad_attr_str(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', BAD_ATTR_STR)
        hack_pt(pt)
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access '__class__' in this context",
            str(err.exception))
        hack_pt(pt, context=self.app)
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access '__class__' in this context",
            str(err.exception))

    def test_cook_zope2_page_templates_bad_attr_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', BAD_ATTR_UNICODE)
        hack_pt(pt)
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access '__class__' in this context",
            str(err.exception))
        hack_pt(pt, context=self.app)
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
        hack_pt(pt, context=self.app)
        self.assertEqual(
            pt.pt_render().strip(), '<p>&lt;application at &gt;</p>')

    def test_cook_zope2_page_templates_good_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', GOOD_UNICODE)
        hack_pt(pt)
        self.assertEqual(pt.pt_render().strip(), '<p>none</p>')
        hack_pt(pt, self.app)
        self.assertEqual(
            pt.pt_render().strip(), '<p>&lt;application at &gt;</p>')

    def test_cook_zope2_page_templates_good_format_attr_str(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', GOOD_FORMAT_ATTR_STR)
        hack_pt(pt, self.app)
        self.assertEqual(
            pt.pt_render().strip(),
            '<p>title of &lt;Application at &gt; is Zope</p>')

    def test_cook_zope2_page_templates_good_format_attr_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', GOOD_FORMAT_ATTR_UNICODE)
        hack_pt(pt, self.app)
        self.assertEqual(
            pt.pt_render().strip(),
            '<p>title of &lt;Application at &gt; is Zope</p>')

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
        from AccessControl.SecurityManagement import getSecurityManager
        from AccessControl.SecurityManagement import noSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

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
            pt.pt_render(namespace).strip().replace('\r\n', '\n'),
            '<p>&lt;application at &gt;</p>\n'
            '<p>&lt;APPLICATION AT &gt;</p>')

    def test_cook_zope3_page_templates_using_format(self):
        from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
        pt = ViewPageTemplateFile('using_format_zope3_page_template.pt')
        hack_pt(pt)
        # Need to pass a namespace.
        namespace = {'context': self.app}
        # Even when one of the accessed items requires a role that we do
        # not have, we get no Unauthorized, because this is a filesystem
        # template.
        self.app.test_folder_1_.__roles__ = ['Manager']
        self.assertEqual(
            pt.pt_render(namespace).strip().replace('\r\n', '\n'),
            "<p>class of &lt;application at &gt; is "
            "&lt;class 'ofs.application.application'&gt;</p>\n"
            "<p>CLASS OF &lt;APPLICATION AT &gt; IS "
            "&lt;CLASS 'OFS.APPLICATION.APPLICATION'&gt;</p>\n"
            "<p>{'foo': &lt;Folder at /test_folder_1_&gt;} has "
            "foo=&lt;Folder at test_folder_1_&gt;</p>\n"
            "<p>{'foo': &lt;Folder at /test_folder_1_&gt;} has "
            "foo=&lt;Folder at test_folder_1_&gt;</p>\n"
            "<p>[&lt;Folder at /test_folder_1_&gt;] has "
            "first item &lt;Folder at test_folder_1_&gt;</p>\n"
            "<p>[&lt;Folder at /test_folder_1_&gt;] has "
            "first item &lt;Folder at test_folder_1_&gt;</p>"
        )

    def test_cook_zope2_page_templates_bad_key_str(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', BAD_KEY_STR)
        hack_pt(pt, self.app)
        self.assertEqual(
            pt.pt_render(),
            '<p>access by key: &lt;Folder at test_folder_1_&gt;</p>')
        self.app.test_folder_1_.__roles__ = ['Manager']
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access 'test_folder_1_' in this context",
            str(err.exception))

    def test_cook_zope2_page_templates_bad_key_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', BAD_KEY_UNICODE)
        hack_pt(pt, self.app)
        self.assertEqual(
            pt.pt_render(),
            '<p>access by key: &lt;Folder at test_folder_1_&gt;</p>')
        self.app.test_folder_1_.__roles__ = ['Manager']
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access 'test_folder_1_' in this context",
            str(err.exception))

    def test_cook_zope2_page_templates_bad_item_str(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        self.app.testlist = [self.app.test_folder_1_]
        pt = ZopePageTemplate('mytemplate', BAD_ITEM_STR)
        hack_pt(pt, self.app.testlist)
        self.assertEqual(
            pt.pt_render(),
            '<p>access by item: &lt;Folder at test_folder_1_&gt;</p>')
        self.app.test_folder_1_.__roles__ = ['Manager']
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access 'test_folder_1_' in this context",
            str(err.exception))

    def test_cook_zope2_page_templates_bad_item_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        self.app.testlist = [self.app.test_folder_1_]
        pt = ZopePageTemplate('mytemplate', BAD_ITEM_UNICODE)
        hack_pt(pt, self.app.testlist)
        self.assertEqual(
            pt.pt_render(),
            '<p>access by item: &lt;Folder at test_folder_1_&gt;</p>')
        self.app.test_folder_1_.__roles__ = ['Manager']
        with self.assertRaises(Unauthorized) as err:
            pt.pt_render()
        self.assertEqual(
            "You are not allowed to access 'test_folder_1_' in this context",
            str(err.exception))

    def test_key_access_is_checked_via_security_manager(self):
        self.assert_is_checked_via_security_manager(
            """<p tal:content="python:'{c[0]}'.format(c=[context])" />"""
        )
