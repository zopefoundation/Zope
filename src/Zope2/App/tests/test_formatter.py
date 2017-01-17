from Testing.ZopeTestCase import FunctionalTestCase
from zExceptions import Unauthorized

import unittest


BAD_STR = """
<p tal:content="python:'class of {0} is {0.__class__}'.format(context)" />
"""
BAD_UNICODE = """
<p tal:content="python:u'class of {0} is {0.__class__}'.format(context)" />
"""
GOOD_STR = '<p tal:content="python:(\'%s\' % context).lower()" />'
GOOD_UNICODE = '<p tal:content="python:(\'%s\' % context).lower()" />'


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
        self.assertRaises(Unauthorized, pt.pt_render)

    def test_cook_zope2_page_templates_bad_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', BAD_UNICODE)
        hack_pt(pt)
        self.assertRaises(Unauthorized, pt.pt_render)

    def test_cook_zope2_page_templates_good_str(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', GOOD_STR)
        hack_pt(pt)
        self.assertEqual(pt.pt_render().strip(), '<p>none</p>')

    def test_cook_zope2_page_templates_good_unicode(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        pt = ZopePageTemplate('mytemplate', unicode(GOOD_UNICODE))
        hack_pt(pt)
        self.assertEqual(pt.pt_render().strip(), '<p>none</p>')

    def test_positional_argument_regression(self):
        """
        to test http://bugs.python.org/issue13598 issue
        """
        from Zope2.App.safe_formatter import SafeFormatter
        try:
            self.assertEquals(
                SafeFormatter('{} {}').safe_format('foo', 'bar'),
                'foo bar'
            )
        except ValueError:
            # On Python 2.6 you get:
            # ValueError: zero length field name in format
            pass

        self.assertEquals(
            SafeFormatter('{0} {1}').safe_format('foo', 'bar'),
            'foo bar'
        )
        self.assertEquals(
            SafeFormatter('{1} {0}').safe_format('foo', 'bar'),
            'bar foo'
        )


class FormatterFunctionalTest(FunctionalTestCase):

    def test_access_to_private_content_not_allowed_via_any_attribute(self):
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        # If access to _delObject would be allowed, it would still only say
        # something like 'bound method _delObject', without actually deleting
        # anything, because methods are not executed in str.format, but there
        # may be @properties that give an attacker secret info.
        pt = ZopePageTemplate('mytemplate', '''
<p tal:content="structure python:'access {0._delObject}'.format(context)" />
''')
        hack_pt(pt, context=self.app)
        self.assertRaises(Unauthorized, pt.pt_render)

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
