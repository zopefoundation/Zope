##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Document Template Tests
"""

__rcs_id__='$Id: testSecurity.py,v 1.7 2001/10/18 20:22:33 shane Exp $'
__version__='$Revision: 1.7 $'[11:-2]

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
        try:
            html(myinst=myclass())
        except Unauthorized:
            # Passed the test.
            pass
        else:
            assert 0, 'Did not deny attribute access'

    def testSecurityInSyntax(self):
        '''
        Ensures syntax errors are thrown for an expr with restricted
        syntax.
        '''
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

    # Note: we need more tests!

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( SecurityTests ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
