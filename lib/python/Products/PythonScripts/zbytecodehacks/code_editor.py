# the third attempt; maybe it'll work sometime.

# interface I want:
# mc=MutableCode(<code object>)
# behaves like list of opcodes, eg
# len(mc) => number of bytecodes in code
# mc[i] returns some representation of the ith opcode
# mc.assemble() => codestring, or maybe code object.

import types,StringIO,struct,new

import ops
from cyclehandle import CycleHandle

class CodeString(CycleHandle):
    def __init__(self,cs=None,bytecodes=None):
	self._set_workers(CodeStringWorker(cs, bytecodes))
        
class CodeStringWorker:
    def __init__(self,cs,bytecodes):
        self.labels=[]
        self.byte2op={}
        self.opcodes=[]

        if bytecodes is None:
            bytecodes = ops._bytecodes
        
        if type(cs) is type(""):
            self.disassemble_no_code(cs,bytecodes)
        else:
            self.disassemble(cs,bytecodes)
    def disassemble(self,code,bytecodes):
        self.labels = []
        self.byte2op = {}
        self.opcodes = []
        self.code = code

        cs=StringIO.StringIO(code.co_code)
        i, op, n = 0, 0, len(code.co_code)
        
        while i < n:
            self.byte2op[i]=op
            byte=cs.read(1)
            self.opcodes.append(bytecodes[byte](cs,self))
            i = cs.tell()
            op = op + 1

        del self.code

        for label in self.labels:
            label.resolve(self)
    def disassemble_no_code(self,codestring,bytecodes):
        self.labels = []
        self.byte2op = {}
        self.opcodes = []

        cs=StringIO.StringIO(codestring)
        i, op, n = 0, 0, len(codestring)
        
        while i < n:
            self.byte2op[i]=op
            byte=cs.read(1)
            self.opcodes.append(bytecodes[byte](cs,self))
            i = cs.tell()
            op = op + 1

        for label in self.labels:
            label.resolve(self)            
    def add_label(self,label):
        self.labels.append(label)
    def find_labels(self,index):
        labelled=self.opcodes[index]
        pointees=[]
        for l in self.labels:
            if l.op == labelled:
                pointees.append(l)
        return pointees
    def __getitem__(self,index):
        return self.opcodes[index]
    def __setitem__(self,index,value):
        # find labels that point to the removed opcode
        pointees=self.find_labels(index)
        if self.opcodes[index].is_jump():
            self.labels.remove(self.opcodes[index].label)
        self.opcodes[index]=value
        for l in pointees:
            l.op=value
        if value.is_jump():
            self.labels.append(value.label)
    def __delitem__(self,index):
        # labels that pointed to the deleted item get attached to the
        # following insn (unless it's the last insn - in which case I
        # don't know what you're playing at, but I'll just point the
        # label at what becomes the last insn)
        pointees=self.find_labels(index)
        if index + 1 == len(self.opcodes):
            replacement = self.opcodes[index]
        else:
            replacement = self.opcodes[index + 1]
        for l in pointees:
            l.op=replacement
        going=self.opcodes[index]
        if going.is_jump():
            self.labels.remove(going.label)
        del self.opcodes[index]
    def __getslice__(self,lo,hi):
        return self.opcodes[lo:hi]
    def __setslice__(self,lo,hi,values):
        # things that point into the block being stomped on get
        # attached to the start of the new block (if there are labels
        # pointing into the block, rather than at its start, a warning
        # is printed, 'cause that's a bit dodgy)
        pointees=[]
        opcodes = self.opcodes
        indices=range(len(opcodes))[lo:hi]
        for i in indices:
            if opcodes[i].is_jump():
                self.labels.remove(opcodes[i].label)
            p=self.find_labels(i)
            if p and i <> lo:
                print "What're you playing at?"
            pointees.extend(p)
        codes = []
        for value in values:
            if value.is_jump():
                self.labels.append(value.label)
            codes.append(value)
        opcodes[lo:hi]=codes
        replacement = opcodes[min(lo, len(opcodes)-1)]
        for l in pointees:
            l.op = replacement
    def __delslice__(self,lo,hi):
        self.__setslice__(lo, hi, [])
    def __len__(self):
        return len(self.opcodes)
    def append(self,value):
        self.opcodes.append(value)
        if value.is_jump():
            self.labels.append(value.label)
    def insert(self,index,value):
        self.opcodes.insert(index,value)     
        if value.is_jump():
            self.labels.append(value.label)
    def remove(self,x):
        del self[self.opcodes.index(x)]
    def index(self,x):
        return self.opcodes.index(x)
    def assemble(self):
        out=StringIO.StringIO()
        for i in self:
            i.byte=out.tell()
            out.write(i.assemble(self))
        for l in self.labels:
            l.write_refs(out)
        out.seek(0)
        return out.read()
    def set_code(self, code):
        self.code = code

