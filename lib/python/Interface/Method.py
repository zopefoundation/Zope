"""Method interfaces
"""
import Exceptions
from Attr import Attribute

sig_traits = ['positional', 'required', 'optional', 'varargs', 'kwargs']

CO_VARARGS = 4
CO_VARKEYWORDS = 8

class MethodClass:

    def fromFunction(self, func, interface='', strip_first=0):
        m=Method(func.__name__, func.__doc__)
        defaults=func.func_defaults or ()
        c=func.func_code
        na=c.co_argcount
        names=c.co_varnames
        d={}
        nr=na-len(defaults)

        if strip_first and nr==0: # 'strip_first' implies method, has 'self'
            defaults=defaults[1:]
            nr=1
        
        for i in range(len(defaults)):
            d[names[i+nr]]=defaults[i]

        start_index = strip_first and 1 or 0
        m.positional=names[start_index:na]
        m.required=names[start_index:nr]
        m.optional=d

        argno = na
        if c.co_flags & CO_VARARGS:
            m.varargs = names[argno]
            argno = argno + 1
        else:
            m.varargs = None
        if c.co_flags & CO_VARKEYWORDS:
            m.kwargs = names[argno]
        else:
            m.kwargs = None

        m.interface=interface
        return m

    def fromMethod(self, meth, interface=''):
        func = meth.im_func
        return self.fromFunction(func, interface, strip_first=1)

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

    def getSignatureInfo(self):
        info = {}
        for t in sig_traits:
            info[t] = getattr(self, t) 

        return info

    def getSignatureString(self):
        sig = "("
        for v in self.positional:
            sig = sig + v
            if v in self.optional.keys():
                sig = sig + "=%s" % `self.optional[v]`
            sig = sig + ", "
        if self.varargs:
            sig = sig + ("*%s, " % self.varargs)
        if self.kwargs:
            sig = sig + ("**%s, " % self.kwargs)

        # slice off the last comma and space
        if self.positional or self.varargs or self.kwargs:
            sig = sig[:-2]

        sig = sig + ")"
        return sig


























