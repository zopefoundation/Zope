#
# Example doctest
#

# $Id: testWarningsTest.py,v 1.2 2005/03/26 18:07:08 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from unittest import TestSuite
from Testing.ZopeTestCase import ZopeDocFileSuite


def test_suite():
    return TestSuite((
        ZopeDocFileSuite('WarningsTest.txt'),
    ))

if __name__ == '__main__':
    framework()

