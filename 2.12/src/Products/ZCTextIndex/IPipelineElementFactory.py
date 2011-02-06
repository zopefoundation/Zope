##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from zope.interface import Interface

class IPipelineElementFactory(Interface):
    """Class for creating pipeline elements by name"""

    def registerFactory(group, name, factory):
        """Registers a pipeline factory by name and element group.

        Each name can be registered only once for a given group. Duplicate
        registrations will raise a ValueError
        """

    def getFactoryGroups():
        """Returns a sorted list of element group names
        """

    def getFactoryNames(group):
        """Returns a sorted list of registered pipeline factory names
        in the specified element group
        """

    def instantiate(group, name):
        """Instantiates a pipeline element by group and name. If name is not
        registered raise a KeyError.
        """
