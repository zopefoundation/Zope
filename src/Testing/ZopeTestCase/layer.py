##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZopeLite layer
"""

_deferred_setup = []


class ZopeLite:
    '''The most base layer'''

    @classmethod
    def setUp(cls):
        '''Brings up the ZopeLite environment.'''
        for func, args, kw in _deferred_setup:
            func(*args, **kw)

    @classmethod
    def tearDown(cls):
        '''ZopeLite doesn't support tear down.

           We don't raise NotImplementedError to avoid
           triggering the testrunner's "resume layer"
           mechanism.

           See zope.testing.testrunner-layers-ntd.txt
        '''

ZopeLiteLayer = ZopeLite


def onsetup(func):
    '''Defers a function call to layer setup.
       Used as a decorator.
    '''
    def deferred_func(*args, **kw):
        _deferred_setup.append((func, args, kw))
    return deferred_func


def appcall(func):
    '''Defers a function call to layer setup.
       Used as a decorator.

       In addition, this decorator implements the appcall
       protocol:

       * The decorated function expects 'app' as first argument.

       * If 'app' is provided by the caller, the function is
         called immediately.

       * If 'app' is omitted or None, the 'app' argument is
         provided by the decorator, and the function call is
         deferred to ZopeLite layer setup.

       Also see utils.appcall.
    '''
    def appcalled_func(*args, **kw):
        if args and args[0] is not None:
            return func(*args, **kw)
        if kw.get('app') is not None:
            return func(*args, **kw)
        def caller(*args, **kw):
            import utils
            utils.appcall(func, *args, **kw)
        _deferred_setup.append((caller, args, kw))
    return appcalled_func

