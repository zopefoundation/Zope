"""\
xapply

Inspired by Don Beaudry's functor module.

xapply exports one public function, the eponymous xapply. xapply can
be thought of as `lazy apply' or `partial argument resolution'.

It takes a function and part of it's argument list, and returns a
function with the first parameters filled in. An example:

def f(x,y):
    return x+y

add1 = xapply(f,1)

add1(2) => 3

This xapply is not yet as general as that from the functor module, but
the functions return are as fast as normal function, i.e. twice as
fast as functors.

This may be generalised at some point in the future.
"""

import new,string,re,types
from ops import LOAD_FAST, LOAD_CONST
from code_editor import Function, InstanceMethod

def xapply_munge(code, args, except0=0):
    nconsts = len(code.co_consts)
    nvars = len(args)

    code.co_consts.extend(list(args))
    
    if except0:
        var2constlim = nvars+1
        var2constoff = nconsts-1
    else:
        var2constlim = nvars
        var2constoff = nconsts

    cs = code.co_code
    for i in range(len(cs)):
        op = cs[i]
        if op.__class__ is LOAD_FAST:
            if op.arg == 0 and except0:
                continue
            if op.arg < var2constlim:
                cs[i] = LOAD_CONST(op.arg + var2constoff)
            else:
                op.arg = op.arg - nvars
    code.co_varnames = code.co_varnames[nvars:]
    code.co_argcount = code.co_argcount - nvars

def xapply_func(func,args):
    f = Function(func)
    xapply_munge(f.func_code,args,0)
    return f.make_function()

def xapply_meth(meth,args):
    im = InstanceMethod(meth)
    xapply_munge(im.im_func.func_code,args,1)
    return im.make_instance_method()

def xapply(callable,*args):
    """ xapply(callable,arg1,arg2,...) -> callable

if

f=xapply(callable,arg1,arg2,...,argn)

then

f(arg<n+1>,....argm)

is equivalent to

callable(arg1,...,argn,arg<n+1>,..argm)

callable currently must be a function or instance method, and keyword
arguments are currently not allowed.

"""
    callable_type=type(callable)
    if callable_type is types.FunctionType:
        return xapply_func(callable,args)
    elif callable_type is types.UnboundMethodType:
        return xapply_meth(callable,args)
    else:
        raise "nope"


