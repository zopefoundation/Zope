##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Record tests

$Id: tests.py,v 1.2 2003/11/28 16:46:36 jim Exp $
"""

from Record import Record
import pickle

class P(Record):
     __record_schema__ = {'a': 0, 'b': 1, 'c': 2}

def test_RecordPickling():
    """

    We can create records from sequences:
    
    >>> r = P(('x', 42, 1.23))

    We can pickle them:

    >>> r2 = pickle.loads(pickle.dumps(r))
    >>> list(r) == list(r2)
    1
    >>> r.__record_schema__ == r2.__record_schema__
    1
    """

import unittest
from doctest import DocTestSuite

def test_suite():
    return unittest.TestSuite((
        DocTestSuite('Record'),
        DocTestSuite(),
        ))

if __name__ == '__main__': unittest.main()
