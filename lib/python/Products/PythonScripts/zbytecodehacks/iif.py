from code_editor import Function
from ops import *
from find_function_call import find_function_call

def iifize(func):
    func = Function(func)
    cs = func.func_code.co_code

    while 1:
        stack = find_function_call(func,"iif")

        if stack is None:
            break

        load, test, consequent, alternative, call = stack

        cs.remove(load)

        jump1 = JUMP_IF_FALSE(alternative)
        cs.insert(cs.index(test)+1,jump1)

        jump2 = JUMP_FORWARD(call)
        cs.insert(cs.index(consequent)+1,jump2)
        
        cs.remove(call)

    cs = None
    
    return func.make_function()
