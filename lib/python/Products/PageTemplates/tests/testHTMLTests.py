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
from Products.PageTemplates.GlobalTranslationService import \
     setGlobalTranslationService
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import noSecurityManager

from Acquisition import Implicit
class AqPageTemplate(Implicit, PageTemplate):
    pass

class Folder(util.Base):
    pass

class TestTranslationService:
    def translate(self, domain, msgid, mapping=None, *args, **kw):
        maps = []
        if mapping is not None:
            # Get a deterministic, sorted representation of dicts.
            for k, v in mapping.items():
                maps.append('%s:%s' % (`k`, `v`))
            maps.sort()
        return "[%s](%s/{%s})" % (domain, msgid, ','.join(maps))


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
        noSecurityManager()  # Use the new policy.

    def tearDown(self):
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        noSecurityManager()  # Reset to old policy.

    def assert_expected(self, t, fname, *args, **kwargs):
        t.write(util.read_input(fname))
        assert not t._v_errors, 'Template errors: %s' % t._v_errors
        expect = util.read_output(fname)
        out = t(*args, **kwargs)
        util.check_html(expect, out)

    def assert_expected_unicode(self, t, fname, *args, **kwargs):
        t.write(util.read_input(fname))
        assert not t._v_errors, 'Template errors: %s' % t._v_errors
        expect = util.read_output(fname)
        expect = unicode(expect, 'utf8')
        out = t(*args, **kwargs)
        util.check_html(expect, out)

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
        self.assert_expected(self.folder.laf, 'TeeShopLAF.html')

    def check2(self):
        self.folder.laf.write(util.read_input('TeeShopLAF.html'))

        self.assert_expected(self.folder.t, 'TeeShop2.html',
                             getProducts=self.getProducts)

    def check3(self):
        self.folder.laf.write(util.read_input('TeeShopLAF.html'))

        self.assert_expected(self.folder.t, 'TeeShop1.html',
                             getProducts=self.getProducts)

    def checkSimpleLoop(self):
        self.assert_expected(self.folder.t, 'Loop1.html')

    def checkFancyLoop(self):
        self.assert_expected(self.folder.t, 'Loop2.html')

    def checkGlobalsShadowLocals(self):
        self.assert_expected(self.folder.t, 'GlobalsShadowLocals.html')

    def checkStringExpressions(self):
        self.assert_expected(self.folder.t, 'StringExpression.html')

    def checkReplaceWithNothing(self):
        self.assert_expected(self.folder.t, 'CheckNothing.html')

    def checkWithXMLHeader(self):
        self.assert_expected(self.folder.t, 'CheckWithXMLHeader.html')

    def checkNotExpression(self):
        self.assert_expected(self.folder.t, 'CheckNotExpression.html')

    def checkPathNothing(self):
        self.assert_expected(self.folder.t, 'CheckPathNothing.html')

    def checkPathAlt(self):
        self.assert_expected(self.folder.t, 'CheckPathAlt.html')

    def checkBatchIteration(self):
        self.assert_expected(self.folder.t, 'CheckBatchIteration.html')

    def checkUnicodeInserts(self):
        self.assert_expected_unicode(self.folder.t, 'CheckUnicodeInserts.html')

    def checkI18nTranslate(self):
        self.assert_expected(self.folder.t, 'CheckI18nTranslate.html')

    def checkI18nTranslateHooked(self):
        old_ts = setGlobalTranslationService(TestTranslationService())
        self.assert_expected(self.folder.t, 'CheckI18nTranslateHooked.html')
        setGlobalTranslationService(old_ts)

def test_suite():
    return unittest.makeSuite(HTMLTests, 'check')

if __name__=='__main__':
   main()

