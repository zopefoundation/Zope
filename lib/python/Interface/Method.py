"""Method interfaces
"""
import Exceptions
from Attr import Attribute

class MethodClass:

    def fromFunction(self, func, interface=''):
        m=Method(func.__name__, func.__doc__)
        defaults=func.func_defaults or ()
        c=func.func_code
        na=c.co_argcount
        names=c.co_varnames
        d={}
        nr=na-len(defaults)
        if nr==0:
            defaults=defaults[1:]
            nr=1
        
        for i in range(len(defaults)):
            d[names[i+nr]]=defaults[i]

        m.positional=names[1:na]
        m.required=names[1:nr]
        m.optional=d
        m.varargs = not not (c.co_flags & 4)
        m.kwargs  = not not (c.co_flags & 8)
        m.interface=interface
        return m

class Method(Attribute):
    """Method interfaces

    The idea here is that you have objects that describe methods.
    This provides an opportunity for rich meta-data.
    """

    fromFunction=MethodClass().fromFunction
    interface=''

    def __init__(self, __name__=None, __doc__=None):
        """Create a 'method' description
        """
        self.__name__=__name__
        self.__doc__=__doc__ or __name__

    def __call__(self, *args, **kw):
        raise Exceptions.BrokenImplementation(self.interface, self.__name__)
        
    
