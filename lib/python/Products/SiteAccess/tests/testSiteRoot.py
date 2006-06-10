"""SiteRoot regression tests.

These tests verify that the request URL headers, in particular ACTUAL_URL, are
set correctly when a SiteRoot is used.

See http://www.zope.org/Collectors/Zope/2077

"""

from Testing.makerequest import makerequest

import Zope2
Zope2.startup()

import transaction

import unittest

class SiteRootRegressions(unittest.TestCase):

    def setUp(self):
        transaction.begin()
        self.app = makerequest(Zope2.app())
        try:
            self.app.manage_addFolder('folder')
	    self.app.folder.manage_addProduct['SiteAccess'].manage_addSiteRoot(title = 'SiteRoot', base = 'http://test_base', path = '/test_path')
	    self.app.REQUEST.set('PARENTS', [self.app])
	    self.app.REQUEST.traverse('/folder')
	    
        except:
            self.tearDown()

    def tearDown(self):
        transaction.abort()
        self.app._p_jar.close()
	
    def testRequest(self):
        self.assertEqual(self.app.REQUEST['SERVER_URL'], 'http://test_base') 
	self.assertEqual(self.app.REQUEST['URL'], 'http://test_base/test_path/index_html')
	self.assertEqual(self.app.REQUEST['ACTUAL_URL'], 'http://test_base/test_path')
    def testAbsoluteUrl(self):	    
	self.assertEqual(self.app.folder.absolute_url(), 'http://test_base/test_path')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SiteRootRegressions))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
