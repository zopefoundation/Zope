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
"""Parrot directive and support classes
"""

from zope.configuration.fields import GlobalObject
from zope.interface import Interface
from zope.schema import TextLine


class IParrotDirective(Interface):
    """State that a class implements something.
    """
    class_ = GlobalObject(
        title="Class",
        required=True,
    )

    name = TextLine(
        title="Name",
        description="The parrots name.",
        required=True,
    )


def parrot(_context, class_, name):
    parrot = class_()
    parrot.pineForFjords()


class NorwegianBlue:

    def pineForFjords(self):
        return "This parrot is no more!"
