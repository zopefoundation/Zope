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
"""Signature module

This provides support for simulating function signatures
"""

from functools import total_ordering


@total_ordering
class FuncCode:

    def __init__(self, varnames=(), argcount=-1):
        # The default values are needed for unpickling instances of this class
        # which where created before 4.0b2 where this class was still an old
        # style class. For details see
        # https://github.com/zopefoundation/Zope/issues/205
        self.co_varnames = varnames
        self.co_argcount = argcount

    def __eq__(self, other):
        if not isinstance(other, FuncCode):
            return False
        return ((self.co_argcount, self.co_varnames) ==  # NOQA: W504
                (other.co_argcount, other.co_varnames))

    def __lt__(self, other):
        if not isinstance(other, FuncCode):
            return False
        return ((self.co_argcount, self.co_varnames) <  # NOQA: W504
                (other.co_argcount, other.co_varnames))


def _setFuncSignature(self, defaults=None, varnames=(), argcount=-1):
    # This is meant to be imported directly into a class.
    # Simplify calls.
    if argcount < 0 and varnames:
        argcount = len(varnames)
    # Generate a change only if we have to.
    if self.__defaults__ != defaults:
        self.__defaults__ = defaults
    code = FuncCode(varnames, argcount)
    if self.__code__ != code:
        self.__code__ = code
