import dis
from code_editor import Function
from find_function_call import find_function_call
from ops import \
     LOAD_GLOBAL, RETURN_VALUE, SET_LINENO, CALL_FUNCTION, \
     JUMP_FORWARD, STORE_FAST

INLINE_MAX_DEPTH = 100

def inline(func, **funcs):
    func = Function(func)
    code = func.func_code

    for name, function in funcs.items():
        count = inline1(func, name, function)

        if count <> 0:
            fcode=function.func_code
            code.co_consts=code.co_consts+list(fcode.co_consts)
            code.co_varnames=code.co_varnames+list(fcode.co_varnames)
            code.co_names=code.co_names+list(fcode.co_names)
            code.co_stacksize=code.co_stacksize+fcode.co_stacksize

    return func.make_function()

def munge_code(function,code):
    f = Function(function)
    fcs = f.func_code.co_code
    i, n = 0, len(fcs)
    retops = []
    while i < n:
        op = fcs[i]
        if op.__class__ is RETURN_VALUE:
            # RETURN_VALUEs have to be replaced by JUMP_FORWARDs
            newop = JUMP_FORWARD()
            fcs[i] = newop
            retops.append(newop)
        elif op.op in dis.hasname:
            op.arg = op.arg + len(code.co_names)
        elif op.op in dis.haslocal:
            op.arg = op.arg + len(code.co_varnames)
        elif op.op in dis.hasconst:
            op.arg = op.arg + len(code.co_consts)
        # should we hack out SET_LINENOs? doesn't seem worth it.
        i = i + 1
    return fcs.opcodes, retops

def inline1(func,funcname,function):
    code = func.func_code
    cs = code.co_code
    count = 0
    defaults_added = 0

    while count < INLINE_MAX_DEPTH:
        stack, numkeywords = find_function_call(func,funcname,allowkeywords=1)

        if stack is None:
            return count

        count = count + 1

        load_func, posargs, kwargs, function_call = \
                   stack[0], stack[1:-2*numkeywords-1], stack[-2*numkeywords-1:-1], stack[-1]

        kw={}
        
        for i in range(0,len(kwargs),2):
            name = code.co_consts[kwargs[i].arg]
            valuesrc = kwargs[i+1]
            kw[name] = valuesrc

        varnames = list(function.func_code.co_varnames)

        for i in kw.keys():
            if i in varnames:
                if varnames.index(i) < len(posargs):
                    raise TypeError, "keyword parameter redefined"
            else:
                raise TypeError, "unexpected keyword argument: %s"%i

        # no varargs yet!
#          flags = function.func_code.co_flags

#          varargs = flags & (1<<2)
#          varkeys = flags & (1<<3)        


        args_got = len(kw) + len(posargs)
        args_expected = function.func_code.co_argcount

        if args_got > args_expected:
            raise TypeError,"too many arguments; expected %d, got %d"%(ac,len(lf) + len(posargs))
        elif args_got < args_expected:
            # default args?
            raise TypeError,"not enough arguments; expected %d, got %d"%(ac,len(lf) + len(posargs))
        
        cs.remove(load_func)

        local_index = len(code.co_varnames) 

        for insn in posargs:
            new = STORE_FAST(local_index)
            cs.insert(cs.index(insn)+1,new)
            labels = cs.find_labels(cs.index(new)+1)
            for label in labels:
                label.op = new
            local_index = local_index + 1

        for name, insn in kw.items():
            new = STORE_FAST(varnames.index(name) + len(code.co_varnames))
            cs.insert(cs.index(insn)+1,new)
            labels = cs.find_labels(cs.index(new)+1)
            for label in labels:
                label.op = new

        newops, retops = munge_code(function,code)

        call_index = cs.index(function_call)
        nextop = cs[call_index + 1]

        cs[call_index:call_index + 1] = newops

        for op in retops:
            op.label.op = nextop

    raise RuntimeError, "are we trying to inline a recursive function here?"

    

