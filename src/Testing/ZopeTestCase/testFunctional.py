##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Example functional ZopeTestCase

Demonstrates how to use the publish() API to execute GET, POST, PUT, etc.
requests against the ZPublisher and how to examine the response.
"""

from Testing import ZopeTestCase

from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password

from AccessControl import getSecurityManager
from AccessControl.Permissions import view
from AccessControl.Permissions import manage_properties
from AccessControl.Permissions import add_documents_images_and_files
from DocumentTemplate.permissions import change_dtml_documents

from StringIO import StringIO
from urllib import urlencode


class TestFunctional(ZopeTestCase.FunctionalTestCase):

    def afterSetUp(self):
        self.folder_path = '/'+self.folder.absolute_url(1)
        self.basic_auth = '%s:%s' % (user_name, user_password)

        # A simple document
        self.folder.addDTMLDocument('index_html', file='index')

        # A document accessible only to its owner
        self.folder.addDTMLDocument('secret_html', file='secret')
        self.folder.secret_html.manage_permission(view, ['Owner'])

        # A method redirecting to the Zope root
        redirect = '''<dtml-call "RESPONSE.redirect('%s')">''' % self.app.absolute_url()
        self.folder.addDTMLMethod('redirect', file=redirect)

        # A method setting a cookie
        set_cookie = '''<dtml-call "RESPONSE.setCookie('foo', 'Bar', path='/')">'''
        self.folder.addDTMLMethod('set_cookie', file=set_cookie)

        # A method changing the title property of an object
        change_title = '''<dtml-call "manage_changeProperties(title=REQUEST.get('title'))">'''
        self.folder.addDTMLMethod('change_title', file=change_title)

    def testPublishFolder(self):
        response = self.publish(self.folder_path)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), 'index')

    def testPublishDocument(self):
        response = self.publish(self.folder_path+'/index_html')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), 'index')

    def testUnauthorized(self):
        response = self.publish(self.folder_path+'/secret_html')
        self.assertEqual(response.getStatus(), 401)

    def testBasicAuth(self):
        response = self.publish(self.folder_path+'/secret_html', self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), 'secret')

    def testRedirect(self):
        response = self.publish(self.folder_path+'/redirect')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'), self.app.absolute_url())

    def testCookie(self):
        response = self.publish(self.folder_path+'/set_cookie')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getCookie('foo').get('value'), 'Bar')
        self.assertEqual(response.getCookie('foo').get('path'), '/')

    def testChangeTitle(self):
        # Change the title of a document
        self.setPermissions([manage_properties])

        # Note that we must pass basic auth info
        response = self.publish(self.folder_path+'/index_html/change_title?title=Foo',
                                self.basic_auth)

        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(self.folder.index_html.title_or_id(), 'Foo')

    def testPOST(self):
        # Change the title in a POST request
        self.setPermissions([manage_properties])

        form = {'title': 'Foo'}
        post_data = StringIO(urlencode(form))

        response = self.publish(self.folder_path+'/index_html/change_title',
                                request_method='POST', stdin=post_data,
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(self.folder.index_html.title_or_id(), 'Foo')

    def testPUTExisting(self):
        # FTP new data into an existing object
        self.setPermissions([change_dtml_documents])

        put_data = StringIO('foo')
        response = self.publish(self.folder_path+'/index_html',
                                request_method='PUT', stdin=put_data,
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 204)
        self.assertEqual(self.folder.index_html(), 'foo')

    def testPUTNew(self):
        # Create a new object via FTP or WebDAV
        self.setPermissions([add_documents_images_and_files])

        put_data = StringIO('foo')
        response = self.publish(self.folder_path+'/new_document',
                                env={'CONTENT_TYPE': 'text/html'},
                                request_method='PUT', stdin=put_data,
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 201)
        self.assertTrue('new_document' in self.folder.objectIds())
        self.assertEqual(self.folder.new_document.meta_type, 'DTML Document')
        self.assertEqual(self.folder.new_document(), 'foo')

    def testPUTEmpty(self):
        # PUT operation without passing stdin should result in empty content
        self.setPermissions([change_dtml_documents])

        response = self.publish(self.folder_path+'/index_html',
                                request_method='PUT',
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 204)
        self.assertEqual(self.folder.index_html(), '')

    def testPROPFIND(self):
        # PROPFIND should work without passing stdin
        response = self.publish(self.folder_path+'/index_html',
                                request_method='PROPFIND',
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 207)

    def testHEAD(self):
        # HEAD should work without passing stdin
        response = self.publish(self.folder_path+'/index_html',
                                request_method='HEAD')

        self.assertEqual(response.getStatus(), 200)

    def testSecurityContext(self):
        # The authenticated user should not change as a result of publish
        self.assertEqual(getSecurityManager().getUser().getId(), user_name)

        self.folder.acl_users.userFolderAddUser('barney', 'secret', [], [])
        self.publish(self.folder_path, basic='barney:secret')

        self.assertEqual(getSecurityManager().getUser().getId(), user_name)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestFunctional))
    return suite

