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
        """It respects `zmi_additional_css_paths` lines property."""
        self.folder.manage_addProperty(
            'zmi_additional_css_paths', ['/foo/bar.css', '/baz.css'], 'lines')
        self.assertIn('href="/foo/bar.css"', self.folder.manage_page_header())
        self.assertIn('href="/baz.css"', self.folder.manage_page_header())

    def test_Management__Navigation__manage_page_header__3(self):
        """It ignores an empty `zmi_additional_css_paths` property."""
        self.folder.manage_addProperty(
            'zmi_additional_css_paths', '', 'string')
        self.assertNotIn('href=""', self.folder.manage_page_header())


class TestTabs(Testing.ZopeTestCase.ZopeTestCase):

    def setUp(self):
        from OFS.DTMLMethod import addDTMLMethod
        super().setUp()
        self.app.REQUEST['PARENTS'] = [self.app]
        addDTMLMethod(self.folder, 'page')

    def test_Tabs_tabs_path_default(self):
        path = '/%s/page' % self.folder.getId()
        self.app.REQUEST.traverse(path)

        crumbs = list(self.folder.tabs_path_default(self.app.REQUEST))
        self.assertDictEqual(crumbs[0],
                             {'url': '/manage_workspace', 'title': 'Root',
                              'last': False})
        self.assertDictEqual(crumbs[1],
                             {'url': '/test_folder_1_/manage_workspace',
                              'title': 'test_folder_1_',
                              'last': True})

    def test_Tabs_tabs_path_length(self):
        path = '/%s/page' % self.folder.getId()
        self.app.REQUEST.traverse(path)

        self.assertEqual(self.folder.tabs_path_length(self.app.REQUEST), 2)

    def test_Tabs_content_type(self):
        req = self.app.REQUEST

        self.folder.manage_tabs(req)
        self.assertIn('text/html', req.RESPONSE.getHeader('Content-Type'))


class TestManagePages(Testing.ZopeTestCase.ZopeTestCase):

    def setUp(self):
        super().setUp()
        uf = self.folder.acl_users
        uf.userFolderAddUser('mgr', 'foo', ['Manager'], [])
        self.login('mgr')

    def tearDown(self):
        self.logout()
        super().tearDown()

    def test_manage_content_type(self):
        req = self.app.REQUEST

        self.folder.manage(req)
        self.assertIn('text/html', req.RESPONSE.getHeader('Content-Type'))
