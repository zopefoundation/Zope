##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Z2 -> Z3 bridge utilities.

$Id: bridge.py 12915 2005-05-31 10:23:19Z philikon $
"""
from Interface._InterfaceClass import Interface as Z2_InterfaceClass
from Interface import Interface as Z2_Interface
from Interface import Attribute as Z2_Attribute
from Interface.Method import Method as Z2_Method

from zope.interface.interface import InterfaceClass as Z3_InterfaceClass
from zope.interface.interface import Interface as Z3_Interface
from zope.interface.interface import Attribute as Z3_Attribute
from zope.interface.interface import Method as Z3_Method

_bridges = {Z2_Interface: Z3_Interface}

def fromZ2Interface(z2i):
    """ Return a Zope 3 interface corresponding to 'z2i'.

    o 'z2i' must be a Zope 2 interface.
    """
    if not isinstance(z2i, Z2_InterfaceClass):
        raise ValueError, 'Not a Zope 2 interface!'

    if z2i in _bridges:
        return _bridges[z2i]

    name = z2i.getName()

    bases = [ fromZ2Interface(x) for x in z2i.getBases() ]

    attrs = {}

    for k, v in z2i.namesAndDescriptions():
        if isinstance(v, Z2_Method):
            v = fromZ2Method(v)

        elif isinstance(v, Z2_Attribute):
            v = fromZ2Attribute(v)

        attrs[k] = v

    # XXX: Note that we pass the original interface's __module__;
    #      we may live to regret that.
    z3i = Z3_InterfaceClass(name=name,
                            bases=tuple(bases),
                            attrs=attrs,
                            __doc__=z2i.getDoc(),
                            __module__=z2i.__module__)
    _bridges[z2i] = z3i
    return z3i

def fromZ2Attribute(z2a):
    """ Return a Zope 3 interface attribute corresponding to 'z2a'.

    o 'z2a' must be a Zope 2 interface attribute.
    """
    if not isinstance(z2a, Z2_Attribute):
        raise ValueError, 'Not a Zope 2 interface attribute!'

    return Z3_Attribute(z2a.getName(), z2a.getDoc())

def fromZ2Method(z2m):
    """ Return a Zope 3 interface method corresponding to 'z2m'.

    o 'z2m' must be a Zope 2 interface method.
    """
    if not isinstance(z2m, Z2_Method):
        raise ValueError, 'Not a Zope 2 interface method!'

    z3m = Z3_Method(z2m.getName(), z2m.getDoc())
    sig = z2m.getSignatureInfo()
    z3m.positional = sig['positional']
    z3m.required = sig['required']
    z3m.optional = sig['optional']
    z3m.varargs = sig['varargs']
    z3m.kwargs = sig['kwargs']
    return z3m
