#
# Runs all tests in the current directory [and below]
#
# Execute like:
#   python runalltests.py [-R]
#
# Alternatively use the testrunner:
#   python /path/to/Zope/bin/testrunner.py -qa
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest, imp
TestRunner = unittest.TextTestRunner
suite = unittest.TestSuite()

def visitor(recursive, dir, names):
    tests = [n[:-3] for n in names if n.startswith('test') and n.endswith('.py')]

    for test in tests:
        saved_syspath = sys.path[:]
        sys.path.insert(0, dir)
        try:
            fp, path, desc = imp.find_module(test, [dir])
            m = imp.load_module(test, fp, path, desc)
            if hasattr(m, 'test_suite'):
                suite.addTest(m.test_suite())
        finally:
            fp.close()
            sys.path[:] = saved_syspath

    if not recursive:
        names[:] = []

if __name__ == '__main__':
    os.path.walk(os.curdir, visitor, '-R' in sys.argv)
    TestRunner().run(suite)

