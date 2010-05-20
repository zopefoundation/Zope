"""SiteRoot regression tests.

These tests verify that the request URL headers, in particular ACTUAL_URL, are
set correctly when a SiteRoot is used.

See http://www.zope.org/Collectors/Zope/2077
"""
import unittest

class SiteRootRegressions(unittest.TestCase):

    def setUp(self):
        import transaction
        from Testing.makerequest import makerequest
        from Testing.ZopeTestCase.ZopeLite import app
        transaction.begin()
        self.app = makerequest(app())
        self.app.manage_addFolder('folder')
        p_disp = self.app.folder.manage_addProduct['SiteAccess']
        p_disp.manage_addSiteRoot(title='SiteRoot',
                                    base='http://test_base',
                                    path='/test_path')
        self.app.REQUEST.set('PARENTS', [self.app])
        self.app.REQUEST.traverse('/folder')

    def tearDown(self):
        import transaction
        transaction.abort()
        self.app._p_jar.close()
        
    def testRequest(self):
        self.assertEqual(self.app.REQUEST['SERVER_URL'], 'http://test_base') 
        self.assertEqual(self.app.REQUEST['URL'],
                         'http://test_base/test_path/index_html')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://test_base/test_path')
    def testAbsoluteUrl(self):            
        self.assertEqual(self.app.folder.absolute_url(),
                         'http://test_base/test_path')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SiteRootRegressions))
    return suite
