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


def appcall(func, *args, **kw):
    '''Calls a function passing 'app' as first argument.'''
    from .base import app
    from .base import close
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
