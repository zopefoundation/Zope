##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import transaction
from zope.deferredimport import deprecated


# BBB Zope 5.0
deprecated(
    'Please import from ZServer.Testing.utils.',
    importObjectFromFile='ZServer.Testing.utils:importObjectFromFile',
    setupCoreSessions='ZServer.Testing.utils:setupCoreSessions',
    setupSiteErrorLog='ZServer.Testing.utils:setupSiteErrorLog',
    startZServer='ZServer.Testing.utils:startZServer',
)

deprecated(
    'Please import from Testing.makerequest.',
    makerequest='Testing.makerequest:makerequest',
)


def appcall(func, *args, **kw):
    '''Calls a function passing 'app' as first argument.'''
    from .base import app, close
    app = app()
    args = (app,) + args
    try:
        return func(*args, **kw)
    finally:
        transaction.abort()
        close(app)


def makelist(arg):
    '''Turns arg into a list. Where arg may be
       list, tuple, or string.
    '''
    if isinstance(arg, list):
        return arg
    if isinstance(arg, tuple):
        return list(arg)
    if isinstance(arg, str):
        return [a for a in [arg] if a]
    raise ValueError('Argument must be list, tuple, or string')
