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
