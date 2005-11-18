##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Implemantation assertion facilities.

Revision information:
$Id$
"""

import Exceptions
from types import ClassType
from Verify import verifyClass
from _InterfaceClass import Interface as InterfaceClass
from types import TupleType, ClassType, StringType

# Special value indicating the object supports
# what its class supports.
CLASS_INTERFACES = 1

from _object import ClassTypes, isInstance

_typeImplements={}

def getImplements(object):
    t = type(object)
    if t in ClassTypes:
        if hasattr(object, '__class_implements__'):
            return object.__class_implements__
    elif hasattr(object, '__implements__'):
        return object.__implements__

    return _typeImplements.get(t, None)


def getImplementsOfInstances(klass, tiget=_typeImplements.get):
    if type(klass) in ClassTypes:
        if hasattr(klass, '__implements__'):
            return klass.__implements__
        else:
            return None
    else:
        return tiget(klass, None)


def visitImplements(implements, object, visitor, getInterface=None):
    """
    Visits the interfaces described by an __implements__ attribute,
    invoking the visitor for each interface object.
    If the visitor returns anything true, the loop stops.
    This does not, and should not, visit superinterfaces.
    """
    # this allows us to work with proxy wrappers in Python 2.2,
    # yet remain compatible with earlier versions of python.
    implements_class = getattr(implements, '__class__', None)

    if implements_class == InterfaceClass or \
       isInstance(implements, InterfaceClass):
        return visitor(implements)
    elif implements == CLASS_INTERFACES:
        klass = getattr(object, '__class__', None)
        if klass is not None:
            i = getImplementsOfInstances(klass)
            if i:
                return visitImplements(i, object, visitor, getInterface)
    elif implements_class == StringType or type(implements) is StringType:
        if getInterface is not None:
            # Look up a named interface.
            i = getInterface(object, implements)
            if i is not None:
                return visitImplements(i, object, visitor, getInterface)
    elif implements_class == TupleType or type(implements) is TupleType:
        for i in implements:
            r = visitImplements(i, object, visitor, getInterface)
            if r:
                # If the visitor returns anything true, stop.
                return r
    else:
        if implements_class is not None and \
           type(implements) != implements_class:
            raise Exceptions.BadImplements(
                """__implements__ should be an interface or tuple,
                not a %s pretending to be a %s"""
                % (type(implements).__name__, implements_class.__name__)
                )
        raise Exceptions.BadImplements(
            """__implements__ should be an interface or tuple,
            not a %s""" % type(implements).__name__)
    return 0


def assertTypeImplements(type, interfaces):
    """Assign a set of interfaces to a Python type such as int, str, tuple,
       list and dict.
    """
    _typeImplements[type]=interfaces

def objectImplements(object, getInterface=None):
    r = []
    implements = getImplements(object)
    if not implements:
        return r
    visitImplements(implements, object, r.append, getInterface)
    return r

def instancesOfObjectImplements(klass, getInterface=None):
    r = []
    implements = getImplementsOfInstances(klass)
    if not implements:
        return r
    visitImplements(implements, klass, r.append, getInterface)
    return r


def _flatten(i, append):
    append(i)
    bases = i.getBases()
    if bases:
        for b in bases:
            _flatten(b, append)

def _detuplize(interface, append):
    if type(interface) is TupleType:
        for subinterface in interface:
             _detuplize(subinterface, append)
    else:
        append(interface)

def flattenInterfaces(interfaces, remove_duplicates=1):
    detupledInterfaces = []
    for interface in interfaces:
        _detuplize(interface, detupledInterfaces.append)
    res = []
    for i in detupledInterfaces:
        _flatten(i, res.append)
    if remove_duplicates:
        # Remove duplicates in reverse.
        # Similar to Python 2.2's method resolution order.
        seen = {}
        index = len(res) - 1
        while index >= 0:
            i = res[index]
            if seen.has_key(i):
                del res[index]
            else:
                seen[i] = 1
            index = index - 1
    return res

def implements(klass, interface, check=1):
    if check:
        verifyClass(interface, klass, tentative=1)

    old=getattr(klass, '__implements__', None)
    if old is None:
        klass.__implements__ = interface
    else:
        klass.__implements__ = old, interface
