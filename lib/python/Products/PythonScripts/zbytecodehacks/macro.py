import dis
from code_editor import Function
from find_function_call import find_function_call
from ops import *

MAX_MACRO_DEPTH = 100

_macros = {}

def add_macro(arg1,arg2=None):
    if arg2 is None:
        _macros[arg1.func_name] = arg1
    else:
        _macros[arg1]=arg2

def expand(func, macros = None):
    func = Function(func)
    code = func.func_code

    if macros is None:
        macros = _macros

    insertions = {}
    trips = 0

    while trips < MAX_MACRO_DEPTH:
        outercount = 0

        for name,macro in macros.items():
            count = expand1(func, name, macro)

            outercount = outercount + count

            if count <> 0 and not insertions.has_key(macro):
                fcode=macro.func_code
                code.co_consts=code.co_consts+list(fcode.co_consts)
                code.co_varnames=code.co_varnames+list(fcode.co_varnames)
                code.co_names=code.co_names+list(fcode.co_names)
                code.co_stacksize=code.co_stacksize+fcode.co_stacksize
                insertions[macro] = 0
                
        if not outercount:
            return func.make_function()
        trips = trips + 1
        
    raise RuntimeError, "unbounded recursion?!"

def expand_these(func,**macros):
    return expand(func,macros)

def remove_epilogue(cs):
    try:
        last,butone,buttwo = cs[-3:]
    except:
        return
    if last.__class__ is buttwo.__class__ is RETURN_VALUE:
        if butone.__class__ is LOAD_CONST:
            if cs.code.co_consts[butone.arg] is None:
                if not (cs.find_labels(-1) or cs.find_labels(-2)):
                    del cs[-2:]

def munge_code(function,code,imported_locals):
    f = Function(function)
    fcs = f.func_code.co_code

    if fcs[0].__class__ is SET_LINENO:
        del fcs[1:1 + 2*len(imported_locals)]
    else:
        del fcs[0:2*len(imported_locals)]

    # a nicety: let's see if the last couple of opcodes are necessary
    # (Python _always_ adds a LOAD_CONST None, RETURN_VALUE to the end
    # of a function, and I'd like to get rid of that if we can).

    remove_epilogue(fcs)    
    
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
            localname = f.func_code.co_varnames[op.arg]
            op.arg = imported_locals.get(localname,op.arg + len(code.co_varnames))
        elif op.op in dis.hasconst:
            op.arg = op.arg + len(code.co_consts)
        # should we hack out SET_LINENOs? doesn't seem worth it.
        i = i + 1
    
    return fcs.opcodes, retops

def expand1(func,name,macro):
    code = func.func_code
    cs = code.co_code
    count = 0
    macrocode = macro.func_code

    while count < MAX_MACRO_DEPTH:
        stack = find_function_call(func,name)

        if stack is None:
            return count

        count = count + 1

        load_func, args, function_call = \
                   stack[0], stack[1:-1], stack[-1]

        args_got = len(args)
        args_expected = macrocode.co_argcount

        if args_got > args_expected:
            raise TypeError,"too many arguments; expected %d, got %d"%(args_expected,args_got)
        elif args_got < args_expected:
            # default args?
            raise TypeError,"not enough arguments; expected %d, got %d"%(args_expected,args_got)
        
        cs.remove(load_func)

        arg_names = macrocode.co_varnames[:macrocode.co_argcount]

        import_args = []
        normal_args = []
        
        for i in range(len(arg_names)):
            if arg_names[i][0] == '.':
                import_args.append(args[i])
            else:
                normal_args.append(args[i])

        imported_locals = {}
        
        for insn in import_args:
            cs.remove(insn)
            if insn.__class__ is LOAD_GLOBAL:
                name = code.co_names[insn.arg]
                var = global_to_local(code, name)                
            elif insn.__class__ is not LOAD_FAST:
                raise TypeError, "imported arg must be local"
            else:
                var = insn.arg
            argindex = macrocode.co_argcount + import_args.index(insn)
            argname = macrocode.co_varnames[argindex]
            imported_locals[argname] = var

        local_index = len(code.co_varnames) 

        for insn in normal_args:
            new = STORE_FAST(local_index + args.index(insn))
            cs.insert(cs.index(insn)+1,new)
            labels = cs.find_labels(cs.index(new)+1)
            for label in labels:
                label.op = new

        newops, retops = munge_code(macro,code,imported_locals)

        call_index = cs.index(function_call)
        nextop = cs[call_index + 1]

        cs[call_index:call_index + 1] = newops

        for op in retops:
            if cs.index(nextop) - cs.index(op) == 1:
                cs.remove(op)
            else:
                op.label.op = nextop

    raise RuntimeError, "are we trying to expand a recursive macro here?"

def global_to_local(code, name):
    """\
internal function to make a global variable into
a local one, for the case that setq is the first
reference to a variable.
Modifies a code object in-place. 
Return value is index into variable table
    """
    cs   = code.co_code

    index = len(code.co_varnames)
    code.co_varnames.append(name)

    for i in range(len(cs)):
        op = cs[i]
        if op.__class__ not in [LOAD_GLOBAL,STORE_GLOBAL]:
            continue
        thisname = code.co_names[op.arg]
        if thisname <> name:
            continue
        if op.__class__ is LOAD_GLOBAL:
            cs[i] = LOAD_FAST(index)
        else:
            cs[i] = STORE_FAST(index)
    return index











