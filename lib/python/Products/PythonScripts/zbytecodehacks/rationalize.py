import code_editor
from ops import *
import operator

CONDJUMP = [ JUMP_IF_TRUE, JUMP_IF_FALSE ]
UNCONDJUMP = [ JUMP_FORWARD, JUMP_ABSOLUTE ]
UNCOND = UNCONDJUMP + [ BREAK_LOOP, STOP_CODE, RETURN_VALUE, \
    RAISE_VARARGS ]
PYBLOCK = [ SETUP_LOOP, SETUP_EXCEPT, SETUP_FINALLY ]
PYENDBLOCK = [ POP_BLOCK ]

binaryops = {
    'BINARY_ADD': operator.add,
    'BINARY_SUBTRACT': operator.sub,
    'BINARY_MULTIPLY': operator.mul,
    'BINARY_DIVIDE': operator.div,
    'BINARY_MODULO': operator.mod,
    'BINARY_POWER': pow,
    'BINARY_LSHIFT': operator.lshift,
    'BINARY_RSHIFT': operator.rshift,
    'BINARY_AND': operator.and_,
    'BINARY_OR': operator.or_,
    'BINARY_XOR': operator.xor
  }

unaryops = {
    'UNARY_POS': operator.pos,
    'UNARY_NEG': operator.neg,
    'UNARY_NOT': operator.not_
  }

def rationalize(code):
    calculateConstants(code)
    strip_setlineno(code)
    simplifyjumps(code)
    removeconstjump(code)
    simplifyjumps(code)
    eliminateUnusedNames(code)
    eliminateUnusedLocals(code)

def calculateConstants(co):
    """Precalculate results of operations involving constants."""
    
    cs = co.co_code
    cc = co.co_consts
    
    stack = []
    i = 0
    while i < len(cs):
        op = cs[i]
        if binaryops.has_key(op.__class__.__name__):
            if stack[-1].__class__ is stack[-2].__class__ is LOAD_CONST:
                arg1 = cc[stack[-2].arg]
                arg2 = cc[stack[-1].arg]
                result = binaryops[op.__class__.__name__](arg1,arg2)

                if result in cc:
                    arg = cc.index(result)
                else:
                    arg = len(cc)
                    cc.append(result)
                    
                cs.remove(stack[-2])
                cs.remove(stack[-1])
                i = i - 2
                cs[i] = LOAD_CONST(arg)

                stack.pop()
                stack.pop()
                stack.append(cs[i])
            else:
                op.execute(stack)
        elif unaryops.has_key(op.__class__.__name__):
            if stack[-1].__class__ is LOAD_CONST:
                arg1 = cc[stack[-1].arg]
                result = unaryops[op.__class__.__name__](arg1)

                if result in cc:
                    arg = cc.index(result)
                else:
                    arg = len(cc)
                    cc.append(result)
                cs.remove(stack[-1])
                i = i - 1
                cs[i] = LOAD_CONST(arg)

                stack.pop()
                stack.append(cs[i])
            else:
                op.execute(stack)
        else:
            # this is almost certainly wrong
            try:
                op.execute(stack)
            except: pass
        i = i + 1

def strip_setlineno(co):
    """Take in an EditableCode object and strip the SET_LINENO bytecodes"""
    i = 0
    while i < len(co.co_code):
        op = co.co_code[i]
        if op.__class__ is SET_LINENO:
            co.co_code.remove(op)
        else:
            i = i + 1

