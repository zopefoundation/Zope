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

# This allows ZPublisher to work with embedded interpreters
# that for some reason have no sys.argv (required by cgi.py).
import sys
if not hasattr(sys, 'argv'):
    sys.argv=[]

from zExceptions import NotFound, BadRequest, InternalError, Forbidden

from Publish import publish_module, Retry

def test(*args, **kw):
    global test
    import Test
    test=Test.publish
    return apply(test, args, kw)