class EditableCode(CycleHandle):
    def __init__(self,code=None):
	self._set_workers(EditableCodeWorker(code))    

class EditableCodeWorker:
    # bits for co_flags
    CO_OPTIMIZED   = 0x0001
    CO_NEWLOCALS   = 0x0002
    CO_VARARGS     = 0x0004
    CO_VARKEYWORDS = 0x0008

    AUTO_RATIONALIZE = 0
    
    def __init__(self,code=None):
        if code is None:
            self.init_defaults()
        elif type(code) in (type(()), type([])):
            self.init_tuple(code)
        else:
            self.init_code(code)
        self.co_code.set_code(self)
    def name_index(self,name):
        if name not in self.co_names:
            self.co_names.append(name)
        return self.co_names.index(name)
    def local_index(self,name):
        if name not in self.co_varnames:
            self.co_varnames.append(name)
        return self.co_varnames.index(name)
    def rationalize(self):
        from rationalize import rationalize
        rationalize(self)
    def init_defaults(self):
        self.co_argcount = 0
        self.co_stacksize = 0 # ???
        self.co_flags = 0 # ???
        self.co_consts = []
        self.co_names = []
        self.co_varnames = []
        self.co_filename = '<edited code>'
        self.co_name = 'no name'
        self.co_firstlineno = 0
        self.co_lnotab = '' # ???
        self.co_code = CodeString()
        self.subcodes = []
    def init_code(self,code):
        self.co_argcount = code.co_argcount
        self.co_stacksize = code.co_stacksize
        self.co_flags = code.co_flags
        self.co_consts = consts = list(code.co_consts)
        self.co_names = list(code.co_names)
        self.co_varnames = list(code.co_varnames)
        self.co_filename = code.co_filename
        self.co_name = code.co_name
        self.co_firstlineno = code.co_firstlineno
        self.co_lnotab = code.co_lnotab
        self.co_code = CodeString(code)
        self.subcodes = subcodes = []
        from types import CodeType
        for i in range(len(consts)):
            if type(consts[i]) == CodeType:
                subcodes.append(EditableCode(consts[i]))
                consts[i] = ()
    def init_tuple(self,tup):
        self.subcodes = []
        if len(tup)==13:
            self.subcodes = map(EditableCode, tup[-1])
            tup = tup[:-1]
        ( self.co_argcount, ignored, self.co_stacksize, self.co_flags
        , self.co_code, co_consts, co_names, co_varnames, self.co_filename
        , self.co_name, self.co_firstlineno, self.co_lnotab
        ) = tup
        self.co_consts = list(co_consts)
        self.co_names = list(co_names)
        self.co_varnames = list(co_varnames)
        self.co_code = CodeString(self)
    def make_code(self):
        if self.AUTO_RATIONALIZE:
            self.rationalize()
        else:
            # hack to deal with un-arg-ed names
            for op in self.co_code:
                if (op.has_name() or op.has_local()) and not hasattr(op, "arg"):
                    if op.has_name():
                      op.arg = self.name_index(op.name)
                    else:
                      op.arg = self.local_index(op.name)

        return apply(new.code, self.as_tuple()[:12])
    def set_function(self, function):
        self.function = function
    def set_name(self, name):
        self.co_name = name
    def set_filename(self, filename):
        self.co_filename = filename
    def as_tuple(self):
        # the assembling might change co_names or co_varnames - so
        # make sure it's done *before* we start gathering them.
        bytecode = self.co_code.assemble()
        subcodes = []
        for subcode in self.subcodes:
            subcodes.append(subcode.as_tuple())
        return (
            self.co_argcount,
            len(self.co_varnames),
            self.co_stacksize,
            self.co_flags,
            bytecode,
            tuple(self.co_consts),
            tuple(self.co_names),
            tuple(self.co_varnames),
            self.co_filename,
            self.co_name,
            self.co_firstlineno,
            self.co_lnotab,
            tuple(subcodes))

