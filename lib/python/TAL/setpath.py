"""
Read a module search path from .path.
"""
import os
import sys
import string

dir = os.path.dirname(__file__)
path = os.path.join(dir, ".path")
try:
    f = open(path)
except IOError:
    raise IOError, "Please edit .path to point to <Zope2/lib/python>"
else:
    for line in f.readlines():
        line = string.strip(line)
        if line and line[0] != '#':
            for dir in string.split(line, os.pathsep):
                dir = os.path.expanduser(os.path.expandvars(dir))
                if dir not in sys.path:
                    sys.path.append(dir)

import ZODB # Must import this first to initialize Persistence properly
