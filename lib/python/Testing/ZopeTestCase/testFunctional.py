#
# Example functional ZopeTestCase
#

# $Id: testFunctional.py,v 1.7 2004/09/04 18:01:08 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

ZopeTestCase.installProduct('PythonScripts')


class TestFunctional(ZopeTestCase.Functional, ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.folder_path = '/%s' % self.folder.absolute_url(1)
        self.basic_auth = '%s:%s' % (ZopeTestCase.user_name, ZopeTestCase.user_password)

        self.folder.addDTMLMethod('index_html', file='foo')

        dispatcher = self.folder.manage_addProduct['PythonScripts']
        dispatcher.manage_addPythonScript('script')
        self.folder.script.ZPythonScript_edit('a=0', 'return a+1')

        self.folder.manage_addFolder('object', '')
        self.folder.addDTMLMethod('change_title', 
            file='''<dtml-call "manage_changeProperties(title=REQUEST.get('title'))">''')

    def testPublishDocument(self):
        response = self.publish(self.folder_path+'/index_html')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), 'foo')

    def testPublishScript(self):
        response = self.publish(self.folder_path+'/script')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), '1')

    def testPublishScriptWithArgument(self):
        response = self.publish(self.folder_path+'/script?a:int=2')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), '3')

    def testServerError(self):
        response = self.publish(self.folder_path+'/script?a=2')
        self.assertEqual(response.getStatus(), 500)

    def testUnauthorized(self):
        self.folder.index_html.manage_permission('View', ['Owner'])
        response = self.publish(self.folder_path+'/index_html')
        self.assertEqual(response.getStatus(), 401)

    def testBasicAuthentication(self):
        self.folder.index_html.manage_permission('View', ['Owner'])
        response = self.publish(self.folder_path+'/index_html',
                                self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), 'foo')

    def testModifyObject(self):
        from AccessControl.Permissions import manage_properties
        self.setPermissions([manage_properties])
        response = self.publish(self.folder_path+'/object/change_title?title=Foo',
                                self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(self.folder.object.title_or_id(), 'Foo')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestFunctional))
    return suite

if __name__ == '__main__':
    framework()

