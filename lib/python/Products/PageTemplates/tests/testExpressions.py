import os, sys
execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.PageTemplates import Expressions

class ExpressionTests(unittest.TestCase):

    def testCompile(self):
        '''Test expression compilation'''
        e = Expressions.getEngine()
        for p in ('x', 'x/y', 'x/y/z'):
            e.compile(p)
            for m in range(2 ** 3):
                mods = ''
                if m & 1: mods = 'if'
                if m & 2: mods = mods + ' exists'
                if m & 4: mods = mods + ' nocall'
                e.compile('(%s) %s' % (mods, p))
        e.compile('string:Fred')
        e.compile('string:A$B')
        e.compile('string:a ${x/y} b ${y/z} c')
        e.compile('python: 2 + 2')
        
def test_suite():
    return unittest.makeSuite(ExpressionTests)

if __name__=='__main__':
    main()
