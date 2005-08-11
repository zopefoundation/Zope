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
"""Test product interfaces

$Id: interfaces.py 12915 2005-05-31 10:23:19Z philikon $
"""
from zope.interface import Interface
from zope.schema import Text, TextLine, Object, Int, List

class IAdaptable(Interface):
    """This is a Zope 3 interface.
    """
    def method():
        """This method will be adapted
        """

class IAdapted(Interface):
    """The interface we adapt to.
    """

    def adaptedMethod():
        """A method to adapt.
        """

class IOrigin(Interface):
    """Something we'll adapt"""

class IDestination(Interface):
    """The result of an adaption"""

    def method():
        """Do something"""

class ISimpleContent(Interface):
    pass

class ICallableSimpleContent(ISimpleContent):
    pass

class IIndexSimpleContent(ISimpleContent):
    pass

class IFancyContent(Interface):
    pass

class IFieldSimpleContent(ISimpleContent):

    title = TextLine(
        title=u"Title",
        description=u"A short description of the event.",
        default=u"",
        required=True
        )

    description = Text(
        title=u"Description",
        description=u"A long description of the event.",
        default=u"",
        required=False
        )

    somenumber = Int(
        title=u"Some number",
        default=0,
        required=False
        )

    somelist = List(
        title=u"Some List",
        value_type=TextLine(title=u"Some item"),
        default=[],
        required=False
        )

class IComplexSchemaContent(Interface):
    
    fishtype = TextLine(
        title=u"Fish type",
        description=u"The type of fish",
        default=u"It was a lovely little fish. And it went wherever I did go.",
        required=False)

    fish = Object(
        title=u"Fish",
        schema=IFieldSimpleContent,
        description=u"The fishy object",
        required=True)
