"""\
closure

implements a form of closures by abusing the co_consts field of a code
object.

exports: bind, bind_locals, bind_now
and contains two examples: make_adder, make_balance
"""

from code_editor import Function
from ops import *

def scan_for_STORE(func,name):
    for i in func.func_code.co_code:
        if i.__class__ in [STORE_FAST,STORE_NAME,STORE_GLOBAL] \
           and i.name == name:
            return 1
    return 0

def bind(function,newname=None,**vars):
    """\
bind(function[,newname],var1=value1,var2=value2,...) -> function

returns a new function (optionally renamed) where every reference to
one of var1, var2, etc is replaced by a reference to the respective
valueN."""
    func = Function(function)
    code = func.func_code
    cs   = func.func_code.co_code

    name2index = {}

    mutated = {}

    for name in vars.keys():
        mutated[name] = scan_for_STORE(func,name)

    if 0 in code.co_consts:
        zeroIndex = code.co_consts.index(0)
    else:
        zeroIndex = len(code.co_consts)
        code.co_consts.append(0)

    i = 0

    while i < len(cs):
        op = cs[i]
        i = i + 1
        # should LOAD_NAME be here??? tricky, I'd say
        if op.__class__ in [LOAD_GLOBAL,LOAD_NAME,LOAD_FAST]:
            if not vars.has_key(op.name):
                continue
            if mutated[name]:
                if not name2index.has_key(op.name):
                    name2index[op.name]=len(code.co_consts)
                code.co_consts.append([vars[op.name]])
                cs[i-1:i] = [LOAD_CONST(name2index[op.name]),
                             LOAD_CONST(zeroIndex),
                             BINARY_SUBSCR()]
                i = i + 2
            else:
                if not name2index.has_key(op.name):
                    name2index[op.name]=len(code.co_consts)
                code.co_consts.append(vars[op.name])
                cs[i-1] = LOAD_CONST(name2index[op.name])
        elif op.__class__ in [STORE_FAST,STORE_NAME,STORE_GLOBAL]:
            if not vars.has_key(op.name):
                continue
            if not mutated[name]:
                continue # shouldn't be reached
            cs[i-1:i] = [LOAD_CONST(name2index[op.name]),
                         LOAD_CONST(zeroIndex),
                         STORE_SUBSCR()]
            i = i + 2

    if newname is not None:
        func.func_name = newname

    return func.make_function()

bind=Function(bind)
bind.func_code.co_varnames[0]='$function'
bind.func_code.co_varnames[1]='$newname'
bind=bind.make_function()

def bind_locals(func):
    """bind_locals(func) -> function

returns a new function where every global variable reference in func
is replaced, if possible, by a reference to a local variable in the
callers context."""
    try:
        raise ""
    except:
        import sys
        frame = sys.exc_traceback.tb_frame.f_back
        name = func.func_name+'+'
        l = apply(bind,(func,name),frame.f_locals)
        frame = None
        return l

def bind_now(func):
    """bind_now(func) -> function

returns a new function where every global variable reference in func
is replaced, if possible, by a reference to a variable in the callers
context."""
    try:
        raise ""
    except:
        import sys
        frame = sys.exc_traceback.tb_frame.f_back
        l = apply(bind,(func,),frame.f_locals)
        g = apply(bind,(l,),frame.f_globals)
        frame = None
        return g

## examples

def make_adder(n):
    """make_adder(n) -> function

return a monadic function that adds n to its argument."""
    def adder(x):
        return x+n
    return bind_locals(adder)

def make_balance(initial_amount):
    """make_balance(initial_amount) -> function

demonstrates an object with state, sicp style."""
    def withdraw(amount):
        if current[0]<amount:
            raise "debt!"
        else:
            current[0]=current[0]-amount
        return current[0]
    return bind(withdraw,current=[initial_amount])
