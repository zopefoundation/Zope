"""
Edit this file to set the proper module search path.
"""
import os
import sys

home = os.path.expanduser("~")
Zopes = os.path.join(home, 'Zope')
pt = os.path.join(Zopes, 'pt')
libPython = os.path.join(pt, 'lib', 'python')

sys.path.append(libPython)

import ZODB # Must import this first to initialize Persistence properly
