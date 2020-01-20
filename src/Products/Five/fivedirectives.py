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

from zope.browserresource.metadirectives import IBasicResourceInformation
from zope.configuration.fields import GlobalObject
from zope.interface import Interface
from zope.schema import TextLine


class ISizableDirective(Interface):
    """Attach sizable adapters to classes.
    """

    class_ = GlobalObject(
        title="Class",
        required=True
    )


class IPagesFromDirectoryDirective(IBasicResourceInformation):
    """Register each file in a skin directory as a page resource
    """

    for_ = GlobalObject(
        title="The interface this view is for.",
        required=False
    )

    module = GlobalObject(
        title="Module",
        required=True
    )

    directory = TextLine(
        title="Directory",
        description="The directory containing the resource data.",
        required=True
    )
