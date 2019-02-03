import os.path
import six
from six.moves.urllib.parse import unquote

from Acquisition import aq_base
import Testing.ZopeTestCase


class TestNavigation(Testing.ZopeTestCase.ZopeTestCase):

    def test_interfaces(self):
        from App.interfaces import INavigation
        from App.Management import Navigation
        from zope.interface.verify import verifyClass

        verifyClass(INavigation, Navigation)

    def test_Management__Navigation__manage_page_header__1(self):
        """It respects `zmi_additional_css_paths` string property."""
        self.folder.manage_addProperty(
            'zmi_additional_css_paths', '/foo/bar.css', 'string')
        self.assertIn('href="/foo/bar.css"', self.folder.manage_page_header())

    def test_Management__Navigation__manage_page_header__2(self):
        """It respects `zmi_additional_css_paths` ustring property."""
        self.folder.manage_addProperty(
            'zmi_additional_css_paths', '/foo/bar.css', 'ustring')
        self.assertIn('href="/foo/bar.css"', self.folder.manage_page_header())

    def test_Management__Navigation__manage_page_header__3(self):
        """It respects `zmi_additional_css_paths` lines property."""
        self.folder.manage_addProperty(
            'zmi_additional_css_paths', ['/foo/bar.css', '/baz.css'], 'ulines')
        self.assertIn('href="/foo/bar.css"', self.folder.manage_page_header())
        self.assertIn('href="/baz.css"', self.folder.manage_page_header())

    def test_Management__Navigation__manage_page_header__4(self):
        """It respects `zmi_additional_css_paths` ulines property."""
        self.folder.manage_addProperty(
            'zmi_additional_css_paths', ['/foo/bar.css', '/baz.css'], 'ulines')
        self.assertIn('href="/foo/bar.css"', self.folder.manage_page_header())
        self.assertIn('href="/baz.css"', self.folder.manage_page_header())

    def test_Management__Navigation__manage_page_header__5(self):
        """It ignores an empty `zmi_additional_css_paths` property."""
        self.folder.manage_addProperty(
            'zmi_additional_css_paths', '', 'string')
        self.assertNotIn('href=""', self.folder.manage_page_header())


class TestTabs(Testing.ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        super(TestTabs, self).afterSetUp()
        # Need to set PARENTS on the request, needed by REQUEST.traverse
        self.request = self.app.REQUEST
        self.request.other.update({'PARENTS': [self.app]})

    def _makeOne(self):
        from App.Management import Tabs
        return Tabs()

    def test_tabs_path_default_nonascii(self):
        """ Test manage_tabs breadcrumbs info with non-ASCII IDs
        """
        from OFS.Image import manage_addFile
        u_test_id = u'\xe4\xf6\xfc'
        if six.PY2:
            test_id = u_test_id.encode('UTF-8')
        else:
            test_id = u_test_id
            
        manage_addFile(self.folder, test_id)
        test_file = self.folder._getOb(test_id)
        test_file_path = '/%s/%s' % (self.folder.getId(), test_file.getId())
        tabs = self._makeOne()

        # Set up the request by traversing to the test file
        self.request.traverse(test_file_path)
        tab_info = list(tabs.tabs_path_default(self.request))
        test_tab = tab_info[-1]  # The last element is the test file

        self.assertTrue(test_tab['last'])
        self.assertEqual(test_tab['title'], u_test_id)
        tab_path = unquote(test_tab['url'])
        self.assertEqual(tab_path, '%s/manage_workspace' % test_file_path)

        # See if what we get from the path is really what we want
        grabbed = self.app.unrestrictedTraverse(os.path.dirname(tab_path))
        self.assertTrue(aq_base(test_file) is aq_base(grabbed))
