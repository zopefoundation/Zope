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
"""ThreadLock tests

>>> lock = ThreadLock.allocate_lock()

>>> twoshouldstart = threading.Event()

>>> n = 0
>>> readbytwo = None

>>> def one():
...     global n
...     lock.acquire()
...     twoshouldstart.set()
...     for i in range(10):
...         time.sleep(.001)
...         lock.acquire()
...         n += 1
... 
...     for i in range(10):
...         time.sleep(.001)
...         lock.release()
... 
...     lock.release()

>>> def two():
...     global readbytwo
...     twoshouldstart.wait()
...     lock.acquire()
...     readbytwo = n
...     lock.release()

>>> ttwo = threading.Thread(target=two)
>>> ttwo.start()
>>> time.sleep(0.001)
>>> tone = threading.Thread(target=one)
>>> tone.start()
>>> tone.join()
>>> ttwo.join()
>>> readbytwo
10

$Id: tests.py,v 1.2 2003/11/28 16:46:39 jim Exp $
"""

import ThreadLock, threading, time
import unittest
from doctest import DocTestSuite

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__': unittest.main()
