"""Method interfaces
"""
import Exceptions
from Attr import Attribute

sig_traits = ['positional', 'required', 'optional', 'varargs', 'kwargs']

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

    def fromMethod(self, meth, interface=''):
        func = meth.im_func
        return self.fromFunction(func, interface)

class Method(Attribute):
    """Method interfaces

    The idea here is that you have objects that describe methods.
    This provides an opportunity for rich meta-data.
    """

    fromFunction=MethodClass().fromFunction
    fromMethod=MethodClass().fromMethod
    interface=''

    def __init__(self, __name__=None, __doc__=None):
        """Create a 'method' description
        """
        self.__name__=__name__
        self.__doc__=__doc__ or __name__

    def __call__(self, *args, **kw):
        raise Exceptions.BrokenImplementation(self.interface, self.__name__)

    def isMethod(self):
        return 1
        
    def getSignatureInfo(self):
        info = {}
        for t in sig_traits:
            info[t] = getattr(self, t) 

        return info

    def getSignatureRepr(self):
        sig = "("
        for v in self.positional:
            sig = sig + v
            if v in self.optional.keys():
                sig = sig + "=%s" % `self.optional[v]`
            sig = sig + ", "
        if self.varargs:
            sig = sig + "*args, "
        if self.kwargs:
            sig = sig + "**kws, "

        # slice off the last comma and space
        if self.positional or self.varargs or self.kwargs:
            sig = sig[:-2]

        sig = sig + ")"
        return sig


























