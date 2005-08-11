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
"""Schema content implementation

$Id: schemacontent.py 12915 2005-05-31 10:23:19Z philikon $
"""
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass

from zope.interface import implements
from interfaces import IComplexSchemaContent
from simplecontent import FieldSimpleContent

class ComplexSchemaContent(SimpleItem):
     implements(IComplexSchemaContent)

     meta_type ="Complex Schema Content"

     def __init__(self, id):
         self.id = id
         self.fish = FieldSimpleContent('fish', 'title')
         self.fish.description = ""
         self.fishtype = 'Lost fishy'

InitializeClass(ComplexSchemaContent)

def manage_addComplexSchemaContent(self, id, REQUEST=None):
    """Add the fancy fancy content."""
    id = self._setObject(id, ComplexSchemaContent(id))
    return ''
