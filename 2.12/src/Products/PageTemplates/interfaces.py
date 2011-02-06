##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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

class IUnicodeEncodingConflictResolver(Interface):
    """ A utility that tries to convert a non-unicode string into
       a Python unicode by implementing some policy in order
       to figure out a possible encoding - either through the
       calling context, the location or the system environment
    """

    def resolve(context, text, expression):
        """ Returns 'text' as unicode string. 
            'context' is the current context object.
            'expression' is the original expression (can be used for 
            logging purposes)
        """


