'''Safe execution of arbitrary code through bytecode munging

CodeBlock is a base class for bytecode munging of code strings.  Derived
classes should override 'forbid' and 'Mungers'.  The class constructor
takes a function name, a parameter string, and a function body string. It
combines the name, parameters, and body into a function (indented one
space), compiles it, and then examines its bytecode.

Any bytecode whose opcode is a key in 'forbid' with a true value may not
appear in the compiled code.

Each object in 'Mungers' is called with the code window object (at start)
and the variable name information for the function.  Mungers can use this
opportunity to examine the code and variables, and perform setup operations.
The value returned from the call is discarded if false, otherwise it is
assumed to be a collection of bytecode-specific functions.

The code window object is passed over the bytecodes, maintaining a stack
of "responsible" opcodes.  At any given position, the size of the stack
should be the same as the size of the run-time stack would be when that
part of the code is executing, and the top of the stack would have been
put there by the "responsible" opcode.

At each position, the mungers are examined to see if they have a function
corresponding to the current opcode.  If so, the function is called with
the code window object.  The function can then use the code window object to
examine or change the bytecode.

Once all processing is done, and if there have not been any errors, the
compiled, edited function is converted into a pickleable tuple, which is
stored as attribute 't' of the resulting instance.  In order for this to
work, mungers must not place unpickleable objects into the list of constants.
In order for unpickling to be robust, they should not place any function
objects there either.  If a function must be provided for use in the
bytecode, it should be loaded from the global dictionary, preferably with an
'illegal' name.
'''

import sys
from string import replace, join
from types import FunctionType
import ops, code_editor, new
from closure import bind

class Warning(Exception): pass
class ForbiddenOp(Exception): pass

general_special_globals = {}

class Munge_window:
    def __init__(self, code, use_stack):
        self.code = code
        self.opn = -1
        self.use_stack = use_stack
        if use_stack:
            self.stack = []
            self.last_empty_stack = None

    def insert_code(self, rcode, at = None):
        opn = self.opn
        # rcode is passed as a (callables, args) pair
        rcode = map(apply, rcode[0], rcode[1])
        if at is None:
            at = opn
        self.code[at + 1:at + 1] = [self.code[at]]
        self.code[at + 1:at + 1] = rcode
        del self.code[at]
        self.opn = opn + len(rcode)
        return rcode

    def set_code(self, rct = 1, rcode = ()):
        'Replace "rct" bytecodes at current position with "rcode"'
        opn = self.opn
        # rcode is passed as a (callables, args) pair
        if rcode:
            rcode = map(apply, rcode[0], rcode[1])
        self.code[opn:opn+rct] = rcode
        if self.use_stack:
            stack = self.stack
            for op in rcode:
                try:
                    op.execute(stack)
                except:
                    del stack[:]
                if not stack:
                    self.last_empty_stack = op
        self.opn = opn + len(rcode) - 1

    def advance(self):
        self.opn = opn = self.opn + 1
        code = self.code
        if opn < len(code):
            self.op = code.opcodes[opn]
            self.opname = self.op.__class__.__name__
            return 1
        elif opn == len(code):
            # Hack!
            self.op = None
            self.opname = 'finalize'
            return 1

    def do_op(self):
        if self.use_stack and self.op:
            op = self.op
            stack = self.stack
            try:
                op.execute(stack)
            except:
                del stack[:]
            if not stack:
                self.last_empty_stack = op

    def after_code_for(self, stack_idx):
        stack = self.stack
        if stack_idx < 0 and len(stack) + stack_idx < 0:
            whichop = self.last_empty_stack
            if whichop is None:
                return 0
        else:
            whichop = stack[stack_idx]
        return self.code.index(whichop)+1

    def assert_stack_size(self, size, ctxt):
        if self.use_stack and len(self.stack) != size:
            raise Warning, ('PythonMethod Bug: %s objects were on the stack '
            '%s when only %s should be.' % (len(self.stack), ctxt, size)) 

    def clear_stack(self):
        if self.use_stack:
            del self.stack[:]
            self.last_empty_stack = self.op

