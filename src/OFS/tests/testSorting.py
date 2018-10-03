# -*- coding: utf-8 -*-
import codecs
import Testing.ZopeTestCase
import Testing.testbrowser
import Zope2.App


class SortingTests(Testing.ZopeTestCase.FunctionalTestCase):
    """Browser testing ..Image.File"""

    def setUp(self):
        super(SortingTests, self).setUp()

        Zope2.App.zcml.load_site(force=True)

        uf = self.app.acl_users
        uf.userFolderAddUser('manager', 'manager_pass', ['Manager'], [])
        self.app.manage_addFolder('sortingTest')
        self.app.sortingTest.manage_addFile('File1')
        self.app.sortingTest.manage_addFile('File2')
        self.app.sortingTest.File1.update_data(u'hällo'.encode('utf-8'))

        self.browser = Testing.testbrowser.Browser()
        self.browser.addHeader(
            'Authorization',
            'basic {}'.format(codecs.encode(
                b'manager:manager_pass', 'base64').decode()))

    def test_sortby(self):
        base_url = 'http://localhost/sortingTest/manage_main?skey=%s&rkey=%s'

        def do_assert(one_before_two):
            one_before_two_found = (
                self.browser.contents.find('File2') >
                self.browser.contents.find('File1')
            )
            self.assertEqual(one_before_two, one_before_two_found)

        self.browser.open(base_url % ('id', 'asc'))
        do_assert(one_before_two=True)

        self.browser.open(base_url % ('id', 'desc'))
        do_assert(one_before_two=False)

        self.browser.open(base_url % ('get_size', 'asc'))
        do_assert(one_before_two=False)

        self.browser.open(base_url % ('get_size', 'desc'))
        do_assert(one_before_two=True)
