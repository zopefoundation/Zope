"""Python Interfaces

Scarecrow version:

  Classes or objects can implement an __implements__ attribute that
  names an interface object or a collection of interface objects.

  An interface is defined using the class statement and one or more base
  interfaces.
"""

from Method import Method
from Attr import Attribute
from types import FunctionType, ClassType
import Exceptions
from InterfaceBase import InterfaceBase

_typeImplements={}

class Interface(InterfaceBase):
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

        if __doc__ is not None:
            self.__doc__=__doc__
        else:
            self.__doc__ = ""

        for k, v in attrs.items():
            if isinstance(v, Method):
                v.interface=name
                v.__name__=k
            elif isinstance(v, FunctionType):
                attrs[k]=Method.fromFunction(v, name)
            elif not isinstance(v, Attribute):
                raise Exceptions.InvalidInterface(
                    "Concrete attribute, %s" % k)

        self.__attrs = attrs

    def getBases(self):
        return self.__bases__

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

    def deferred(self):
        """Return a defrered class corresponding to the interface
        """
        if hasattr(self, "_deferred"): return self._deferred

        klass={}
        exec "class %s: pass" % self.__name__ in klass
        klass=klass[self.__name__]
        
        self.__d(klass.__dict__)

        self._deferred=klass

        return klass

    def __d(self, dict):

        for k, v in self.__attrs.items():
            if isinstance(v, Method) and not dict.has_key(k):
                dict[k]=v

        for b in self.__bases__: b.__d(dict)
            

    def __any(self, interfaces):
        for i in interfaces:
            if isinstance(i,Interface):
                if i is self or i.extends(self): return 1
            else:
                if self.__any(i): return 1
        return 0

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
