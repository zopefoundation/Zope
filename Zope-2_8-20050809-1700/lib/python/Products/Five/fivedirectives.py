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
"""Five ZCML directive schemas

$Id: fivedirectives.py 12915 2005-05-31 10:23:19Z philikon $
"""
from zope.interface import Interface
from zope.app.publisher.browser.metadirectives import IBasicResourceInformation
from zope.configuration.fields import GlobalObject, Tokens, PythonIdentifier
from zope.schema import TextLine

class IImplementsDirective(Interface):
    """State that a class implements something.
    """
    class_ = GlobalObject(
        title=u"Class",
        required=True
        )

    interface = Tokens(
        title=u"One or more interfaces",
        required=True,
        value_type=GlobalObject()
        )

class ITraversableDirective(Interface):
    """Make instances of class traversable publically.

    This can be used to browse to pages, resources, etc.

    Traversal can be controlled by registering an ITraverser adapter.
    """
    class_ = GlobalObject(
        title=u"Class",
        required=True
        )

class IDefaultViewableDirective(Interface):
    """Make instances of class viewable publically.

    The default view is looked up using a IBrowserDefault adapter.
    """
    class_ = GlobalObject(
        title=u"Class",
        required=True
        )

class ISendEventsDirective(Interface):
    """Make instances of class send events.
    """

    class_ = GlobalObject(
        title=u"Class",
        required=True
        )

class IBridgeDirective(Interface):
    """Bridge from a Zope 2 interface to an equivalent Zope3 interface.
    """
    zope2 = GlobalObject(
        title=u"Zope2",
        required=True
        )

    package = GlobalObject(
        title=u"Target package",
        required=True
        )

    name = PythonIdentifier(
        title=u"Zope3 Interface name",
        description=u"If not supplied, the new interface will have the same "
                    u"name as the source interface.",
        required=False
        )

class IPagesFromDirectoryDirective(IBasicResourceInformation):
    """Register each file in a skin directory as a page resource
    """

    for_ = GlobalObject(
        title=u"The interface this view is for.",
        required=False
        )

    module = GlobalObject(
        title=u"Module",
        required=True
        )

    directory = TextLine(
        title=u"Directory",
        description=u"The directory containing the resource data.",
        required=True
        )
