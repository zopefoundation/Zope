##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Python Interfaces

  Classes or objects can implement an __implements__ attribute that
  names an interface object or a collection of interface objects.

  An interface is defined using the class statement and one or more base
  interfaces.
"""

from Method import Method
from Attr import Attribute
from types import FunctionType, ClassType
import Exceptions

_typeImplements={}

class Interface:
    """Prototype (scarecrow) Interfaces Implementation
    """

    def __init__(self, name, bases=(), attrs=None, __doc__=None):
        """Create a new interface
        """        
        for b in bases:
            if not isinstance(b, Interface):
                raise TypeError, 'Expected base interfaces'
        self.__bases__=bases
        self.__name__=name

        if attrs is None: attrs={}
        if attrs.has_key('__doc__'):
            if __doc__ is None: __doc__=attrs['__doc__']
            del attrs['__doc__']
        self.__attrs=attrs

        if __doc__ is not None: self.__doc__=__doc__

        for k, v in attrs.items():
            if isinstance(v, Method):
                v.interface=name
                v.__name__=k
            elif isinstance(v, FunctionType):
                attrs[k]=Method.fromFunction(v, name)
            elif not isinstance(v, Attribute):
                raise Exceptions.InvalidInterface(
                    "Concrete attribute, %s" % k)

    def defered(self):
        """Return a defered class corresponding to the interface
        """
        if hasattr(self, "_defered"): return self._defered

        klass={}
        exec "class %s: pass" % self.__name__ in klass
        klass=klass[self.__name__]
        
        self.__d(klass.__dict__)

        self._defered=klass

        return klass

    def __d(self, dict):

        for k, v in self.__dict__.items():
            if isinstance(v, Method) and not dict.has_key(k):
                dict[k]=v

        for b in self.__bases__: b.__d(dict)
            

    def extends(self, other):
        """Does an interface extend another?
        """
        for b in self.__bases__:
            if b is other: return 1
            if b.extends(other): return 1
        return 0

    def implementedBy(self, object,
                      tiget=_typeImplements.get):
        """Does the given object implement the interface?
        """
        t=type(object)
        if t is ClassType:
            if hasattr(object, '__class_implements__'):
                implements=object.__class_implements__
            else: implements=Class
        elif hasattr(object, '__implements__'):
            implements=object.__implements__
        else:
            implements=tiget(t, None)
            if implements is None: return 0
    
        if isinstance(implements,Interface):
            return implements is self or implements.extends(self)
        else:
            return self.__any(implements)

    def implementedByInstancesOf(self, klass,
                                 tiget=_typeImplements.get):
        """Do instances of the given class implement the interface?
        """
        if type(klass) is ClassType:
            if hasattr(klass, '__implements__'):
                implements=klass.__implements__
            else: return 0
        elif hasattr(klass, 'instancesImplement'):
            # Hook for ExtensionClass. :)
            implements=klass.instancesImplement()
        else:
            implements=tiget(klass,None)

        if implements is None: return 0
        
        if isinstance(implements,Interface):
            return implements is self or implements.extends(self)
        else:
            return self.__any(implements)

    def interfaceName(self):
        """ name? """
        return self.__name__

    def implements(self):
        """ Returns a list of sequence of base Interfaces """
        return self.__bases__

    def names(self):
        """Return the attribute names defined by the interface
        """
        return self.__attrs.keys()

    def namesAndDescriptions(self):
        """Return the attribute names and descriptions defined by the interface
        """
        return self.__attrs.items()

    def getDescriptionFor(self, name, default=None):
        """Return the attribute description for the given name
        """
        return self.__attrs.get(name, default)

    def __any(self, interfaces):
        for i in interfaces:
            if isinstance(i,Interface):
                if i is self or i.extends(self): return 1
            else:
                if self.__any(i): return 1
        return 0

    def documentation(self):
        """ returns the doc string for the inteface """
        return self.__doc__

    def __repr__(self):
        return "<Interface %s at %x>" % (self.__name__, id(self))

Base=Interface("Interface")

class Named(Base):
    "Objects that have a name."

    __name__=Attribute("The name of the object")

class Class(Named):
    """Implement shared instance behavior and create instances
    
    Classes can be called to create an instance.  This interface does
    not specify what if any arguments are required.
    """

    # Note that we don't use a function definition here, because
    # we don't want to specify a signature!
    __call__=Method("Instantiate instances of the class")

    __bases__=Attribute("A sequence of base classes")


def assertTypeImplements(type, interfaces):
    """Return the interfaces implemented by objects of the given type
    """
    _typeImplements[type]=interfaces
