##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from unittest import TestCase, TestSuite, main, makeSuite
from Products.ZCTextIndex.IPipelineElement import IPipelineElement
from Products.ZCTextIndex.PipelineFactory import PipelineElementFactory

class NullPipelineElement:
    
    __implements__ = IPipelineElement
    
    def process(source):
        pass    

class PipelineFactoryTest(TestCase):
    
    def setUp(self):
        self.huey = NullPipelineElement()
        self.dooey = NullPipelineElement()
        self.louie = NullPipelineElement()
        
    def testPipeline(self):
        pf = PipelineElementFactory()
        pf.registerFactory('huey', self.huey)
        pf.registerFactory('dooey', self.dooey)
        pf.registerFactory('louie', self.louie)
        self.assertRaises(ValueError, pf.registerFactory, 'huey', self.huey)
        self.assertEqual(pf.getFactoryNames(), ['dooey', 'huey', 'louie'])
    
def test_suite():
    return makeSuite(PipelineFactoryTest)

if __name__=='__main__':
    main(defaultTest='test_suite')
