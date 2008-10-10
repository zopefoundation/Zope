##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""General exceptions that wish they were standard exceptions

These exceptions are so general purpose that they don't belong in Zope
application-specific packages.

$Id$
"""

import warnings

from zope.interface import implements
from zope.interface.common.interfaces import IException
from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IForbidden
from zExceptions.unauthorized import Unauthorized

class BadRequest(Exception):
    implements(IException)

class InternalError(Exception):
    implements(IException)

class NotFound(Exception):
    implements(INotFound)

class Forbidden(Exception):
    implements(IForbidden)

class MethodNotAllowed(Exception):
    pass

class Redirect(Exception):
    pass

def upgradeException(t, v):
    # If a string exception is found, convert it to an equivalent
    # exception defined either in builtins or zExceptions. If none of
    # that works, tehn convert it to an InternalError and keep the
    # original exception name as part of the exception value.
    import zExceptions

    if not isinstance(t, basestring):
        return t, v

    warnings.warn('String exceptions are deprecated starting '
                  'with Python 2.5 and will be removed in a '
                  'future release', DeprecationWarning)

    n = None
    if __builtins__.has_key(t):
        n = __builtins__[t]
    elif hasattr(zExceptions, t):
        n = getattr(zExceptions, t)
    if n is not None and issubclass(n, Exception):
        t = n
    else:
        v = t, v
        t = InternalError
    return t, v