class CodeBlock:
    '''Compile a string containing Python code, with restrictions'''

    forbid = {}
    Mungers = ()
    globals = {'__builtins__': None}
    forbidden = "Forbidden operation %s at line %d"

    def __init__(self, src, name='<function>', filename='<string>'):
        self.f = None
        defns = {'__builtins__': None}
        self.warnings, self.errors = [], []
        try:
            exec src in defns
        except SyntaxError:
            import traceback
            self.errors = traceback.format_exception_only(SyntaxError,
                                                          sys.exc_info()[1])
            return
        for v in defns.values():
            if type(v) is FunctionType:
                block = v
                break
        else:
            raise SyntaxError, 'string did not define a function'
        # Crack open the resulting function and munge it.
        f = code_editor.Function(block)
        f.func_name = name
        f.func_globals = self.globals
        f.func_code.set_filename(filename)
        self.munge_data = {}
        self.munge(f.func_code)

        if not self.errors: self.t = f.as_tuple()

    def munge(self, fc, depth=0):
        # Recurse into nested functions first
        for subcode in fc.subcodes:
            self.munge(subcode, depth+1)
        # Make the current recursion depth accessible
        self.depth = depth
        code = fc.co_code
        warnings, errors = self.warnings, self.errors
        # Initialize the Munge objects
        mungers = []
        window = Munge_window(code, 1)
        margs = (self, window, fc)
        for M in self.Mungers:
            try:
                mungers.append(apply(M, margs))
            except Exception, e:
                errors.append(e.__class__.__name__ + ', ' + str(e))
        # Try to collect all initialization errors before failing
        if errors:
            return
        # Mungers which only perform an initial pass should return false
        mungers = filter(None, mungers)
        line = 0 ; forbid = self.forbid
        while window.advance():
            op, opname = window.op, window.opname
            if isinstance(op, ops.SET_LINENO):
                line = op.arg
                window.do_op()
            elif op and forbid.get(op.op, 0):
                errors.append(self.forbidden % (opname, line))
                window.do_op() #???
            else:
                for m in mungers:
                    handler = getattr(m, opname, None)
                    if handler:
                        try:
                            # Return true to prevent further munging
                            handled = handler(window)
                        except ForbiddenOp:
                            errors.append(self.forbidden % (opname, line))
                        except Exception, e:
                            raise
                            errors.append(e.__class__.__name__ + ', ' + str(e))
                        else:
                            if not handled:
                                continue
                        break
                else:
                    window.do_op()
    def __call__(self, *args, **kargs):
        F = code_editor.Function(self.t)
        F.func_globals = self.globals
        self.__call__ = f = F.make_function()
        return apply(f, args, kargs)

def _print_handler(printlist, *txt):
    add = printlist.append
    if len(txt):
        if printlist and printlist[-1:] != ['\n']:
            add(' ')
        add(str(txt[0]))
    else:
        add('\n')
def _join_printed(printlist):
    return join(printlist, '')
_join_printed = bind(_join_printed, join=join, map=map, str=str)

general_special_globals['$print_handler'] = _print_handler
general_special_globals['$join_printed'] = _join_printed
general_special_globals['$printed'] = None

