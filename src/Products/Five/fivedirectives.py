##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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
"""

from zope.interface import Interface
from zope.browserresource.metadirectives import IBasicResourceInformation
from zope.configuration.fields import GlobalObject, Tokens
from zope.schema import TextLine


# Deprecated, the class directive from zope.security allows the same
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


class ISizableDirective(Interface):
    """Attach sizable adapters to classes.
    """

    class_ = GlobalObject(
        title=u"Class",
        required=True
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


from zope.deferredimport import deprecated

deprecated("Please import from OFS.metadirectives",
    IRegisterPackageDirective = 'OFS.metadirectives:IRegisterPackageDirective',
    IRegisterClassDirective = 'OFS.metadirectives:IRegisterClassDirective',
    IDeprecatedManageAddDeleteDirective = \
        'OFS.metadirectives:IDeprecatedManageAddDeleteDirective',
)

deprecated("Please import from zope.configuration.xmlconfig",
    IInclude = 'zope.configuration.xmlconfig:IInclude',
)
