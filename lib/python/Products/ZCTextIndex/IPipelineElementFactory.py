##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from Interface import Base as Interface

class IPipelineElementFactory(Interface):
    """Class for creating pipeline elements by name"""

    def registerFactory(name, factory):
        """Registers a pipeline factory by name.
        
        Each name can be registered only once. Duplicate registrations
        will raise a ValueError
        """
        
    def getFactoryNames():
        """Returns a sorted list of registered pipeline factory names
        """
        
    def instantiate(name):
        """Instantiates a pipeline element by name. If name is not registered
        raise a KeyError.
        """
