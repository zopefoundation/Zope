##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from unittest import TestCase, TestSuite, main, makeSuite
from Products.ZCTextIndex.IPipelineElement import IPipelineElement
from Products.ZCTextIndex.PipelineFactory import PipelineElementFactory
from zope.interface import implements

class NullPipelineElement:

    implements(IPipelineElement)

    def process(source):
        pass

class PipelineFactoryTest(TestCase):

    def setUp(self):
        self.huey = NullPipelineElement()
        self.dooey = NullPipelineElement()
        self.louie = NullPipelineElement()
        self.daffy = NullPipelineElement()

    def testPipeline(self):
        pf = PipelineElementFactory()
        pf.registerFactory('donald', 'huey', self.huey)
        pf.registerFactory('donald', 'dooey',  self.dooey)
        pf.registerFactory('donald', 'louie', self.louie)
        pf.registerFactory('looney', 'daffy', self.daffy)
        self.assertRaises(ValueError, pf.registerFactory,'donald',  'huey',
                          self.huey)
        self.assertEqual(pf.getFactoryGroups(), ['donald', 'looney'])
        self.assertEqual(pf.getFactoryNames('donald'),
                         ['dooey', 'huey', 'louie'])

def test_suite():
    return makeSuite(PipelineFactoryTest)

if __name__=='__main__':
    main(defaultTest='test_suite')
