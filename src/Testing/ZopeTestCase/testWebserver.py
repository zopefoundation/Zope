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
"""Example ZopeTestCase testing web access to a freshly started ZServer

Note that we need to set up the error_log before starting the ZServer.

Note further that the test thread needs to explicitly commit its
transactions, so the ZServer threads can see modifications made to
the ZODB.

IF YOU THINK YOU NEED THE WEBSERVER STARTED YOU ARE PROBABLY WRONG!
This is only required in very special cases, like when testing
ZopeXMLMethods where XSLT processing is done by external tools that
need to URL-call back into the Zope server.

If you want to write functional unit tests, see the testFunctional.py 
example instead.
"""

from Testing import ZopeTestCase

from Testing.ZopeTestCase import transaction
from AccessControl import Unauthorized
import urllib

# Create the error_log object
ZopeTestCase.utils.setupSiteErrorLog()

# Start the web server
ZopeTestCase.utils.startZServer()


class ManagementOpener(urllib.FancyURLopener):
    '''Logs on as manager when prompted'''
    def prompt_user_passwd(self, host, realm):
        return ('manager', 'secret')


class UnauthorizedOpener(urllib.FancyURLopener):
    '''Raises Unauthorized when prompted'''
    def prompt_user_passwd(self, host, realm):
        raise Unauthorized, 'The URLopener was asked for authentication'


class TestWebserver(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        uf = self.folder.acl_users
        uf.userFolderAddUser('manager', 'secret', ['Manager'], [])

        self.folder_url = self.folder.absolute_url()

        # A simple document
        self.folder.addDTMLDocument('index_html', file='index_html called')

        # A document only accessible to manager
        self.folder.addDTMLDocument('secret_html', file='secret_html called')

        for p in ZopeTestCase.standard_permissions:
            self.folder.secret_html.manage_permission(p, ['Manager'])

        # A method to change the title property of an object
        self.folder.addDTMLMethod('change_title', 
            file='''<dtml-call "manage_changeProperties(title=REQUEST.get('title'))">'''
                 '''<dtml-var title_or_id>''')

        manager = uf.getUserById('manager').__of__(uf)
        self.folder.change_title.changeOwnership(manager)

        # Commit so the ZServer threads can see the changes
        transaction.commit()

    def beforeClose(self):
        # Commit after cleanup
        transaction.commit()

    def testAccessPublicObject(self):
        # Test access to a public resource
        page = self.folder.index_html(self.folder)
        self.assertEqual(page, 'index_html called')

    def testURLAccessPublicObject(self):
        # Test web access to a public resource
        urllib._urlopener = ManagementOpener()
        page = urllib.urlopen(self.folder_url+'/index_html').read()
        self.assertEqual(page, 'index_html called')

    def testAccessProtectedObject(self):
        # Test access to a protected resource
        page = self.folder.secret_html(self.folder)
        self.assertEqual(page, 'secret_html called')

    def testURLAccessProtectedObject(self):
        # Test web access to a protected resource
        urllib._urlopener = ManagementOpener()
        page = urllib.urlopen(self.folder_url+'/secret_html').read()
        self.assertEqual(page, 'secret_html called')

    def testSecurityOfPublicObject(self):
        # Test security of a public resource
        try: 
            self.folder.restrictedTraverse('index_html')
        except Unauthorized:
            # Convert error to failure
            self.fail('Unauthorized')

    def testURLSecurityOfPublicObject(self):
        # Test web security of a public resource
        urllib._urlopener = UnauthorizedOpener()
        try: 
            urllib.urlopen(self.folder_url+'/index_html')
        except Unauthorized:
            # Convert error to failure
            self.fail('Unauthorized')

    def testSecurityOfProtectedObject(self):
        # Test security of a protected resource
        try:
            self.folder.restrictedTraverse('secret_html')
        except Unauthorized:
            pass    # Test passed
        else:
            self.fail('Resource not protected')

    def testURLSecurityOfProtectedObject(self):
        # Test web security of a protected resource
        urllib._urlopener = UnauthorizedOpener()
        try: 
            urllib.urlopen(self.folder_url+'/secret_html')
        except Unauthorized:
            pass    # Test passed
        else:
            self.fail('Resource not protected')

    def testModifyObject(self):
        # Test a script that modifies the ZODB
        self.setRoles(['Manager'])
        self.app.REQUEST.set('title', 'Foo')
        page = self.folder.index_html.change_title(self.folder.index_html,
                                                   self.app.REQUEST)
        self.assertEqual(page, 'Foo')
        self.assertEqual(self.folder.index_html.title, 'Foo')

    def testURLModifyObject(self):
        # Test a transaction that actually commits something
        urllib._urlopener = ManagementOpener()
        page = urllib.urlopen(self.folder_url+'/index_html/change_title?title=Foo').read()
        self.assertEqual(page, 'Foo')


class TestSandboxedWebserver(ZopeTestCase.Sandboxed, TestWebserver):
    '''Demonstrates that tests involving ZServer threads can also be 
       run from sandboxes. In fact, it may be preferable to do so.
    '''

    # Note: By inheriting from TestWebserver we run the same 
    # test methods as above!

    def testConnectionIsShared(self):
        # Due to sandboxing the ZServer thread operates on the
        # same connection as the main thread, allowing us to
        # see changes made to 'index_html' right away.
        urllib._urlopener = ManagementOpener()
        urllib.urlopen(self.folder_url+'/index_html/change_title?title=Foo')
        self.assertEqual(self.folder.index_html.title, 'Foo')

    def testCanCommit(self):
        # Additionally, it allows us to commit transactions without
        # harming the test ZODB.
        self.folder.foo = 1
        transaction.commit()
        self.folder.foo = 2
        transaction.commit()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestWebserver))
    suite.addTest(makeSuite(TestSandboxedWebserver))
    return suite

