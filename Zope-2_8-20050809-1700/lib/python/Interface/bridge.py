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
""" Z3 -> Z2 bridge utilities.

$Id$
"""
from Interface._InterfaceClass import Interface as Z2_InterfaceClass
from Interface import Interface as Z2_Interface
from Interface import Attribute as Z2_Attribute
from Interface.Method import Method as Z2_Method

from zope.interface.interface import InterfaceClass as Z3_InterfaceClass
from zope.interface.interface import Interface as Z3_Interface
from zope.interface.interface import Attribute as Z3_Attribute
from zope.interface.interface import Method as Z3_Method

_bridges = {Z3_Interface: Z2_Interface}

def fromZ3Interface(z3i):
    """ Return a Zope 2 interface corresponding to 'z3i'.

    o 'z3i' must be a Zope 3 interface.
    """
    if not isinstance(z3i, Z3_InterfaceClass):
        raise ValueError, 'Not a Zope 3 interface!'

    if z3i in _bridges:
        return _bridges[z3i]

    name = z3i.getName()
    bases = [ fromZ3Interface(x) for x in z3i.getBases() ]
    attrs = {}

    for k, v in z3i.namesAndDescriptions():
        if isinstance(v, Z3_Method):
            v = fromZ3Method(v)

        elif isinstance(v, Z3_Attribute):
            v = fromZ3Attribute(v)

        attrs[k] = v

    # XXX: Note that we pass the original interface's __module__;
    #      we may live to regret that.
    z2i = Z2_InterfaceClass(name=name,
                            bases=tuple(bases),
                            attrs=attrs,
                            __doc__=z3i.getDoc(),
                            __module__=z3i.__module__)
    _bridges[z3i] = z2i
    return z2i

def fromZ3Attribute(z3a):
    """ Return a Zope 2 interface attribute corresponding to 'z3a'.

    o 'z3a' must be a Zope 3 interface attribute.
    """
    if not isinstance(z3a, Z3_Attribute):
        raise ValueError, 'Not a Zope 3 interface attribute!'

    return Z2_Attribute(z3a.getName(), z3a.getDoc())

def fromZ3Method(z3m):
    """ Return a Zope 2 interface method corresponding to 'z3m'.

    o 'z3m' must be a Zope 3 interface method.
    """
    if not isinstance(z3m, Z3_Method):
        raise ValueError, 'Not a Zope 3 interface method!'

    z2m = Z2_Method(z3m.getName(), z3m.getDoc())
    sig = z3m.getSignatureInfo()
    z2m.positional = sig['positional']
    z2m.required = sig['required']
    z2m.optional = sig['optional']
    z2m.varargs = sig['varargs']
    z2m.kwargs = sig['kwargs']
    return z2m

def createZope3Bridge(zope3, package, name):
    # Map a Zope 3 interface into a Zope2 interface, seated within 'package'
    # as 'name'.
    z2i = fromZ3Interface(zope3)

    if name is not None:
        z2i.__dict__['__name__'] = name

    z2i.__dict__['__module__'] = package.__name__
    setattr(package, z2i.getName(), z2i)
