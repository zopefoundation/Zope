# Framework for running Unit tests

import unittest

MODULES = ('commitlog', 'create', 'virgin', 'zodb_simple', 'storage_api')



def suite():
    alltests = unittest.TestSuite()
    for modname in MODULES:
        mod = __import__('test_'+modname)
        alltests.addTest(mod.suite())
    return alltests



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
