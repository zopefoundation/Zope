##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from Products.Five import BrowserView
import random

class Overview(BrowserView):
    def reversedIds(self):
        result = []
        for id in self.context.objectIds():
            l = list(id)
            l.reverse()
            reversed_id = ''.join(l)
            result.append(reversed_id)
        return result

    def directlyPublished(self):
        return "This is directly published"

class NewExample(BrowserView):
    def helpsWithOne(self):
        return random.randrange(10)
    
    def two(self):
        return "Two got called"
