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
"""Defer expression handler
"""

_marker = []

class DeferWrapper:
    def __init__(self, expr, econtext):
        self._expr = expr
        self._econtext = econtext
        self._result = _marker

    def __str__(self):
        return str(self())

    def __call__(self):
        r = self._result
        if r is _marker:
            r = self._expr(self._econtext)
        return r

class DeferExpr:
    def __init__(self, name, expr, compiler):
        self._s = expr = expr.lstrip()
        self._c = compiler.compile(expr)

    def __call__(self, econtext):
        return DeferWrapper(self._c, econtext)

    def __repr__(self):
        return 'defer:%s' % `self._s`
