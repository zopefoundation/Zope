from code_editor import Function
from ops import *
import dis,new,string

PRECONDITIONS  = 1
POSTCONDITIONS = 2
INVARIANTS     = 4
EVERYTHING     = PRECONDITIONS|POSTCONDITIONS|INVARIANTS

if __debug__:
    __strength__ = PRECONDITIONS|POSTCONDITIONS
else:
    __strength__ = 0

# TODO: docs, sort out inheritance.

if __debug__:
    def add_contracts(target_class,contract_class,strength=None):
        if strength is None:
            strength = __strength__

        newmethods = {}
        contractmethods = contract_class.__dict__
        if strength & INVARIANTS:
            inv = contractmethods.get("class_invariants",None)

        for name, meth in target_class.__dict__.items():
            if strength & PRECONDITIONS:
                pre = contractmethods.get("pre_"+name,None)
                if pre is not None:
                    meth = add_precondition(meth,pre)
            if strength & POSTCONDITIONS:
                post = contractmethods.get("post_"+name,None)
                if post is not None:
                    meth = add_postcondition(meth,post)
            if (strength & INVARIANTS) and inv \
               and type(meth) is type(add_contracts):
                if name <> '__init__':
                    meth = add_precondition(meth,inv)
                meth = add_postcondition(meth,inv)
            newmethods[name] = meth

        return new.classobj(target_class.__name__,
                            target_class.__bases__,
                            newmethods)

    def add_precondition(meth,cond):
        meth  = Function(meth)
        cond  = Function(cond)

        mcs = meth.func_code.co_code
        ccs = cond.func_code.co_code

        nlocals = len(meth.func_code.co_varnames)
        nconsts = len(meth.func_code.co_consts)
        nnames  = len(meth.func_code.co_names)

        nargs   = meth.func_code.co_argcount

        retops = []

        for op in ccs:
            if op.__class__ is RETURN_VALUE:
                # RETURN_VALUEs have to be replaced by JUMP_FORWARDs
                newop = JUMP_FORWARD()
                ccs[ccs.index(op)] = newop
                retops.append(newop)
            elif op.op in dis.hasname:
                op.arg = op.arg + nnames
            elif op.op in dis.haslocal:
                if op.arg >= nargs:
                    op.arg = op.arg + nlocals
            elif op.op in dis.hasconst:
                op.arg = op.arg + nconsts

        new = POP_TOP()
        mcs.insert(0,new)
        mcs[0:0] = ccs.opcodes
        for op in retops:
            op.label.op = new

        meth.func_code.co_consts.extend(cond.func_code.co_consts)
        meth.func_code.co_varnames.extend(cond.func_code.co_varnames)
        meth.func_code.co_names.extend(cond.func_code.co_names)

        return meth.make_function()

    def add_postcondition(meth,cond):
        """ a bit of a monster! """
        meth  = Function(meth)
        cond  = Function(cond)

        mcode = meth.func_code
        ccode = cond.func_code

        mcs = mcode.co_code
        ccs = ccode.co_code

        nlocals = len(mcode.co_varnames)
        nconsts = len(mcode.co_consts)
        nnames  = len(mcode.co_names)

        nargs   = ccode.co_argcount

        cretops = []

        Result_index = len(meth.func_code.co_varnames)

        mcode.co_varnames.append('Result')

        old_refs = find_old_refs(cond)

        for op in ccs:
            if op.__class__ is RETURN_VALUE:
                newop = JUMP_FORWARD()
                ccs[ccs.index(op)] = newop
                cretops.append(newop)
            elif op.op in dis.hasname:
                if cond.func_code.co_names[op.arg] == 'Result' \
                   and op.__class__ is LOAD_GLOBAL:
                    ccs[ccs.index(op)] = LOAD_FAST(Result_index)
                else:
                    op.arg = op.arg + nnames
            elif op.op in dis.haslocal:
                if op.arg >= nargs:
                    op.arg = op.arg + nlocals + 1 # + 1 for Result
            elif op.op in dis.hasconst:
                op.arg = op.arg + nconsts

        # lets generate the prologue code to save values for `Old'
        # references and point the LOAD_FASTs inserted by
        # find_old_refs to the right locations.

        prologue = []

        for ref, load_op in old_refs:
            if ref[0] in mcode.co_varnames:
                prologue.append(LOAD_FAST(mcode.co_varnames.index(ref[0])))
            else:
                prologue.append(LOAD_GLOBAL(mcode.name_index(ref[0])))
            for name in ref[1:]:
                prologue.append(LOAD_ATTR(mcode.name_index(name)))
            lname = string.join(ref,'.')
            lindex = len(mcode.co_varnames)
            mcode.co_varnames.append(lname)
            prologue.append(STORE_FAST(lindex))
            load_op.arg = lindex

        mcs[0:0] = prologue

        mretops = []

        for op in mcs:
            if op.__class__ is RETURN_VALUE:
                newop = JUMP_FORWARD()
                mcs[mcs.index(op)] = newop
                mretops.append(newop)

        n = len(mcs)

        # insert the condition code
        mcs[n:n] = ccs.opcodes

        # store the returned value in Result
        store_result = STORE_FAST(Result_index)
        mcs.insert(n, store_result)

        # target the returns in the method to this store
        for op in mretops:
            op.label.op = store_result

        # the post condition will leave a value on the stack; lose it.
        # could just strip off the LOAD_CONST & RETURN_VALLUE at the
        # end of the function and scan for RETURN_VALUES in the
        # postcondition as a postcondition shouldn't be returning
        # things (certainly not other than None).
        new = POP_TOP()
        mcs.append(new)

        # redirect returns in the condition to the POP_TOP just
        # inserted...
        for op in cretops:
            op.label.op = new

        # actually return Result...
        mcs.append(LOAD_FAST(Result_index))
        mcs.append(RETURN_VALUE())

        # and add the new constants and names (to avoid core dumps!)
        mcode.co_consts  .extend(ccode.co_consts  )
        mcode.co_varnames.extend(ccode.co_varnames)
        mcode.co_names   .extend(ccode.co_names   )

        return meth.make_function()

    def find_old_refs(func):
        chaining = 0
        refs     = []
        ref      = []
        code     = func.func_code
        cs       = code.co_code

        i = 0
        
        while i < len(cs):
            op=cs[i]
            if not chaining:
                if op.__class__ is LOAD_GLOBAL:
                    if code.co_names[op.arg]=='Old':
                        chaining=1
            else:
                if op.__class__ is LOAD_ATTR:
                    ref.append(code.co_names[op.arg])
                else:
                    newop = LOAD_FAST(0)
                    cs[i-len(ref)-1:i] = [newop]
                    i = i - len(ref)
                    refs.append((ref,newop))
                    ref = []
                    chaining = 0
            i=i+1

        return refs
else: # if not __debug__
    def add_contracts(target_class,contracts_class):
        return target_class
    
# example

class Uncontracted:
    def __init__(self,x,y):
        self.x=x
        self.y=y
    def do(self):
#        self.x = self.x + 1 # sneaky!
        return self.x/self.y

class Contracts:
    def pre___init__(self,x,y):
        assert y <> 0
    def post_do(self):
        assert Old.self.x == self.x
        assert Old.self.y == self.y
        assert Result > 0, "Result was %s"%`Result`
    def class_invariants(self):
        assert self.x > 0

Contracted = add_contracts(Uncontracted,Contracts)



