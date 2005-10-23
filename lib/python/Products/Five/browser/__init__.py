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
"""Provide basic browser functionality

$Id: __init__.py 18841 2005-10-23 09:57:38Z philikon $
"""
import Acquisition
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

class BrowserView(Acquisition.Explicit):
    security = ClassSecurityInfo()

    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    # XXX do not create any methods on the subclass called index_html,
    # as this makes Zope 2 traverse into that first!

InitializeClass(BrowserView)
