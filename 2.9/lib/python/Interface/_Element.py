##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""

Revision information:
$Id$
"""

from _object import object

class Element(object):

    # We can't say this yet because we don't have enough
    # infrastructure in place.
    #
    #__implements__ = IElement

    def __init__(self, __name__=None, __doc__=''):
        """Create an 'attribute' description
        """
        if not __doc__ and __name__ and __name__.find(' ') >= 0:
            __doc__ = __name__
            __name__ = None

        self.__name__=__name__
        self.__doc__=__doc__
        self.__tagged_values = {}

    def getName(self):
        """ Returns the name of the object. """
        return self.__name__

    def getDoc(self):
        """ Returns the documentation for the object. """
        return self.__doc__

    def getTaggedValue(self, tag):
        """ Returns the value associated with 'tag'. """
        return self.__tagged_values[tag]

    def getTaggedValueTags(self):
        """ Returns a list of all tags. """
        return self.__tagged_values.keys()

    def setTaggedValue(self, tag, value):
        """ Associates 'value' with 'key'. """
        self.__tagged_values[tag] = value
