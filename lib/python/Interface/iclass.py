"""Python Interfaces

Scarecrow version:

  Classes or objects can implement an __implements__ attribute that
  names a sequence of interface objects.

  An interface is defined using the class statement and one or more base
  interfaces.
"""

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
        implements=tiget(type(object), None)
        if implements is None:
            if hasattr(object, '__implements__'):
                implements=object.__implements__
            else: return 0
    
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
        elif hasattr(klass, 'instancesImplements'):
            # Hook for ExtensionClass. :)
            implements=klass.instancesImplements()
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

    def __any(self, interfaces):
        for i in interfaces:
            if isinstance(i,Interface):
                return i is self or i.extends(self)
            else:
                return self.__any(i)

ClassType=type(Interface)

Base=Interface("Interface")

def assertTypeImplements(type, interfaces):
    """Return the interfaces implemented by objects of the given type
    """
    _typeImplements[type]=interfaces

