from iclass import Interface, ClassType, Base, assertTypeImplements

def impliedInterface(klass, __name__=None, __doc__=None):
    """Create an interface object from a class

    The interface will contain only objects with doc strings and with names
    that begin and end with '__' or names that don't begin with '_'.
    """
    if __name__ is None: name="%sInterface" % klass.__name__
    return Interface(__name__, (), _ii(klass, {}), __doc__)

def _ii(klass, items):
    for k, v in klass.__dict__.items():
        if k[:1]=='_' and not (len(k) > 4 and k[:2]=='__' and k[-2:]=='__'):
            continue
        items[k]=v
    for b in klass.__bases__: _ii(b)
    return items
    
def implementedBy(object):        
    """Return the interfaces implemented by the object
    """
    r=[]

    implements=tiget(type(object), None)
    if implements is None:
        if hasattr(object, '__implements__'):
            implements=object.__implements__
        else: return r

    if isinstance(implements,Interface): r.append(i)
    else: _wi(implements, r.append)

    return r

    
def implementedByInstances(object):
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
        if isinstance(implements,Interface): r.append(i)
        else: _wi(implements, r.append)

    return r


def _wi(interfaces, append):
    for i in interfaces:
        if isinstance(i,Interface): append(i)
        else: _wi(i, append)
