"""Provide an apply-like facility that works with any mapping object
"""

def default_call_object(object, args, context):
    result=apply(object,args) # Type s<cr> to step into published object.
    return result

def default_missing_name(name, context):
    raise TypeError, 'argument %s was ommitted' % name

def default_handle_class(klass, context):
    if hasattr(klass,'__init__'): 
        f=klass.__init__.im_func
        c=f.func_code
        names=c.co_varnames[1:c.co_argcount]
        return klass, names, f.func_defaults
    else:
        return klass, (), ()

def mapply(object, positional=(), keyword={},
           debug=None, maybe=None,
           missing_name=default_missing_name,
           handle_class=default_handle_class,
           context=None
           ):

    if hasattr(object,'__bases__'):
        f, names, defaults = handle_class(object, context)
    else:
        f=object
        im=0
        if hasattr(f, 'im_func'):
            im=1
        elif not hasattr(f,'func_defaults'):
            if hasattr(f, '__call__'):
                f=f.__call__
                if hasattr(f, 'im_func'):
                    im=1
                elif not hasattr(f,'func_defaults') and maybe: return object
            elif maybe: return object
    
        if im:
            f=f.im_func
            c=f.func_code
            defaults=f.func_defaults
            names=c.co_varnames[1:c.co_argcount]
        else:
            defaults=f.func_defaults
            c=f.func_code
            names=c.co_varnames[:c.co_argcount]

    nargs=len(names)
    if positional:
        if len(positional) > nargs: raise TypeError, 'too many arguments'
        args=list(positional)
    else:
        args=[]

    get=keyword.get
    nrequired=len(names) - (len(defaults or ()))
    for index in range(len(args), len(names)):
        name=names[index]
        v=get(name, args)
        if v is args:
            if index < nrequired: v=missing_name(name, context)
            else: v=defaults[index-nrequired]
        args.append(v)

    args=tuple(args)
    if debug is not None: return debug(object,args,context)
    else: return apply(object,args)
