#
# Example functional doctest
#

# $Id: testWarningsTest.py,v 1.4 2005/02/16 14:21:59 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

package = 'Testing.ZopeTestCase.ztc_doctest'


def test_suite():
    from unittest import TestSuite
    from Testing.ZopeTestCase import FunctionalDocFileSuite

    return TestSuite((
        FunctionalDocFileSuite('WarningsTest.txt', package=package),
    ))

if __name__ == '__main__':
    framework()

