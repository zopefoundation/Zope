##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

######################################################################
# Set up unit testing framework
#
# The following code should be at the top of every test module:
#
# import os, sys
# execfile(os.path.join(sys.path[0], 'framework.py'))
#
# ...and the following at the bottom:
#
# if __name__ == '__main__':
#     main()

import string

scriptdir = sys.path[0]
input_dir = os.path.join(scriptdir, 'input')
output_dir = os.path.join(scriptdir, 'output')

if not sys.modules.has_key('unittest'):
    if os.path.abspath(scriptdir) == os.path.abspath('.'):
        # We're in the tests directory, and need to find unittest.
        cwd = os.getcwd()
        while 1:
            for ext in 'py', 'pyc', 'pyo', 'pyd':
                if os.path.isfile(os.path.join(cwd, 'unittest.' + ext)):
                    break
            else:
                cwd, lastdir = os.path.split(cwd)
                if lastdir:
                    continue
            break
        sys.path.insert(1, cwd)
    else:
        # We must be in the same directory as unittest
        sys.path.insert(1, '')

import unittest

TestRunner = unittest.TextTestRunner

def read_input(filename):
    filename = os.path.join(input_dir, filename)
    return open(filename, 'r').read()

def read_output(filename):
    filename = os.path.join(output_dir, filename)
    return open(filename, 'r').read()

def main():
   if len(sys.argv) > 1:
       errs = globals()[sys.argv[1]]()
   else:
       errs = TestRunner().run(test_suite())
   sys.exit(errs and 1 or 0)

def debug():
   test_suite().debug()

def pdebug():
   import pdb
   pdb.run('debug()')
   


