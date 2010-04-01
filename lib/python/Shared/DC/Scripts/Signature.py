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

__version__='$Revision: 1.6 $'[11:-2]

class FuncCode:

    def __init__(self, varnames, argcount):
        self.co_varnames=varnames
        self.co_argcount=argcount

    def __cmp__(self, other):
        if other is None: return 1
        try: return cmp((self.co_argcount, self.co_varnames),
                        (other.co_argcount, other.co_varnames))
        except: return 1

# This is meant to be imported directly into a class.

def _setFuncSignature(self, defaults=None, varnames=(), argcount=-1):
    # Simplify calls.
    if argcount < 0 and varnames:
        argcount = len(varnames)
    # Generate a change only if we have to.
    if self.func_defaults != defaults:
        self.func_defaults = defaults
    code = FuncCode(varnames, argcount)
    if self.func_code != code:
        self.func_code = code
