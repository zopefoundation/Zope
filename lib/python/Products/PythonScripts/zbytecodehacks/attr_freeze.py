from code_editor import Function
from ops import LOAD_GLOBAL, LOAD_ATTR, LOAD_CONST

def freeze_one_attr(cs,code,attr,value):
    looking_for=0
    is_global=1
    inserted=0

    i = 0
    while i < len(cs):
        op=cs[i]
        if is_global:
            if op.__class__ is LOAD_GLOBAL:
                if code.co_names[op.arg]==attr[looking_for]:
                    looking_for=looking_for+1
                    is_global=0
        else:
            if op.__class__ is LOAD_ATTR \
               and code.co_names[op.arg]==attr[looking_for]:
                looking_for=looking_for+1
                if looking_for == len(attr):
                    inserted=1
                    newop=LOAD_CONST(len(code.co_consts))
                    cs[i-len(attr)+1:i+1]=[newop]
                    i=i-len(attr)
                    looking_for=0
                    is_global=1
            else:
                looking_for=0
                is_global=1
        i=i+1

    if inserted:
        code.co_consts.append(value)
    return cs
    
class Ref:
    def __init__(self,name=()):
        self.name=name
    def __getattr__(self,attr):
        return Ref(self.name+(attr,))
    def __call__(self):
        return self.name
    def __repr__(self):
        return `self.name`

def freeze_attrs(func,*vars):
    func=Function(func)
    code=func.func_code
    cs=code.co_code

    if len(vars)%2 <> 0:
        raise TypeError, "wrong number of arguments"

    for i in range(0,len(vars),2):
        freeze_one_attr(cs,code,vars[i](),vars[i+1])

    return func.make_function()
