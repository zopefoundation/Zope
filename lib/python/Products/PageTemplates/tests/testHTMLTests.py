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
class AqPageTemplate(Implicit, PageTemplate):
   pass

class Folder(util.Base):
   pass

class HTMLTests(unittest.TestCase):

   def setUp(self):
      self.folder = f = Folder()
      f.laf = AqPageTemplate()
      f.t = AqPageTemplate()

   def getProducts(self):
      return [
         {'description': 'This is the tee for those who LOVE Zope. '
          'Show your heart on your tee.',
          'price': 12.99, 'image': 'smlatee.jpg'
          },
         {'description': 'This is the tee for Jim Fulton. '
          'He\'s the Zope Pope!',
          'price': 11.99, 'image': 'smpztee.jpg'
          },
         ]

   def check1(self):
      laf = self.folder.laf
      laf.write(util.read_input('TeeShopLAF.html'))
      expect = util.read_output('TeeShopLAF.html')
      util.check_html(expect, laf())

   def check2(self):
      self.folder.laf.write(util.read_input('TeeShopLAF.html'))

      t = self.folder.t
      t.write(util.read_input('TeeShop2.html'))
      expect = util.read_output('TeeShop2.html')
      out = t(getProducts=self.getProducts)
      util.check_html(expect, out)
      

   def check3(self):
      self.folder.laf.write(util.read_input('TeeShopLAF.html'))

      t = self.folder.t
      t.write(util.read_input('TeeShop1.html'))
      expect = util.read_output('TeeShop1.html')
      out = t(getProducts=self.getProducts)
      util.check_html(expect, out)

   def checkSimpleLoop(self):
      t = self.folder.t
      t.write(util.read_input('Loop1.html'))
      expect = util.read_output('Loop1.html')
      out = t()
      util.check_html(expect, out)

   def checkGlobalsShadowLocals(self):
      t = self.folder.t
      t.write(util.read_input('GlobalsShadowLocals.html'))
      expect = util.read_output('GlobalsShadowLocals.html')
      out = t()
      util.check_html(expect, out)

   def checkStringExpressions(self):
      t = self.folder.t
      t.write(util.read_input('StringExpression.html'))
      expect = util.read_output('StringExpression.html')
      out = t()
      util.check_html(expect, out)
      
   def checkReplaceWithNothing(self):
      t = self.folder.t
      t.write(util.read_input('CheckNothing.html'))
      expect = util.read_output('CheckNothing.html')
      out = t()
      util.check_html(expect, out)

   def checkWithXMLHeader(self):
      t = self.folder.t
      t.write(util.read_input('CheckWithXMLHeader.html'))
      expect = util.read_output('CheckWithXMLHeader.html')
      out = t()
      util.check_html(expect, out)

   def checkNotExpression(self):
      t = self.folder.t
      t.write(util.read_input('CheckNotExpression.html'))
      expect = util.read_output('CheckNotExpression.html')
      out = t()
      util.check_html(expect, out)
      
   def checkPathNothing(self):
      t = self.folder.t
      t.write(util.read_input('CheckPathNothing.html'))
      expect = util.read_output('CheckPathNothing.html')
      out = t()
      util.check_html(expect, out)
      
   def checkPathAlt(self):
      t = self.folder.t
      t.write(util.read_input('CheckPathAlt.html'))
      expect = util.read_output('CheckPathAlt.html')
      out = t()
      util.check_html(expect, out)


def test_suite():
   return unittest.makeSuite(HTMLTests, 'check')

if __name__=='__main__':
   main()