class Function(CycleHandle):
    def __init__(self,func=None):
	self._set_workers(FunctionWorker(func))
	    
class FunctionWorker:
    def __init__(self,func):
        if func is None:
            self.init_defaults()
        elif type(func) in (type(()), type([])):
            self.init_tuple(func)
        else:
            self.init_func(func)
        self.func_code.set_function(self)
    def init_defaults(self):
        self.__name = "no name"
        self.__doc = None
        self.func_code = EditableCode()
        self.func_defaults = []
        self.func_globals = {} # ???
    def init_func(self,func):
        self.__name = func.func_name
        self.__doc = func.func_doc
        self.func_code = EditableCode(func.func_code)
        self.func_defaults = func.func_defaults
        self.func_globals = func.func_globals
    def init_tuple(self,tup):
        ( self.__name, self.__doc, func_code, self.func_defaults
        , self.func_globals
        ) = tup
        self.func_code = EditableCode(func_code)
    def __getattr__(self,attr):
        # for a function 'f.__name__ is f.func_name'
        # so lets hack around to support that...
        if attr in ['__name__','func_name']:
            return self.__name
        if attr in ['__doc__','func_doc']:
            return self.__doc
        raise AttributeError, attr
    def __setattr__(self,attr,value):
        if attr in ['__name__','func_name']:
            self.__name = value
        elif attr in ['__doc__','func_doc']:
            self.__doc = value
        else:
            self.__dict__[attr]=value
    def make_function(self):
        self.func_code.set_name(self.__name)
        newfunc = new.function(
            self.func_code.make_code(),
            self.func_globals,
            self.__name)
        if not self.func_defaults:
            defs=None
        else:
            defs=tuple(self.func_defaults)
        newfunc.func_defaults = defs
        newfunc.func_doc = self.__doc
        return newfunc
    def __call__(self,*args,**kw):
        return apply(self.make_function(),args,kw)
    def set_method(self, method):
        self.method = method
    def as_tuple(self):
        self.func_code.set_name(self.__name)
        if not self.func_defaults:
            defs=None
        else:
            defs=tuple(self.func_defaults)
        return (self.__name, self.__doc, self.func_code.as_tuple(), defs, {})
    
class InstanceMethod(CycleHandle):
    def __init__(self,meth=None):
        self._set_workers(InstanceMethodWorker(meth))

class InstanceMethodWorker:
    def __init__(self,meth):
        if meth is None:
            self.init_defaults()
        else:
            self.init_meth(meth)
        self.im_func.set_method(self)
    def init_defaults(self):
        self.im_class = None
        self.im_func = Function()
        self.im_self = None
    def init_meth(self,meth):
        self.im_class = meth.im_class
        self.im_func = Function(meth.im_func)
        self.im_self = meth.im_self
    def make_instance_method(self):
        return new.instancemethod(
            self.im_func.make_function(),
            self.im_self,self.im_class)

class FunctionOrMethod:
    def __init__(self,functionormethod):
        if type(functionormethod) is types.FunctionType:
            self.is_method = 0
            self.function = Function(functionormethod)
        elif type(functionormethod) is types.UnboundMethodType:
            self.is_method = 1
            self.method = InstanceMethod(functionormethod)
            self.function = self.method.im_func
    def make_function_or_method(self):
        if self.is_method:
            return self.method.make_instance_method()
        else:
            return self.function.make_function()
        
