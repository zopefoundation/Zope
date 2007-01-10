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
"""Demo schema content

$Id$
"""
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass

from zope.i18nmessageid import MessageFactory
from zope.interface import implements, Interface
from zope.schema import TextLine, Text, Object, Int, List
from zope.app.form import CustomWidgetFactory
from Products.Five.form.objectwidget import ObjectWidget

_ = MessageFactory('formtest')

class IFieldContent(Interface):

    title = TextLine(
        title=_(u"Title"),
        description=_(u"A short description of the event."),
        default=u"",
        required=True
        )

    description = Text(
        title=_(u"Description"),
        description=_(u"A long description of the event."),
        default=u"",
        required=False
        )

    somenumber = Int(
        title=_(u"Some number"),
        default=0,
        required=False
        )

    somelist = List(
        title=_(u"Some List"),
        value_type=TextLine(title=_(u"Some item")),
        default=[],
        required=False
        )

class FieldContent(SimpleItem):
    """A Viewable piece of content with fields"""
    implements(IFieldContent)
    meta_type = 'Five FieldContent'

    def __init__(self, id, title):
        self.id = id
        self.title = title

InitializeClass(FieldContent)

def manage_addFieldContent(self, id, title, REQUEST=None):
    """Add the field content"""
    id = self._setObject(id, FieldContent(id, title))
    return ''

class IComplexSchemaContent(Interface):

    fishtype = TextLine(
        title=u"Fish type",
        description=u"The type of fish",
        default=u"It was a lovely little fish. And it went wherever I did go.",
        required=False)

    fish = Object(
        title=u"Fish",
        schema=IFieldContent,
        description=u"The fishy object",
        required=True)

class ComplexSchemaContent(SimpleItem):
     implements(IComplexSchemaContent)
     meta_type ="Five ComplexSchemaContent"

     def __init__(self, id):
         self.id = id
         self.fish = FieldContent('fish', 'title')
         self.fish.description = ""
         self.fishtype = 'Lost fishy'

class ComplexSchemaView:
    """Needs a docstring"""

    fish_widget = CustomWidgetFactory(ObjectWidget, FieldContent)

InitializeClass(ComplexSchemaContent)

def manage_addComplexSchemaContent(self, id, REQUEST=None):
    """Add the complex schema content"""
    id = self._setObject(id, ComplexSchemaContent(id))
    return ''

def modifiedSubscriber(content, ev):
    """A simple event handler, which sets a flag on the object"""
    content._modified_flag = True

def createdSubscriber(content,ev):
    """A simple event handler, which sets a flag on the object"""
    content._created_flag = True
