from code_editor import Function

from ops import *

def find_function_call(infunc,calledfuncname, allowkeywords=0, startindex=0):
    i = startindex
    code = infunc.func_code
    cs = code.co_code

    def match(op,name = calledfuncname):
        return getattr(op,'name',None) == name

    while i < len(cs):
        op = code.co_code[i]
        if match(op):
            try:
                if allowkeywords:
                    return simulate_stack_with_keywords(code,i)
                else:
                    return simulate_stack(code,i)
            except:
                i = i + 1
        i = i + 1
    if allowkeywords:
        return None,0
    else:
        return None
    
def call_stack_length_usage(arg):
    num_keyword_args=arg>>8
    num_regular_args=arg&0xFF
    return 2*num_keyword_args + num_regular_args

def simulate_stack(code,index_start):
    stack = []
    cs = code.co_code
    i, n = index_start, len(cs)
    
    while i < n:
        op = cs[i]
        if op.__class__ is CALL_FUNCTION and op.arg+1==len(stack):
            stack.append(op)
            return stack
        elif op.is_jump():
            i = cs.index(op.label.op)+1
        else:
            op.execute(stack)
            i = i + 1
    raise "no call found!"

def simulate_stack_with_keywords(code,index_start):
    stack = []
    cs = code.co_code
    i, n = index_start, len(cs)
    
    while i < n:
        op = cs[i]
        if op.__class__ is CALL_FUNCTION \
           and call_stack_length_usage(op.arg)+1==len(stack):
            stack.append(op)
            return stack, op.arg>>8
        elif op.is_jump():
            i = cs.index(op.label.op)+1
        else:
            op.execute(stack)
            i = i + 1
    raise "no call found!"
