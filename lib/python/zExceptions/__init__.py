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

from unauthorized import Unauthorized

class BadRequest(Exception):
    pass

class InternalError(Exception):
    pass

class NotFound(Exception):
    pass

class Forbidden(Exception):
    pass

class MethodNotAllowed(Exception):
    pass

class Redirect(Exception):
    pass