class Printing:
    '''Intercept print statements

    Print statements are either converted to no-ops, or replaced with
    calls to a handler.  The default handler _print_handler appends the
    intended output to a list.  'printed' is made into a reserved name
    which can only be used to read the result of _join_printed.

    _print_handler and _join_printed should be provided in the global
    dictionary as $print_handler and $join_printed'''
    lfnames = (('$printed',), ('$print_handler',), ('$join_printed',))
    print_prep = ( (ops.LOAD_FAST, ops.LOAD_FAST), (lfnames[1], lfnames[0]) )
    get_printed = ( (ops.LOAD_FAST, ops.LOAD_FAST, ops.CALL_FUNCTION),
                    (lfnames[2], lfnames[0], (1,)) )
    init_printed = ( (ops.BUILD_LIST, ops.STORE_GLOBAL), 
                      ((0,), lfnames[0]) )
    make_local = (ops.LOAD_GLOBAL, ops.STORE_FAST)
    call_print1 = ( (ops.CALL_FUNCTION, ops.POP_TOP), ((1,), ()) )
    call_print2 = ( (ops.CALL_FUNCTION, ops.POP_TOP), ((2,), ()) )
    
    def __init__(self, cb, w, fc):
        if 'printed' in fc.co_varnames:
            raise SyntaxError, '"printed" is a reserved word.'
        self.warnings, self.depth = cb.warnings, cb.depth
        self.md = cb.munge_data['Printing'] = cb.munge_data.get('Printing', {})
        self.names_used = names_used = {}
        names = fc.co_names
        if 'printed' in names:
            names_used[0] = names.index('printed')
            names_used[2] = 1
        else:
            self.LOAD_GLOBAL = None
    def finalize(self, w):
        names_used = self.names_used
        if names_used:
            # Load special names used by the function (and $printed always)
            ln = self.lfnames
            names_used[0] = 1
            for i in names_used.keys():
                w.insert_code( (self.make_local, (ln[i], ln[i])), 0)
            # Inform higher-level mungers of name usage
            self.md.update(names_used)
        if self.md and self.depth == 0:
            # Initialize the $printed variable in the base function
            w.insert_code(self.init_printed, 0)
            if not self.md.has_key(2):
                self.warnings.append(
                "Prints, but never reads 'printed' variable.")

    def PRINT_ITEM(self, w):
        # Load the printing function before the code for the operand.
        w.insert_code(self.print_prep, w.after_code_for(-2))
        w.assert_stack_size(1, "at a 'print' statement")
        # Instead of printing, call our function and discard the result.
        w.set_code(1, self.call_print2)
        self.names_used[1] = 1
        return 1
    
    def PRINT_NEWLINE(self, w):
        w.assert_stack_size(0, "at a 'print' statement")
        w.insert_code(self.print_prep)
        w.set_code(1, self.call_print1)
        self.names_used[1] = 1
        return 1
    
    def LOAD_GLOBAL(self, w):
        if w.op.arg==self.names_used[0]:
            # Construct the print result instead of getting non-existent var.
            w.set_code(1, self.get_printed)
            return 1

general_special_globals['$loop_watcher'] = lambda: None

class LoopLimits:
    '''Try to prevent "excessive" iteration and recursion

    Loop ends, 'continue' statements, and function entry points all
    call a hook function, which can keep track of iteration and call
    depth, and raise an exception to terminate processing.

    The hook function should be provided in the global
    dictionary as $loop_watcher'''
    lwname = ('$loop_watcher',)
    notify_watcher = ( (ops.LOAD_FAST, ops.CALL_FUNCTION, ops.POP_TOP),
                       (lwname, (0,), ()) )
    make_local = (ops.LOAD_GLOBAL, ops.STORE_FAST)
    
    def __init__(self, cb, w, fc):
        pass

    def finalize(self, w):
        # Localize the watcher, and call it.
        w.insert_code(self.notify_watcher, 0)
        w.insert_code( (self.make_local, (self.lwname, self.lwname)), 0)

    def JUMP_ABSOLUTE(self, w):
        # Call the watcher before looping
        w.insert_code(self.notify_watcher)
        return 1
    
def PublicNames(cb, w, fc):
    '''Restrict access to all but public names

    Forbid use of any multi-character name starting with _
    '''
    protected = []
    for name in fc.co_names:
        if name[:1]=='_' and len(name)>1:
            protected.append(name)
    if protected:
        raise SyntaxError, ('Names starting with "_" are not allowed (%s).'
                            % join(protected, ', '))

class AllowMapBuild:
    '''Allow literal mappings to be constructed unmunged

    Optimize construction of literal dictionaries, which requires
    STORE_SUBSCR, by checking the stack.'''
    def __init__(self, cb, w, fc):
        pass
    def STORE_SUBSCR(self, w):
        if isinstance(w.stack[-2], ops.BUILD_MAP):
            w.do_op()
            return 1

def _get_call(w):
    load_guard = ((ops.LOAD_FAST, ops.LOAD_ATTR), (('$guard',), (guard,)))
    # Load the binary guard function before its parameters are computed.
    iops = w.insert_code(load_guard, w.after_code_for(-3))
    # Fix the execution stack to refer to the loaded function.
    if w.use_stack: w.stack[-2:-2] = iops[1:]
    # Call guard function instead of performing binary op
    w.set_code(1, cf2)
    return 1
