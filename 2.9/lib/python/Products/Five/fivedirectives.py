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

$Id: fivedirectives.py 12884 2005-05-30 13:10:41Z philikon $
"""
from zope.interface import Interface
from zope.app.publisher.browser.metadirectives import IBasicResourceInformation
from zope.app.security.fields import Permission
from zope.configuration.fields import GlobalObject, Tokens, PythonIdentifier
from zope.configuration.fields import Bool
from zope.schema import ASCII
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

class ISizableDirective(Interface):
    """Make instances of class send events.
    """

    class_ = GlobalObject(
        title=u"Class",
        required=True
        )

class IContainerEventsDirective(Interface):
    """Global switch to enable container events
    """

class IDeprecatedManageAddDeleteDirective(Interface):
    """Call manage_afterAdd & co for these contained content classes.
    """
    class_ = GlobalObject(
        title=u"Class",
        required=True,
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

class IRegisterClassDirective(Interface):

    """registerClass directive schema.

    Register Five content with Zope 2.
    """

    class_ = GlobalObject(
        title=u'Instance Class',
        description=u'Dotted name of the class that is registered.',
        required=True
        )

    meta_type = ASCII(
        title=u'Meta Type',
        description=u'A human readable unique identifier for the class.',
        required=True
        )

    permission = Permission(
        title=u'Add Permission',
        description=u'The permission for adding objects of this class.',
        required=True
        )

    addview = ASCII(
        title=u'Add View ID',
        description=u'The ID of the add view used in the ZMI. Consider this '
                    u'required unless you know exactly what you do.',
        default=None,
        required=False
        )

    icon = ASCII(
        title=u'Icon ID',
        description=u'The ID of the icon used in the ZMI.',
        default=None,
        required=False
        )

    global_ = Bool(
        title=u'Global scope?',
        description=u'If "global" is False the class is only available in '
                    u'containers that explicitly allow one of its interfaces.',
        default=True,
        required=False
        )
