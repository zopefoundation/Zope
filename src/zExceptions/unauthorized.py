##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
$Id$
"""

from zope.interface import implements
from zope.security.interfaces import IUnauthorized


class Unauthorized(Exception):
    """Some user wasn't allowed to access a resource
    """
    implements(IUnauthorized)

    def _get_message(self):
        return self._message

    message = property(_get_message,)

    def __init__(self, message=None, value=None, needed=None, name=None, **kw):
        """Possible signatures:

        Unauthorized()
        Unauthorized(message) # Note that message includes a space
        Unauthorized(name)
        Unauthorized(name, value)
        Unauthorized(name, value, needed)
        Unauthorized(message, value, needed, name)

        Where needed is a mapping objects with items representing requirements
        (e.g. {'permission': 'add spam'}). Any extra keyword arguments
        provides are added to needed.
        """
        if name is None and (
            not isinstance(message, basestring) or len(message.split()) <= 1):
            # First arg is a name, not a message
            name=message
            message=None

        self.name=name
        self._message=message
        self.value=value

        if kw:
            if needed: needed.update(kw)
            else: needed=kw

        self.needed=needed

    def __str__(self):
        if self.message is not None:
            return self.message
        if self.name is not None:
            return ("You are not allowed to access '%s' in this context"
                    % self.name)
        elif self.value is not None:
            return ("You are not allowed to access '%s' in this context"
                    % self.getValueName())
        return repr(self)

    def __unicode__(self):
        result = self.__str__()
        if isinstance(result, unicode):
            return result
        return unicode(result, 'ascii') # override sys.getdefaultencoding()

    def getValueName(self):
        v=self.value
        vname=getattr(v, '__name__', None)
        if vname: return vname
        c = getattr(v, '__class__', type(v))
        c = getattr(c, '__name__', 'object')
        return "a particular %s" % c
