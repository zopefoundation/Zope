##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import unittest

class TestTaintedString(unittest.TestCase):
    def setUp(self):
        self.unquoted = '<test attr="&">'
        self.quoted = '&lt;test attr=&quot;&amp;&quot;&gt;'
        self.tainted = self._getClass()(self.unquoted)

    def _getClass(self):
        from ZPublisher.TaintedString import TaintedString
        return TaintedString

    def testStr(self):
        self.assertEquals(str(self.tainted), self.unquoted)

    def testRepr(self):
        self.assertEquals(repr(self.tainted), repr(self.quoted))

    def testCmp(self):
        self.assertEquals(cmp(self.tainted, self.unquoted), 0)
        self.assertEquals(cmp(self.tainted, 'a'), -1)
        self.assertEquals(cmp(self.tainted, '.'), 1)

    def testHash(self):
        hash = {}
        hash[self.tainted] = self.quoted
        hash[self.unquoted] = self.unquoted
        self.assertEquals(hash[self.tainted], self.unquoted)

    def testLen(self):
        self.assertEquals(len(self.tainted), len(self.unquoted))

    def testGetItem(self):
        self.assert_(isinstance(self.tainted[0], self._getClass()))
        self.assertEquals(self.tainted[0], '<')
        self.failIf(isinstance(self.tainted[-1], self._getClass()))
        self.assertEquals(self.tainted[-1], '>')

    def testGetSlice(self):
        self.assert_(isinstance(self.tainted[0:1], self._getClass()))
        self.assertEquals(self.tainted[0:1], '<')
        self.failIf(isinstance(self.tainted[1:], self._getClass()))
        self.assertEquals(self.tainted[1:], self.unquoted[1:])

    def testConcat(self):
        self.assert_(isinstance(self.tainted + 'test', self._getClass()))
        self.assertEquals(self.tainted + 'test', self.unquoted + 'test')
        self.assert_(isinstance('test' + self.tainted, self._getClass()))
        self.assertEquals('test' + self.tainted, 'test' + self.unquoted)

    def testMultiply(self):
        self.assert_(isinstance(2 * self.tainted, self._getClass()))
        self.assertEquals(2 * self.tainted, 2 * self.unquoted)
        self.assert_(isinstance(self.tainted * 2, self._getClass()))
        self.assertEquals(self.tainted * 2, self.unquoted * 2)

    def testInterpolate(self):
        tainted = self._getClass()('<%s>')
        self.assert_(isinstance(tainted % 'foo', self._getClass()))
        self.assertEquals(tainted % 'foo', '<foo>')
        tainted = self._getClass()('<%s attr="%s">')
        self.assert_(isinstance(tainted % ('foo', 'bar'), self._getClass()))
        self.assertEquals(tainted % ('foo', 'bar'), '<foo attr="bar">')

    def testStringMethods(self):
        simple = "capitalize isalpha isdigit islower isspace istitle isupper" \
            " lower lstrip rstrip strip swapcase upper".split()
        returnsTainted = "capitalize lower lstrip rstrip strip swapcase upper"
        returnsTainted = returnsTainted.split()
        unquoted = '\tThis is a test  '
        tainted = self._getClass()(unquoted)
        for f in simple:
            v = getattr(tainted, f)()
            self.assertEquals(v, getattr(unquoted, f)())
            if f in returnsTainted:
                self.assert_(isinstance(v, self._getClass()))
            else:
                self.failIf(isinstance(v, self._getClass()))

        optArg = "lstrip rstrip strip".split()
        for f in optArg:
            v = getattr(tainted, f)(" ")
            self.assertEquals(v, getattr(unquoted, f)(" "))
            self.assert_(isinstance(v, self._getClass()))        

        justify = "center ljust rjust".split()
        for f in justify:
            v = getattr(tainted, f)(30)
            self.assertEquals(v, getattr(unquoted, f)(30))
            self.assert_(isinstance(v, self._getClass()))

        searches = "find index rfind rindex endswith startswith".split()
        searchraises = "index rindex".split()
        for f in searches:
            v = getattr(tainted, f)('test')
            self.assertEquals(v, getattr(unquoted, f)('test'))
            if f in searchraises:
                self.assertRaises(ValueError, getattr(tainted, f), 'nada')

        self.assertEquals(tainted.count('test', 1, -1),
            unquoted.count('test', 1, -1))

        self.assertEquals(tainted.encode(), unquoted.encode())
        self.assert_(isinstance(tainted.encode(), self._getClass()))

        self.assertEquals(tainted.expandtabs(10),
            unquoted.expandtabs(10))
        self.assert_(isinstance(tainted.expandtabs(), self._getClass()))

        self.assertEquals(tainted.replace('test', 'spam'),
            unquoted.replace('test', 'spam'))
        self.assert_(isinstance(tainted.replace('test', '<'), self._getClass()))
        self.failIf(isinstance(tainted.replace('test', 'spam'),
            self._getClass()))

        self.assertEquals(tainted.split(), unquoted.split())
        for part in self._getClass()('< < <').split():
            self.assert_(isinstance(part, self._getClass()))
        for part in tainted.split():
            self.failIf(isinstance(part, self._getClass()))

        multiline = 'test\n<tainted>'
        lines = self._getClass()(multiline).split()
        self.assertEquals(lines, multiline.split())
        self.assert_(isinstance(lines[1], self._getClass()))
        self.failIf(isinstance(lines[0], self._getClass()))

        transtable = ''.join(map(chr, range(256)))
        self.assertEquals(tainted.translate(transtable),
            unquoted.translate(transtable))
        self.assert_(isinstance(self._getClass()('<').translate(transtable),
            self._getClass()))
        self.failIf(isinstance(self._getClass()('<').translate(transtable, '<'),
            self._getClass()))

    def testQuoted(self):
        self.assertEquals(self.tainted.quoted(), self.quoted)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTaintedString, 'test'))
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

def debug():
    test_suite().debug()

def pdebug():
    import pdb
    pdb.run('debug()')

if __name__=='__main__':
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        main()
