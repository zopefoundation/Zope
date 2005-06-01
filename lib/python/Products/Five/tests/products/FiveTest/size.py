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
"""Size adapters

$Id: size.py 12915 2005-05-31 10:23:19Z philikon $
"""
from zope.interface import implements
from zope.app.size.interfaces import ISized

class SimpleContentSize(object):
    """Size for ``SimpleContent`` objects."""
    implements(ISized)

    def __init__(self, context):
	self.context = context

    def sizeForSorting(self):
	return ('byte', 42)

    def sizeForDisplay(self):
	return "What is the meaning of life?"

class FancyContentSize(object):
    """Size for ``SimpleContent`` objects."""
    implements(ISized)

    def __init__(self, context):
	self.context = context

    def sizeForSorting(self):
	return ('line', 143)

    def sizeForDisplay(self):
	return "That's not the meaning of life!"
