import struct,dis,new
from label import Label

class ByteCode:
    pass

class GenericOneByteCode(ByteCode):
    def __init__(self,cs,code):
        pass
    def __repr__(self):
        return self.__class__.__name__
    def assemble(self,code):
        return self.opc
    def is_jump(self):
        return 0 
    def has_name(self):
        return 0
    def has_name_or_local(self):
        return self.has_name() or self.has_local()
    def has_local(self):
        return 0

class GenericThreeByteCode(GenericOneByteCode):
    def __init__(self,cs,code):
        GenericOneByteCode.__init__(self,cs,code)
        arg=cs.read(2)
        self.arg=struct.unpack('<h',arg)[0]
    def __repr__(self):
        return "%s %d"%(self.__class__.__name__, self.arg)
    def assemble(self,code):
        return self.opc+struct.pack('<h',self.arg)
    def user_init(self,arg):
        self.arg = arg

class Jump(GenericThreeByteCode):
    def __repr__(self):
        return "%s %s"%(self.__class__.__name__, `self.label`)
    def is_jump(self):
        return 1
    def user_init(self,arg):
        self.label.op = arg
    
class JRel(Jump):
    def __init__(self,cs,code):
        GenericThreeByteCode.__init__(self,cs,code)
        self.label = Label(cs.tell()+self.arg)
        code.add_label(self.label)
    def assemble(self,code):
        self.label.add_relref(self.byte)
        return self.opc+'\000\000'

class JAbs(Jump):
    def __init__(self,cs,code):
        GenericThreeByteCode.__init__(self,cs,code)
        self.label = Label(self.arg)
        code.add_label(self.label)
    def assemble(self,code):
        self.label.add_absref(self.byte)
        return self.opc+'\000\000'

class _NamedOpcode(GenericThreeByteCode):
    def user_init(self,arg):
        if type(arg) == type(1):
            self.arg = arg
        else:
            self.name = arg
    def __repr__(self):
        if hasattr(self,"name"):
            return "%s : %s"%(self.__class__.__name__,self.name)
        else:
            return "%s : %d"%(self.__class__.__name__,self.arg)            

class NameOpcode(_NamedOpcode):
    def __init__(self,cs,code):
        GenericThreeByteCode.__init__(self,cs,code)
        self.name = code.code.co_names[self.arg]
    def has_name(self):
        return 1
    def assemble(self,code):
        if hasattr(self,"name") and not hasattr(self,"arg"):
            self.arg = code.code.name_index(self.name)
        return GenericThreeByteCode.assemble(self,code)

class LocalOpcode(_NamedOpcode):
    def __init__(self,cs,code):
        GenericThreeByteCode.__init__(self,cs,code)
        self.name = code.code.co_varnames[self.arg]
    def has_local(self):
        return 1
    def assemble(self,code):
        if hasattr(self,"name") and not hasattr(self,"arg"):
            self.arg = code.code.local_index(self.name)
        return GenericThreeByteCode.assemble(self,code)
    
