import os, sys, unittest

from Products.PageTemplates import Expressions

class ExpressionTests(unittest.TestCase):

    def testCompile(self):
        '''Test expression compilation'''
        e = Expressions.getEngine()
        for p in ('x', 'x/y', 'x/y/z'):
            e.compile(p)
        e.compile('path:a|b|c/d/e')
        e.compile('string:Fred')
        e.compile('string:A$B')
        e.compile('string:a ${x/y} b ${y/z} c')
        e.compile('python: 2 + 2')
        e.compile('python: 2 \n+\n 2\n')

def test_suite():
    return unittest.makeSuite(ExpressionTests)

if __name__=='__main__':
    main()
