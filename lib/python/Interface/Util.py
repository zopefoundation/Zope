from iclass import Interface, Class, ClassType, Base, assertTypeImplements
from types import FunctionType

def impliedInterface(klass, __name__=None, __doc__=None):
    """Create an interface object from a class

    The interface will contain only objects with doc strings and with names
    that begin and end with '__' or names that don't begin with '_'.
    """
    if __name__ is None: __name__="%sInterface" % klass.__name__
    return Interface(__name__, (), _ii(klass, {}), __doc__)

def _ii(klass, items):
    for k, v in klass.__dict__.items():
        if type(v) is not FunctionType or not v.__doc__:
            continue
        if k[:1]=='_' and not (k[:2]=='__' and k[-2:]=='__'):
            continue
        items[k]=v
    for b in klass.__bases__: _ii(b, items)
    return items
    
def objectImplements(object):        
    """Return the interfaces implemented by the object
    """
    r=[]

    t=type(object)
    if t is ClassType:
        if hasattr(object, '__class_implements__'):
            implements=object.__class_implements__
        else:
            implements=Class
    elif hasattr(object, '__implements__'):
        implements=object.__implements__
    else:
        implements=tiget(t, None)
        if implements is None: return r

    if isinstance(implements,Interface): r.append(implements)
    else: _wi(implements, r.append)

    return r

    
def instancesOfObjectImplements(klass):
    """Return the interfaces that instanced implement (by default)
    """
    r=[]

    if type(klass) is ClassType:
        if hasattr(klass, '__implements__'):
            implements=klass.__implements__
        else: return r
    elif hasattr(klass, 'instancesImplements'):
        # Hook for ExtensionClass. :)
        implements=klass.instancesImplements()
    else:
        implements=tiget(klass,None)

    if implements is not None: 
        if isinstance(implements,Interface): r.append(implements)
        else: _wi(implements, r.append)

    return r


def _wi(interfaces, append):
    for i in interfaces:
        if isinstance(i,Interface): append(i)
        else: _wi(i, append)
