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
"""Interface object implementation

Revision information:
$Id$
"""

from inspect import currentframe
import sys
from Method import Method, fromFunction
from Attribute import Attribute
from types import FunctionType
import Exceptions
from _Element import Element
from _object import isInstance

class Interface(Element):
    """Prototype (scarecrow) Interfaces Implementation
    """

    # We can't say this yet because we don't have enough
    # infrastructure in place.
    #
    #__implements__ = IInterface

    def __init__(self, name, bases=(), attrs=None, __doc__=None,
                 __module__=None):

        if __module__ is None:
            if attrs is not None and attrs.has_key('__module__'):
                __module__ = attrs['__module__']
                del attrs['__module__']
            else:
                try:
                    # Figure out what module defined the interface.
                    # This is how cPython figures out the module of
                    # a class, but of course it does it in C. :-/
                    __module__ = currentframe().f_back.f_globals['__name__']
                except (AttributeError, KeyError):
                    pass
        self.__module__ = __module__

        for b in bases:
            if not isInstance(b, Interface):
                raise TypeError, 'Expected base interfaces'
        self.__bases__=bases

        if attrs is None: attrs={}
        if attrs.has_key('__doc__'):
            if __doc__ is None: __doc__=attrs['__doc__']
            del attrs['__doc__']

        if __doc__ is not None:
            self.__doc__=__doc__
        else:
            self.__doc__ = ""

        Element.__init__(self, name, __doc__)

        for k, v in attrs.items():
            if isInstance(v, Attribute):
                v.interface=name
                if not v.__name__:
                    v.__name__ = k
            elif isinstance(v, FunctionType):
                attrs[k]=fromFunction(v, name)
            else:
                raise Exceptions.InvalidInterface(
                    "Concrete attribute, %s" % k)

        self.__attrs = attrs

    def getBases(self):
        return self.__bases__

    def extends(self, other, strict=1):
        """Does an interface extend another?
        """
        if not strict and self is other:
            return 1

        for b in self.__bases__:
            if b == other: return 1
            if b.extends(other): return 1
        return 0

    def isEqualOrExtendedBy(self, other):
        """Same interface or extends?
        """
        if self == other:
            return 1
        return other.extends(self)

    def isImplementedBy(self, object):
        """Does the given object implement the interface?
        """
        i = getImplements(object)
        if i is not None:
            return visitImplements(
                i, object, self.isEqualOrExtendedBy, self._getInterface)
        return 0

    def isImplementedByInstancesOf(self, klass):
        """Do instances of the given class implement the interface?
        """
        i = getImplementsOfInstances(klass)
        if i is not None:
            return visitImplements(
                i, klass, self.isEqualOrExtendedBy, self._getInterface)
        return 0

    def names(self, all=0):
        """Return the attribute names defined by the interface
        """
        if not all:
            return self.__attrs.keys()

        r = {}
        for name in self.__attrs.keys():
            r[name] = 1
        for base in self.__bases__:
            for name in base.names(all):
                r[name] = 1
        return r.keys()

    def namesAndDescriptions(self, all=0):
        """Return the attribute names and descriptions defined by the interface
        """
        if not all:
            return self.__attrs.items()

        r = {}
        for name, d in self.__attrs.items():
            r[name] = d

        for base in self.__bases__:
            for name, d in base.namesAndDescriptions(all):
                if not r.has_key(name):
                    r[name] = d

        return r.items()

    def getDescriptionFor(self, name):
        """Return the attribute description for the given name
        """
        r = self.queryDescriptionFor(name)
        if r is not None:
            return r

        raise KeyError, name

    def queryDescriptionFor(self, name, default=None):
        """Return the attribute description for the given name
        """
        r = self.__attrs.get(name, self)
        if r is not self:
            return r
        for base in self.__bases__:
            r = base.queryDescriptionFor(name, self)
            if r is not self:
                return r

        return default

    def deferred(self):
        """Return a defered class corresponding to the interface
        """
        if hasattr(self, "_deferred"): return self._deferred

        klass={}
        exec "class %s: pass" % self.__name__ in klass
        klass=klass[self.__name__]

        self.__d(klass.__dict__)

        self._deferred=klass

        return klass

    def _getInterface(self, ob, name):
        '''
        Retrieve a named interface.
        '''
        return None

    def __d(self, dict):

        for k, v in self.__attrs.items():
            if isInstance(v, Method) and not dict.has_key(k):
                dict[k]=v

        for b in self.__bases__: b.__d(dict)

    def __repr__(self):
        name = self.__name__
        m = self.__module__
        if m:
            name = '%s.%s' % (m, name)
        return "<%s %s at %x>" % (self.__class__.__name__, name, id(self))

    def __reduce__(self):
        return self.__name__

    def __hash__(self):
        """ interface instances need to be hashable, and inheriting
        from extensionclass makes instances unhashable unless we declare
        a __hash__ method here"""
        return id(self)

# We import this here to deal with module dependencies.
from Implements import getImplementsOfInstances, visitImplements, getImplements
from Implements import instancesOfObjectImplements
