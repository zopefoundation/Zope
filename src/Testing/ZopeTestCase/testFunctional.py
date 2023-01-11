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

from io import BytesIO
from urllib.parse import urlencode

from AccessControl import getSecurityManager
from AccessControl.Permissions import manage_properties
from AccessControl.Permissions import view
from DocumentTemplate.permissions import change_dtml_documents
from Testing import ZopeTestCase
from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password


SET_COOKIE_DTML = '''\
<dtml-call "RESPONSE.setCookie('foo', 'Bar', path='/')">'''

CHANGE_TITLE_DTML = '''\
<dtml-call "manage_changeProperties(title=REQUEST.get('title'))">'''


class TestFunctional(ZopeTestCase.FunctionalTestCase):

    def afterSetUp(self):
        self.folder_path = '/' + self.folder.absolute_url(1)
        self.basic_auth = f'{user_name}:{user_password}'

        # A simple document
        self.folder.addDTMLDocument('index_html', file=b'index')

        # A document accessible only to its owner
        self.folder.addDTMLDocument('secret_html', file=b'secret')
        self.folder.secret_html.manage_permission(view, ['Owner'])

        # A method redirecting to the Zope root
        url = self.app.absolute_url().encode('ascii')
        self.folder.addDTMLMethod(
            'redirect',
            file=b'<dtml-call "RESPONSE.redirect(\'%s\')">' % url)

        # A method setting a cookie
        self.folder.addDTMLMethod('set_cookie', file=SET_COOKIE_DTML)

        # A method changing the title property of an object
        self.folder.addDTMLMethod('change_title', file=CHANGE_TITLE_DTML)

        # A method with a non-ascii path
        self.folder.addDTMLMethod('täst', file=b'test')

    def testPublishFolder(self):
        response = self.publish(self.folder_path)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), b'index')

    def testPublishDocument(self):
        response = self.publish(self.folder_path + '/index_html')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), b'index')

    def testPublishDocumentNonAscii(self):
        response = self.publish(self.folder_path + '/täst')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), b'test')

    def testPublishDocumentNonAsciiUrlEncoded(self):
        response = self.publish(self.folder_path + '/t%C3%A4st')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), b'test')

    def testUnauthorized(self):
        response = self.publish(self.folder_path + '/secret_html')
        self.assertEqual(response.getStatus(), 401)

    def testBasicAuth(self):
        response = self.publish(self.folder_path + '/secret_html',
                                self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), b'secret')

    def testRedirect(self):
        response = self.publish(self.folder_path + '/redirect')
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         self.app.absolute_url())

    def testCookie(self):
        response = self.publish(self.folder_path + '/set_cookie')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getCookie('foo').get('value'), 'Bar')
        self.assertEqual(response.getCookie('foo').get('Path'), '/')

    def testChangeTitle(self):
        # Change the title of a document
        self.setPermissions([manage_properties])

        path = self.folder_path + '/index_html/change_title?title=Foo'
        # Note that we must pass basic auth info
        response = self.publish(path, self.basic_auth)

        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(self.folder.index_html.title_or_id(), 'Foo')

    def testPOST(self):
        # Change the title in a POST request
        self.setPermissions([manage_properties])

        form = {'title': 'Foo'}
        post_data = BytesIO(urlencode(form).encode('utf-8'))

        response = self.publish(self.folder_path + '/index_html/change_title',
                                request_method='POST', stdin=post_data,
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(self.folder.index_html.title_or_id(), 'Foo')

    def testPUTExisting(self):
        # PUT new data into an existing object
        self.setPermissions([change_dtml_documents])

        put_data = BytesIO(b'foo')
        response = self.publish(self.folder_path + '/index_html',
                                request_method='PUT', stdin=put_data,
                                basic=self.basic_auth)

        self.assertEqual(response.getStatus(), 204)
        self.assertEqual(self.folder.index_html(), 'foo')

    def testHEAD(self):
        # HEAD should work without passing stdin
        response = self.publish(self.folder_path + '/index_html',
                                request_method='HEAD')

        self.assertEqual(response.getStatus(), 200)

    def testSecurityContext(self):
        # The authenticated user should not change as a result of publish
        self.assertEqual(getSecurityManager().getUser().getId(), user_name)

        self.folder.acl_users.userFolderAddUser('barney', 'secret', [], [])
        self.publish(self.folder_path, basic='barney:secret')

        self.assertEqual(getSecurityManager().getUser().getId(), user_name)


def test_suite():
    import unittest

    return unittest.defaultTestLoader.loadTestsFromTestCase(TestFunctional)
