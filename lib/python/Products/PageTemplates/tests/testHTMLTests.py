##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

import os, sys, unittest

from Products.PageTemplates.tests import util
from Products.PageTemplates.PageTemplate import PageTemplate
from AccessControl import SecurityManager

from Acquisition import Implicit
class AqPageTemplate(Implicit, PageTemplate):
   pass

class Folder(util.Base):
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

class HTMLTests(unittest.TestCase):

   def setUp(self):
      self.folder = f = Folder()
      f.laf = AqPageTemplate()
      f.t = AqPageTemplate()
      self.policy = UnitTestSecurityPolicy()
      self.oldPolicy = SecurityManager.setSecurityPolicy( self.policy )

   def tearDown(self):
      SecurityManager.setSecurityPolicy( self.oldPolicy )

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