def _SLICE(w):
    load_guard = ((ops.LOAD_FAST, ops.LOAD_ATTR, ops.ROT_TWO),
                  (('$guard',), ('getslice',), ()))
    # Load the Slice guard and switch it with the argument.
    w.insert_code(load_guard, w.opn+1)
    # Call the slice guard after performing the slice.
    w.insert_code(cf1, w.opn+4)
    return 1

# Code for calling a function with 1 or 2 parameters, respectively
cf1 = ((ops.CALL_FUNCTION,), ((1,),))
cf2 = ((ops.CALL_FUNCTION,), ((2,),))

class _GuardedOps:
    def __call__(self, cb, w, fc):
        g = self.guard_name
        localize_guard = ( (ops.LOAD_GLOBAL, ops.STORE_FAST),
                           ((g,),(g,)) )
        # Insert setup code; no need to fix stack
        w.insert_code(localize_guard, 0)
        return self

def GuardedBinaryOps(guards):
    '''Allow operations to be Guarded, by replacing them with guard calls.

    Construct a munging object which will replace specific opcodes with
    calls to methods of a guard object.  The guard object must appear in
    the global dictionary as $guard.'''
    gops = _GuardedOps()
    gops.guard_name = '$guard'
    opmap = ( ('mul', 'BINARY_MULTIPLY')
             ,('div', 'BINARY_DIVIDE')
             ,('power', 'BINARY_POWER') )
    for guard, defname in opmap:
        if hasattr(guards, guard):
            setattr(gops, defname, bind(_get_call, guard=guard, cf2=cf2))
    if hasattr(guards, 'getslice'):
        gops.SLICE_3 = gops.SLICE_2 = gops.SLICE_1 = gops.SLICE_0 = bind(_SLICE, cf1=cf1)
    return gops

def _wrap(w):
    load_guard = ((ops.LOAD_FAST,), ((guard,),))
    # Load the guard function before the guarded object, call after.
    w.insert_code(load_guard, w.after_code_for(spos - 1))
    if spos == 0:
        w.set_code(0, cf1)
    else:
        iops = w.insert_code(cf1, w.after_code_for(spos))
        # Fix the execution stack.
        if w.use_stack: w.stack[spos] = iops[0]

def _WriteGuardWrapper():
    def model_handler(self, *args):
        try:
            f = getattr(self.__dict__['_ob'], secattr)
        except AttributeError:
            raise TypeError, error_msg
        apply(f, args)
    d = {}
    for name, error_msg in (
        ('setitem', 'object does not support item assignment'),
        ('delitem', 'object does not support item deletion'),
        ('setattr', 'attribute-less object (assign or del)'),
        ('delattr', 'attribute-less object (assign or del)'),
        ('setslice', 'object does not support slice assignment'),
        ('delslice', 'object does not support slice deletion'),
        ):
        fname = '__%s__' % name
        d[fname] = bind(model_handler, fname,
                        secattr='__guarded_%s__' % name,
                        error_msg=error_msg)
    return new.classobj('Wrapper', (), d)

def _WriteGuard(ob):
    if type(ob) in safetypes or getattr(ob, '_guarded_writes', None):
        return ob
    w = Wrapper()
    w.__dict__['_ob'] = ob
    return w

WriteGuard = bind(_WriteGuard, safetypes=(type([]), type({})),
                  Wrapper=_WriteGuardWrapper())

def RedirectWrites():
    '''Redirect STORE_* and DELETE_* on objects to methods

    Construct a munging object which will wrap all objects which are the
    target of a STORE or DELETE op by passing them to a guard function.
    The guard function must appear in the global dictionary as $write_guard.'''
    gops = _GuardedOps()
    gops.guard_name = guard = '$write_guard'
    opmap = ( ('STORE_SUBSCR', -2)
             ,('DELETE_SUBSCR', -2)
             ,('STORE_ATTR', -1)
             ,('DELETE_ATTR', -1)
             ,('STORE_SLICE_0', -1)
             ,('STORE_SLICE_1', -2)
             ,('STORE_SLICE_2', -2)
             ,('STORE_SLICE_3', -3)
             ,('DELETE_SLICE_0', -1)
             ,('DELETE_SLICE_1', -2)
             ,('DELETE_SLICE_2', -2)
             ,('DELETE_SLICE_3', -3) )
    for defname, spos in opmap:
        setattr(gops, defname, bind(_wrap, spos=spos, cf2=cf2, guard=guard))
    return gops
        
