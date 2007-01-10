##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Machinery for making things traversable through adaptation

BBB 2006/05/01 -- to be removed after 12 months

$Id$
"""
import zope.deferredimport
zope.deferredimport.deprecated(
    "__bobo_traverse__ and ITraverser/ITraversable for controlling "
    "URL traversal have become obsolete. Use an IPublishTraverse "
    "adapter instead.  This reference will go away in Zope 2.12.",
    Traversable = "Products.Five.bbb:Traversable",
    FiveTraversable = "zope.traversing.adapters:DefaultTraversable",
    )
zope.deferredimport.deprecated(
    "Use zope.publisher.browser.TestRequest instead.",
    FakeRequest = "zope.publisher.browser:TestRequest",
    )
