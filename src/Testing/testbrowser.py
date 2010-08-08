##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""Support for using zope.testbrowser from Zope2.

Mostly just copy and paste from zope.testbrowser.testing.
"""

# Forward compatibility with Zope 2.13
from Products.Five.testbrowser import Browser
from Products.Five.testbrowser import PublisherConnection
from Products.Five.testbrowser import PublisherHTTPHandler
from Products.Five.testbrowser import PublisherMechanizeBrowser