def simplifyjumps(co):
    cs = co.co_code
    
    i = 0
    pyblockstack = [None]
    loopstack = [None]
    trystack = [None]
    firstlook = 1

    while i < len(cs):
        op = cs[i]

        # new pyblock?
        if firstlook:
            if op.__class__ in PYBLOCK:
                pyblockstack.append(op)
                if op.__class__ is SETUP_LOOP:
                    loopstack.append(op.label.op)
                else:
                    trystack.append(op.label.op)
            # end of pyblock?
            elif op.__class__ == POP_BLOCK:
                op2 = pyblockstack.pop()
                if op2.__class__ == SETUP_LOOP:
                    loopstack.pop()
                else:
                    trystack.pop()

        # Is the code inaccessible
        if i >= 1:
            if cs[i-1].__class__ in UNCOND and not (cs.find_labels(i) or \
                    op.__class__ in PYENDBLOCK):
                cs.remove(op)
                firstlook = 1
                continue

            # are we jumping from the statement before?
            if cs[i-1].__class__ in UNCONDJUMP:
                if cs[i-1].label.op == op:
                    cs.remove(cs[i-1])
                    firstlook = 1
                    continue

            # break before end of loop?
            elif cs[i-1].__class__ == BREAK_LOOP:
                if op.__class__ == POP_BLOCK:
                    cs.remove(cs[i-1])
                    firstlook = 1
                    continue

        # Do we have an unconditional jump to an unconditional jump?
        if op.__class__ in UNCONDJUMP:
            if op.label.op.__class__ in UNCONDJUMP:
                refop = op.label.op
                if op.__class__ == JUMP_FORWARD:
                    newop = JUMP_ABSOLUTE()
                    newop.label.op = refop.label.op
                    cs[i] = newop
                else: 
                    op.label.op = refop.label.op
                firstlook = 0
                continue

        # Do we have a conditional jump to a break?
        if op.__class__ in CONDJUMP and loopstack[-1]:
            destindex = cs.index(op.label.op)
            preendindex = cs.index(loopstack[-1])-2
            if cs[i+2].__class__ == BREAK_LOOP and cs[preendindex].__class__ \
                    == POP_TOP:
                if op.__class__ == JUMP_IF_FALSE:
                    newop = JUMP_IF_TRUE()
                else:
                    newop = JUMP_IF_FALSE()
                newop.label.op = cs[preendindex]
                cs[i] = newop
                cs.remove(cs[i+1])
                cs.remove(cs[i+1])
                cs.remove(cs[i+1])
                firstlook = 0
                continue
            elif cs[destindex+1].__class__ == BREAK_LOOP and \
                    cs[preendindex].__class__ == POP_TOP:
                op.label.op = cs[preendindex]
                cs.remove(cs[destindex])
                cs.remove(cs[destindex])
                cs.remove(cs[destindex])
                firstlook = 0
                continue

        firstlook = 1
        i = i+1


def removeconstjump(co):
    cs = co.co_code
    cc = co.co_consts
    
    i = 0
    while i < len(cs):
        op = cs[i]
        if op.__class__ in CONDJUMP and cs[i-1].__class__ == LOAD_CONST:
            if (op.__class__ == JUMP_IF_FALSE and cc[cs[i-1].arg]) or \
               (op.__class__ == JUMP_IF_TRUE and not cc[cs[i-1].arg]):
                cs.remove(cs[i-1])
                cs.remove(cs[i-1])
                cs.remove(cs[i-1])
                i = i-2
            else:
                cs.remove(cs[i-1])
                cs.remove(cs[i])
                newop = JUMP_FORWARD()
                newop.label.op = cs[cs.index(op.label.op)+1]
                cs[i-1] = newop
                i = i-1
        i = i+1

def eliminateUnusedNames(code):
    used_names = {}

    for op in code.co_code:
        if op.has_name():
            if hasattr(op,"arg"):
                arg = op.arg
            else:
                arg = op.arg = code.name_index(op.name)
            used_names[arg] = 1

    used_names = used_names.keys()
    used_names.sort()
    name_mapping = {}

    for i in range(len(used_names)):
        name_mapping[used_names[i]]=i

    newnames = []
    for i in range(len(code.co_names)):
        if i in used_names:
            newnames.append(code.co_names[i])
    code.co_names = newnames

    for op in code.co_code:
        if op.has_name():
            op.arg = name_mapping[op.arg]

def eliminateUnusedLocals(code):
    used_names = {}

    for op in code.co_code:
        if op.has_local():
            if hasattr(op,"arg"):
                arg = op.arg
            else:
                arg = op.arg = code.local_index(op.name)
            used_names[arg] = 1

    used_names = used_names.keys()
    used_names.sort()
    name_mapping = {}

    for i in range(len(used_names)):
        name_mapping[used_names[i]]=i

    newnames = []
    for i in range(len(code.co_varnames)):
        if i in used_names:
            newnames.append(code.co_varnames[i])
    code.co_varnames = newnames

    for op in code.co_code:
        if op.has_local():
            op.arg = name_mapping[op.arg]
    
    
                
