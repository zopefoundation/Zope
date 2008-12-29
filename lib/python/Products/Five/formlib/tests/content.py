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
"""Test content.

$Id$
"""
from App.class_init import InitializeClass
from OFS.SimpleItem import SimpleItem

from zope.i18nmessageid import MessageFactory
from zope.interface import implements
from zope.interface import Interface
from zope.schema import ASCIILine
from zope.schema import List
from zope.schema import TextLine

_ = MessageFactory('formtest')

class IContent(Interface):

    id = ASCIILine(
        title=_(u"Id"),
        description=_(u"The object id."),
        default='',
        required=True
        )

    title = TextLine(
        title=_(u"Title"),
        description=_(u"A short description of the event."),
        default=u"",
        required=True
        )

    somelist = List(
        title=_(u"Some List"),
        value_type=TextLine(title=_(u"Some item")),
        default=[],
        required=False
        )

class Content(SimpleItem):
    """A Viewable piece of content with fields
    """
    implements(IContent)

    meta_type = 'Five Formlib Test Content'

    def __init__(self, id, title, somelist=None):
        self.id = id
        self.title = title
        self.somelist = somelist

InitializeClass(Content)
