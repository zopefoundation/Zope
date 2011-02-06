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
"""Lazy expression handler

A lazy expressions is implemented similarly to the defer expression
but has a different result. While a defer expression is evaluated
every time it is used according to its context a lazy expression is
evaluted only the first time it is used. Lazy expression are known
under the name lazy initialization of variables, too.  A common use
case for a lazy expression is a lazy binding of a costly expression.
While one could call an expression only when it's required it makes
sense to define it only one time when it could be used multiple times.

Example

    <div tal:define="lazyvar lazy:here/suckMyCPU">
        <div tal:condition="foo" tal:content="lazyvar" />
        <div tal:condition="bar" tal:content="lazyvar" />
        <div tal:condition"python: not (foo or bar)">...</div>
    </div>
"""
from zope.tales.expressions import DeferWrapper, DeferExpr
_marker = object()

# TODO These should really be integrated into the Zope 3 ZPT
# implementation (zope.tales)

class LazyWrapper(DeferWrapper):
    """Wrapper for lazy: expression
    """
    def __init__(self, expr, econtext):
        DeferWrapper.__init__(self, expr, econtext)
        self._result = _marker

    def __call__(self):
        r = self._result
        if r is _marker:
            self._result = r = self._expr(self._econtext)
        return r

class LazyExpr(DeferExpr):
    """lazy: expression handler for lazy initialization of expressions
    """
    def __call__(self, econtext):
        return LazyWrapper(self._c, econtext)

    def __repr__(self):
        return 'lazy:%s' % `self._s`