def _ReadGuard(ob):
    if type(ob) in safetypes or hasattr(ob, '_guarded_reads'):
        return ob
    w = Wrapper()
    w.__dict__['_ob'] = ob
    return w

ReadGuard = bind(_ReadGuard, safetypes=(type(''), type([]), type({}),
                                        type(()), type(0), type(1.0),) )

def RedirectReads():
    '''Redirect LOAD_* on objects to methods

    Construct a munging object which will wrap all objects which are the
    target of a LOAD op by passing them to a guard function.
    The guard function must appear in the global dictionary as $read_guard.'''
    gops = _GuardedOps()
    gops.guard_name = guard = '$read_guard'
    opmap = ( ('BINARY_SUBSCR', -2)
             ,('LOAD_ATTR', -1)
             ,('SLICE_0', -1)
             ,('SLICE_1', -2)
             ,('SLICE_2', -2)
             ,('SLICE_3', -3) )
    for defname, spos in opmap:
        setattr(gops, defname, bind(_wrap, spos=spos, cf2=cf2, guard=guard))
    return gops

class SafeBlock(CodeBlock):
    forbid = {ops.STORE_NAME.op: 1, ops.DELETE_NAME.op: 1}
    for opclass in ops._bytecodes.values():
        if forbid.get(opclass.op, 1):
            opname = opclass.__name__
            if opname[:5] == 'EXEC_':
                forbid[opclass.op] = 1
    Mungers = [Printing, PublicNames, AllowMapBuild]

def UntupleFunction(t, special_globals, **globals):
    import new
    globals.update(general_special_globals)
    globals.update(special_globals)
    globals['global_exists'] = defined = globals.has_key
    if not defined('__builtins__'):
        globals['__builtins__'] = {}

    t = list(t)
    # Handle nested functions and lambdas
    t_code = t[2]
    if len(t_code) == 13:
       sub_codes = [t_code]
       funstack = [sub_codes]
       while funstack:
         if len(t_code) == 13:
           # This has nested code objects, so make it mutable
           sub_codes[0] = t_parent = t_code = list(t_code)
           # Put the list of nested codes on the stack for processing
           sub_codes = list(t_code.pop())
           funstack.append(sub_codes)
         else:
           # This code tuple is fully processed, so untuple it
           func_code = apply(new.code, tuple(t_code))
           # Find the first placeholder () in the parent's constants
           t_consts = list(t_parent[5])
           # Replace the placeholder with the code object
           t_consts[t_consts.index(())] = func_code
           t_parent[5] = tuple(t_consts)
           # Clear it from the stack
           del sub_codes[0]
         # Get the next code tuple to process
         if not sub_codes:
           # Back up one level
           funstack.pop()
           sub_codes = funstack[-1]
           if len(funstack) > 1:
               t_parent = funstack[-2][0]
           else:
               funstack = None
         t_code = sub_codes[0]
    f = new.function(apply(new.code, tuple(t_code)), globals, t[0])
    f.func_defaults = t[3] and tuple(t[3])
    f.func_doc = t[1]
    return f

def test(p, c):
    sb = SafeBlock('f', p, c)
    print sb.errors, sb.warnings
    f = code_editor.Function(sb.t)
    for c in f.func_code.co_code:
        print c
    for subcode in f.func_code.subcodes:
        for c in subcode.co_code:
            print ' ', c
    return sb

if __name__ == '__main__':    
        sb = test('x', '''\
print x
def plus1(x):
  print x+1
plus1(x)
return printed''')
        f = UntupleFunction(sb.t, {})
        #from dis import dis
        #dis(f)
        print f(2),
        print f(3),

