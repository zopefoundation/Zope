# This software is subject to the provisions of the Zope Public License,
# Version 1.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.

"""
Read a module search path from .path.
"""
import os
import sys

dir = os.path.dirname(__file__)
path = os.path.join(dir, ".path")
try:
    f = open(path)
except IOError:
    raise IOError, "Please edit .path to point to <Zope2/lib/python>"
else:
    for line in f.readlines():
        line = line.strip()
        if line and line[0] != '#':
            for dir in line.split(os.pathsep):
                dir = os.path.expanduser(os.path.expandvars(dir))
                if dir not in sys.path:
                    sys.path.append(dir)

import ZODB # Must import this first to initialize Persistence properly
