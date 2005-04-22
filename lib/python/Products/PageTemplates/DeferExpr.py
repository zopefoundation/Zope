##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Defer and Lazy expression handler

defer expressions can be usesd for a design pattern called deferred evaluation.

Example:

    <div tal:define="xis defer:string:x is $x">
      <p tal:repeat="x python:range(3)"
         tal:content="xis"></p>
    </div>

Output:

    <div>
      <p>x is 0</p>
      <p>x is 1</p>
      <p>x is 2</p>
    </div>
    
A lazy expressions is implemented in a similar way but has a different result. While
a defer expression is evaluated every time it is used according to its context a lazy
expression is evaluted only the first time it is used. Lazy expression are known
under the name lazy initialization of variables, too. 
A common use case for a lazy expression is a lazy binding of a costly expression.
While one could call an expression only when it's required it makes sense to define
it only one time when it could be used multiple times.

Example

    <div tal:define="lazyvar lazy:here/suckMyCPU">
        <div tal:condition="foo" tal:content="lazyvar" />
        <div tal:condition="bar" tal:content="lazyvar" />
        <div tal:condition"python: not (foo or bar)">...</div>
    </div>
"""

_marker = object()

# defer expression

class DeferWrapper:
    """Wrapper for defer: expression
    """
    def __init__(self, expr, econtext):
        self._expr = expr
        self._econtext = econtext

    def __str__(self):
        return str(self())

    def __call__(self):
        return self._expr(self._econtext)

class DeferExpr:
    """defer: expression handler for deferred evaluation of the context
    """
    def __init__(self, name, expr, compiler):
        self._s = expr = expr.lstrip()
        self._c = compiler.compile(expr)

    def __call__(self, econtext):
        return DeferWrapper(self._c, econtext)

    def __repr__(self):
        return 'defer:%s' % `self._s`

# lazy expression

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

