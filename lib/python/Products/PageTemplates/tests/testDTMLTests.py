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

import os, sys, unittest

from Products.PageTemplates.tests import util
from Products.PageTemplates.PageTemplate import PageTemplate
from Acquisition import Implicit
from AccessControl import SecurityManager

class AqPageTemplate(Implicit, PageTemplate):
   pass

class UnitTestSecurityPolicy:
    """
        Stub out the existing security policy for unit testing purposes.
    """
    #
    #   Standard SecurityPolicy interface
    #
    def validate( self
                , accessed=None
                , container=None
                , name=None
                , value=None
                , context=None
                , roles=None
                , *args
                , **kw):
        return 1
    
    def checkPermission( self, permission, object, context) :
        return 1

class DTMLTests(unittest.TestCase):

   def setUp(self):
      self.t=(AqPageTemplate())
      self.policy = UnitTestSecurityPolicy()
      self.oldPolicy = SecurityManager.setSecurityPolicy( self.policy )

   def tearDown(self):
      SecurityManager.setSecurityPolicy( self.oldPolicy )

   def check1(self):
      """DTML test 1: if, in, and var:

      %(comment)[ blah %(comment)]
      <html><head><title>Test of documentation templates</title></head>
      <body>
      %(if args)[
      <dl><dt>The arguments to this test program were:<p>
      <dd>
      <ul>
      %(in args)[
        <li>Argument number %(num)d was %(arg)s
      %(in args)]
      </ul></dl><p>
      %(if args)]
      %(else args)[
      No arguments were given.<p>
      %(else args)]
      And thats da trooth.
      </body></html>
      """

      tal = util.read_input('DTML1.html')
      self.t.write(tal)

      aa=util.argv(('one', 'two', 'three', 'cha', 'cha', 'cha'))
      o=self.t.__of__(aa)()
      expect = util.read_output('DTML1a.html')

      util.check_xml(expect, o)

      aa=util.argv(())
      o=self.t.__of__(aa)()
      expect = util.read_output('DTML1b.html')
      util.check_xml(expect, o)

   def check3(self):
      """DTML test 3: batches and formatting:

        <html><head><title>Test of documentation templates</title></head>
        <body>
        <!--#if args-->
          The arguments were:
          <!--#in args size=size end=end-->
              <!--#if previous-sequence-->
                 (<!--#var previous-sequence-start-arg-->-
                  <!--#var previous-sequence-end-arg-->)
              <!--#/if previous-sequence-->
              <!--#if sequence-start-->
                 <dl>
              <!--#/if sequence-start-->
              <dt><!--#var sequence-arg-->.</dt>
              <dd>Argument <!--#var num fmt=d--> was <!--#var arg--></dd>
              <!--#if next-sequence-->
                 (<!--#var next-sequence-start-arg-->-
                  <!--#var next-sequence-end-arg-->)
              <!--#/if next-sequence-->
          <!--#/in args-->
          </dl>
        <!--#else args-->
          No arguments were given.<p>
        <!--#/if args-->
        And I\'m 100% sure!
        </body></html>
      """

      tal = util.read_input('DTML3.html')
      self.t.write(tal)

      aa=util.argv(('one', 'two', 'three', 'four', 'five',
                    'six', 'seven', 'eight', 'nine', 'ten',
                    'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
                    'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
                    ))
      from Products.PageTemplates.tests import batch        
      o=self.t.__of__(aa)(batch=batch.batch(aa.args, 5))

      expect = util.read_output('DTML3.html')
      util.check_xml(expect, o)

def test_suite():
   return unittest.makeSuite(DTMLTests, 'check')

if __name__=='__main__':
   main()

