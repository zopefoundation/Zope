#
# Example functional doctest
#

# $Id: testFunctionalDocTest.py,v 1.7 2005/02/16 14:21:59 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
ZopeTestCase.installProduct('PythonScripts')

package = 'Testing.ZopeTestCase.ztc_doctest'


def setUp(self):
    '''This method will run after the test_class' setUp.
    '''
    self.folder.addDTMLDocument('index_html', file='index')

    self.folder.manage_addProduct['PythonScripts'].manage_addPythonScript('script')
    self.folder.script.ZPythonScript_edit(params='a=0', body='return a+1')

    change_title = '''<dtml-call "manage_changeProperties(title=REQUEST.get('title'))">'''
    self.folder.addDTMLMethod('change_title', file=change_title)


def test_suite():
    from unittest import TestSuite
    from Testing.ZopeTestCase import FunctionalDocFileSuite

    return TestSuite((
        FunctionalDocFileSuite('FunctionalDocTest.txt', package=package, setUp=setUp),
    ))

if __name__ == '__main__':
    framework()

