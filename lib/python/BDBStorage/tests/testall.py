# Framework for running Unit tests

import sys
import unittest

MODULES = ('commitlog', 'create', 'virgin', 'zodb_simple',
           'storage_api', 'storage_undo')



def suite():
    alltests = unittest.TestSuite()
    for mod in [__import__('test_'+mod) for mod in MODULES]:
        alltests.addTest(mod.suite())
    return alltests



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
