#
# Example Zope doctest
#

# $Id: testZopeDocTest.py,v 1.2 2005/03/26 18:07:08 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from unittest import TestSuite
from Testing.ZopeTestCase import ZopeDocTestSuite
from Testing.ZopeTestCase import ZopeDocFileSuite


def setUp(self):
    '''This method will run after the test_class' setUp.

    >>> 'object' in folder.objectIds()
    True
    '''
    self.folder.manage_addFolder('object', '')


def test_suite():
    return TestSuite((
        ZopeDocTestSuite(setUp=setUp),
        ZopeDocFileSuite('ZopeDocTest.txt', setUp=setUp),
    ))

if __name__ == '__main__':
    framework()

