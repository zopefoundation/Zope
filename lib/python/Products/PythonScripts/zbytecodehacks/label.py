import struct

class Label:
    def __init__(self,byte=None):
        self.byte=byte
        self.__op=None
        self.absrefs=[]
        self.relrefs=[]
    def resolve(self,code):
        self.__op=code.opcodes[code.byte2op[self.byte]]
    def add_absref(self,byte):
        # request that the absolute address of self.op be written to
        # the argument of the opcode starting at byte in the
        # codestring
        self.absrefs.append(byte)
    def add_relref(self,byte):
        # request that the relative address of self.op be written to
        # the argument of the opcode starting at byte in the
        # codestring
        self.relrefs.append(byte)
    def __setattr__(self,attr,value):
        if attr == 'op':
            self.__op = value
        else:
            self.__dict__[attr] = value
    def __getattr__(self,attr):
        if attr == 'op':
            return self.__op
        else:
            raise AttributeError, attr
    def write_refs(self,cs):
        address=self.__op.byte
        for byte in self.absrefs:
            cs.seek(byte+1)
            cs.write(struct.pack('<h',address))
        for byte in self.relrefs:
            offset=address-byte-3
            cs.seek(byte+1)
            cs.write(struct.pack('<h',offset))

