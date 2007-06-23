##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Profiling support for ZTC

$Id$
"""

import os, sys
import interfaces

# Some distros ship without profile
try:
    from profile import Profile
    from pstats import Stats
except ImportError:
    def Profile(): pass

_profile = Profile()
_have_stats = 0

limit = ('.py:', 200)
sort = ('cumulative', 'time', 'pcalls')
strip_dirs = 1


def runcall(*args, **kw):
    if _profile is None:
        return apply(args[0], args[1:], kw)
    else:
        global _have_stats
        _have_stats = 1
        return apply(_profile.runcall, args, kw)


def print_stats(limit=limit, sort=sort, strip_dirs=strip_dirs):
    if _have_stats:
        stats = Stats(_profile)
        if strip_dirs:
            stats.strip_dirs()
        apply(stats.sort_stats, sort)
        apply(stats.print_stats, limit)


def dump_stats(filename):
    if _have_stats:
        _profile.dump_stats(filename)


class Profiled:
    '''Derive from this class and an xTestCase to get profiling support::

           class MyTest(Profiled, ZopeTestCase):
               ...

       Then run the test module by typing::

           $ python testSomething.py profile

       Profiler statistics will be printed after the test results.
    '''

    __implements__ = (interfaces.IProfiled,)

    def runcall(self, *args, **kw):
        return apply(runcall, args, kw)

    def __call__(self, result=None):
        if result is None: result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._TestCase__testMethodName)
        try:
            try:
                if int(os.environ.get('PROFILE_SETUP', 0)):
                    self.runcall(self.setUp)
                else:
                    self.setUp()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                return

            ok = 0
            try:
                if int(os.environ.get('PROFILE_TESTS', 0)):
                    self.runcall(testMethod)
                else:
                    testMethod()
                ok = 1
            except self.failureException:
                result.addFailure(self, self._TestCase__exc_info())
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())

            try:
                if int(os.environ.get('PROFILE_TEARDOWN', 0)):
                    self.runcall(self.tearDown)
                else:
                    self.tearDown()
            except KeyboardInterrupt:
                raise
            except:
                result.addError(self, self._TestCase__exc_info())
                ok = 0
            if ok: result.addSuccess(self)
        finally:
            result.stopTest(self)

