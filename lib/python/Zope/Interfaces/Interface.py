import types

class Interface:
    """
    Describes an interface.
    """

    __extends__=()

    def __init__(self, klass, name=None):
        # Creates an interface instance given a python class.
        # the class describes the inteface; it contains
        # methods, arguments and doc strings.
        # 
        # The name of the interface is deduced from the __name__
        # attribute.
        #
        # The base interfaces are deduced from the __extends__
        # attribute.

        if name is not None:
            self.name = name
        else:
            self.name=klass.__name__
            
        self.doc=klass.__doc__
        if hasattr(klass,'__extends__'):
            self.extends=klass.__extends__
        
        # Get info on attributes, ignore
        # attributes that start with underscore.
        self.attributes=[]
        for k,v in klass.__dict__.items():
            if k[0] != '_':
                if type(v)==types.FunctionType:
                    self.attributes.append(Method(v))
                else:
                    self.attributes.append(Attribute(k))
        
    def getAttributes(self):
        """
        Returns the interfaces attributes.
        """
        return self.attributes
    
    

class Attribute:
    """
    Describes an attribute of an interface.
    """
    
    permission="" # how to indicate permissions, in docstrings?
    
    def __init__(self, name):
        self.name=name
        self.doc="" # how to get doc strings from attributes?


class Method(Attribute):
    """
    Describes a Method attribute of an interface.
    
    required - a sequence of required arguments 
    optional - a sequence of tuples (name, default value)
    varargs - the name of the variable argument or None
    kwargs - the name of the kw argument or None
    """
    
    varargs=None
    kwargs=None
    
    def __init__(self, func):
        self.name=func.__name__
        self.doc=func.__doc__
        
        # figure out the method arguments
        # mostly stolen from pythondoc
        CO_VARARGS = 4
        CO_VARKEYWORDS = 8
        names = func.func_code.co_varnames
        nrargs = func.func_code.co_argcount
        if func.func_defaults:
            nrdefaults = len(func.func_defaults)
        else:
            nrdefaults = 0
        self.required = names[:nrargs-nrdefaults]
        if func.func_defaults:
            self.optional = tuple(map(None, names[nrargs-nrdefaults:nrargs],
                                 func.func_defaults))
        else:
            self.optional = ()
        varargs = []
        ix = nrargs
        if func.func_code.co_flags & CO_VARARGS:
            self.varargs=names[ix]
            ix = ix+1
        if func.func_code.co_flags & CO_VARKEYWORDS:
            self.kwargs=names[ix]


if __name__=='__main__':
    class T:
        "test interface description"
        __name__="org.zope.test"
        a=None
        
        def foo(self, a, b=None, *c, **d):
            "foo description"
            
    i=Interface(T)
    print i.name
    print i.doc
    for a in i.getAttributes():
        print a.__dict__
    
