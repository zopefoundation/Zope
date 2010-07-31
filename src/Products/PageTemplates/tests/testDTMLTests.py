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

import zope.component.testing
from zope.component import provideUtility
from zope.traversing.adapters import DefaultTraversable
from Products.PageTemplates.tests import util
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.interfaces import IUnicodeEncodingConflictResolver
from Products.PageTemplates.unicodeconflictresolver import DefaultUnicodeEncodingConflictResolver
from Acquisition import Implicit
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import noSecurityManager

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

class DTMLTests(zope.component.testing.PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(DTMLTests, self).setUp()
        zope.component.provideAdapter(DefaultTraversable, (None,))
        provideUtility(DefaultUnicodeEncodingConflictResolver, IUnicodeEncodingConflictResolver)

        self.t = AqPageTemplate()
        self.policy = UnitTestSecurityPolicy()
        self.oldPolicy = SecurityManager.setSecurityPolicy(self.policy)
        noSecurityManager()  # Use the new policy.

    def tearDown(self):
        super(DTMLTests, self).tearDown()
        SecurityManager.setSecurityPolicy(self.oldPolicy)
        noSecurityManager()  # Reset to old policy.

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

    def check_on_error_in_slot_filler(self):
        # The `here` isn't defined, so the macro definition is
        # expected to catch the error that gets raised.
        text = '''\
            <div metal:define-macro="foo">
               <div tal:on-error="string:eek">
                  <div metal:define-slot="slot" />
                  cool
               </div>
            </div>

            <div metal:use-macro="template/macros/foo">
               <div metal:fill-slot="slot">
                  <p tal:content="here/xxx" />
               </div>
            </div>
            '''
        self.t.write(text)
        aa = util.argv(('one', 'two', 'three', 'four', 'five'))
        self.t.__of__(aa)()

    def check_on_error_in_slot_default(self):
        # The `here` isn't defined, so the macro definition is
        # expected to catch the error that gets raised.
        text = '''\
            <div metal:define-macro="foo">
               <div tal:on-error="string:eek">
                  <div metal:define-slot="slot">
                    <div tal:content="here/xxx" />
                  </div>
               </div>
            </div>

            <div metal:use-macro="template/macros/foo">
            </div>
            '''
        self.t.write(text)
        aa = util.argv(('one', 'two', 'three', 'four', 'five'))
        self.t.__of__(aa)()


def test_suite():
    return unittest.makeSuite(DTMLTests, 'check')
