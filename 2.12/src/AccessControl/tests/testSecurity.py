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
"""Document Template Tests
"""

__rcs_id__='$Id$'
__version__='$Revision: 1.13 $'[11:-2]

import os, sys, unittest

import ZODB
from DocumentTemplate import HTML
from DocumentTemplate.tests.testDTML import DTMLTests
from Products.PythonScripts.standard import DTML
from AccessControl import User, Unauthorized
from ExtensionClass import Base

class UnownedDTML(DTML):
    def getOwner(self):
        return None

class SecurityTests (DTMLTests):
    doc_class = UnownedDTML
    unrestricted_doc_class = HTML

    def testNoImplicitAccess(self):
        class person:
            name='Jim'

        doc = self.doc_class(
            '<dtml-with person>Hi, my name is '
            '<dtml-var name></dtml-with>')
        try:
            doc(person=person())
        except Unauthorized:
            # Passed the test.
            pass
        else:
            assert 0, 'Did not protect class instance'

    def testExprExplicitDeny(self):
        class myclass (Base):
            __roles__ = None  # Public
            somemethod__roles__ = ()  # Private
            def somemethod(self):
                return "This is a protected operation of public object"

        html = self.doc_class('<dtml-var expr="myinst.somemethod()">')
        self.failUnlessRaises(Unauthorized, html, myinst=myclass())

    def testSecurityInSyntax(self):
        # Ensures syntax errors are thrown for an expr with restricted
        # syntax.
        expr = '<dtml-var expr="(lambda x, _read=(lambda ob:ob): x.y)(c)">'
        try:
            # This would be a security hole.
            html = self.doc_class(expr)  # It might compile here...
            html()                       # or it might compile here.
        except SyntaxError:
            # Passed the test.
            pass
        else:
            assert 0, 'Did not catch bad expr'
        # Now be sure the syntax error occurred for security purposes.
        html = self.unrestricted_doc_class(expr)
        class c:
            y = 10
        res = html(c=c)
        assert res == '10', res

    def testNewDTMLBuiltins(self):

        NEW_BUILTINS_TEMPLATE = """
        <dtml-var expr="_.min([1,2])">
        <dtml-var expr="_.max([2,3])">
        <dtml-var expr="_.sum([1,2,3,4])">
        <dtml-var expr="_.hasattr(1, 'foo') and 'Yes' or 'No'">
        <dtml-var expr="_.None">
        <dtml-var expr="_.string.strip(' testing ')">
        <dtml-var expr="[x for x in (1, 2, 3)]">
        """

        EXPECTED = ['1', '3', '10', 'No', 'None', 'testing', '[1, 2, 3]']

        #
        #   XXX:    these expressions seem like they should work, with
        #           the following ExPECTED, but they raise Unauthorized
        #           on the 'next' name.
        #
        #<dtml-var expr="_.iter([1,2,3]).next()">
        #<dtml-var expr="_.enumerate([1,2,3]).next()">
        #
        #EXPECTED = ['1', '3', '10', '1', '(0, 1)']

        template = self.doc_class(NEW_BUILTINS_TEMPLATE)
        res = template()
        lines = filter(None, [x.strip() for x in res.split('\n')])

        self.assertEqual(lines, EXPECTED)

    # Note: we need more tests!

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( SecurityTests ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
