"""
Edit this file to set the proper module search path.
"""
import os
import sys

home = os.path.expanduser("~")
projects = os.path.join(home, 'projects')
zope2 = os.path.join(projects, 'Zope2')
libPython = os.path.join(zope2, 'lib', 'python')

sys.path.append(libPython)

import ZODB # Must import this first to initialize Persistence properly
