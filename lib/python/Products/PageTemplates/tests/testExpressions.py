import os, sys
execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.PageTemplates import Expressions

class ExpressionTests(unittest.TestCase):

    def testCompile(self):
        '''Test expression compilation'''
        e = Expressions.getEngine()
        e.compile('x')
        e.compile('path:x')
        e.compile('x/y')
        e.compile('string:Fred')
        e.compile('python: 2 + 2')
        
def test_suite():
    return unittest.makeSuite(ExpressionTests)

if __name__=='__main__':
    main()
