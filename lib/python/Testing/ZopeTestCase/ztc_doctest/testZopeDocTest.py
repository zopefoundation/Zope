#
# Example Zope doctest
#

# $Id: testZopeDocTest.py,v 1.2 2005/02/16 14:21:59 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

package = 'Testing.ZopeTestCase.ztc_doctest'


def setUp(self):
    '''This method will run after the test_class' setUp.
    '''
    self.folder.manage_addFolder('object', '')


def test_suite():
    from unittest import TestSuite
    from Testing.ZopeTestCase import ZopeDocFileSuite

    return TestSuite((
        ZopeDocFileSuite('ZopeDocTest.txt', package=package, setUp=setUp),
    ))

if __name__ == '__main__':
    framework()

