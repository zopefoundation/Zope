import string, struct, sys, tempfile
import Shared.DC.xml.ppml
import Shared.DC.xml.xyap

ppml=Shared.DC.xml.ppml
xyap=Shared.DC.xml.xyap
xyap=xyap.xyap
p64=ppml.p64
u64=ppml.u64
cp=ppml.cp

try: from cStringIO import StringIO
except: from StringIO import StringIO

export_end_marker='\377'*16
StringType=type('')

class ZopeData:
    def __init__(self, parser, tag, attrs):
        self._pos=0
        self.file=parser.file
        self.tempfile=parser.tempfile

    def append(self, transaction, f=None):
        file=self.file
        write=file.write
        tfile=self.tempfile
        dlen=tfile.tell()
        tfile.seek(0)
        id=transaction.serial
        user, desc, ext = transaction._ude
        transaction._ude=None

        tlen=transaction._thl
        pos=self._pos
        file.seek(pos)
        tl=tlen+dlen
        stl=p64(tl)
        write(struct.pack(
            ">8s" "8s" "c"  "H"         "H"         "H"
            , id, stl, ' ', len(user), len(desc), len(ext),
            ))
        if user: write(user)
        if desc: write(desc)
        if ext: write(ext)

        cp(tfile,file,dlen)

        write(stl)
        self._pos=pos+tl+8


class Transaction:
    def __init__(self, parser, tag, attrs):
        self.file=parser.file
        self.tempfile=parser.tempfile

        self.tempfile.seek(0)
       
        tyme=attrs['time']
        start=0
        stop=string.find(tyme[start:],'-')+start
        year=string.atoi(tyme[start:stop])
        start=stop+1
        stop=string.find(tyme[start:],'-')+start
        month=string.atoi(tyme[start:stop])
        start=stop+1
        stop=string.find(tyme[start:],' ')+start
        day=string.atoi(tyme[start:stop])
        start=stop+1
        stop=string.find(tyme[start:],':')+start
        hour=string.atoi(tyme[start:stop])
        start=stop+1
        stop=string.find(tyme[start:],':')+start
        minute=string.atoi(tyme[start:stop])
        start=stop+1
        second=string.atof(tyme[start:])
        t=(((((year-1900)*12+month-1)*31+day-1)*24+hour)*60+minute)
        t=struct.pack(">If",t,second*(1L<<32)/60)
        self.serial=t
        self._user=user=''
        self._descr=desc=''
        self._ext=ext=''
        self._thl= 23+len(user)+len(desc)+len(ext)
        self._ude= user, desc, ext
        self._index={}
        self._tindex=[]
        self._pos=0
        self._oid='\0\0\0\0\0\0\0\0'

    def append(self, data):
        version=''
        old=self._index.get(self._oid,0)
        pnv=None
        if old:
            file=self.file
            file.seek(old)
            read=file.read
            h=read(42)
            doid,oserial,sprev,stloc,vlen,splen = unpack(">8s8s8s8sH8s", h)
            if doid != self.serial: raise CorruptedDataError, h
            
        tfile=self.tempfile
        write=tfile.write
        pos=self._pos
        serial=self.serial
        oid=self._oid
        here=tfile.tell()+pos+self._thl
        self._tindex.append((self._oid, here))
        serial=self.serial
        write(struct.pack(">8s8s8s8sH8s", oid, serial, p64(old), p64(pos),
                   len(version), p64(len(data))))

        for x in data[2:]:
            write(x)

        return serial

def save_user(self, tag, data):
    transaction=self._transaction
    if len(data)>2: v=data[2]
    else: v=''
    self._user=v
    transaction._thl=self._transaction._thl+len(v)
    transaction._ude=v,transaction._ude[1],transaction._ude[2]
    return v

def save_description(self, tag, data):
    transaction=self._transaction
    if len(data)>2: v=data[2]
    else: v=''
    a=data[1]
    if a.has_key('encoding'): encoding=a['encoding']
    else: encoding=''
    if encoding:
        v=unconvert(encoding,v)
    transaction._descr=v
    transaction._thl=transaction._thl+len(v)
    transaction._ude=transaction._ude[0],v,transaction._ude[2]
    return v

def save_rec(self, tag, data):
    a=data[1]
    if a.has_key('id'):
        a['id']=p64(string.atoi(a['id'])+1)
    if a.has_key('time'):
        start=0
        stop=string.find(a['time'][start:],'-')+start
        year=string.atoi(a['time'][start:stop])
        start=stop+1
        stop=string.find(a['time'][start:],'-')+start
        month=string.atoi(a['time'][start:stop])
        start=stop+1
        stop=string.find(a['time'][start:],' ')+start
        day=string.atoi(a['time'][start:stop])
        start=stop+1
        stop=string.find(a['time'][start:],':')+start
        hour=string.atoi(a['time'][start:stop])
        start=stop+1
        stop=string.find(a['time'][start:],':')+start
        minute=string.atoi(a['time'][start:stop])
        start=stop+1
        second=string.atof(a['time'][start:])
        a['time']=struct.pack(">If",(((((year-1900)*12)+month-1)*31+day-1)*24+
                                   hour)*60 +minute, second*(1L<<32)/60)
        data[1]=a
        
    return data

def start_transaction(self, tag, attrs):
    self._transaction=Transaction(self, tag, attrs)
    return self._transaction

def start_ZopeData(self, tag, attrs):
    self._ZopeData=ZopeData(self, tag, attrs)
    return self._ZopeData

def XMLtobbb(infile, outfile, binary=0):
    import Shared.DC.xml.pyexpat
    if type(infile) is StringType:
        data=open(infile).read()
    if type(outfile) is StringType:
        outfile=open(outfile,'w'+'b')
    F=ppml.xmlPickler()
    F.end_handlers['user'] = save_user
    F.end_handlers['description'] = save_description
    F.end_handlers['rec'] = save_rec
    F.start_handlers['transaction'] = start_transaction
    F.start_handlers['ZopeData'] = start_ZopeData
    F.binary=binary
    F.file=outfile
    F.tempfile=tempfile.TemporaryFile()
    p=xml.parsers.pyexpat.ParserCreate()
    p.CharacterDataHandler=F.handle_data
    p.StartElementHandler=F.unknown_starttag
    p.EndElementHandler=F.unknown_endtag
    r=p.Parse(data)
    return r

def save_record(self, tag, data):
    file=self.file
    write=file.write
    pos=file.tell()
    file.seek(pos)
    a=data[1]
    if a.has_key('id'): oid=a['id']
    oid=ppml.p64(string.atoi(oid))
    v=''
    for x in data[2:]:
        v=v+x
    l=ppml.p64(len(v))
    v=oid+l+v
    return v

class zopedata:
    def __init__(self, parser, tag, attrs):
        self.file=parser.file
        write=self.file.write
        write('ZEXP')

    def append(self, data):
        file=self.file
        write=file.write
        pos=file.tell()
        file.seek(pos)
        write(data)

def start_zopedata(self, tag, data):
    return zopedata(self, tag, data)

def save_zopedata(self, tag, data):
    file=self.file
    write=file.write
    pos=file.tell()
    file.seek(pos)
    write(export_end_marker)
    

def XMLtoExport(infile, outfile):
    import Shared.DC.xml.pyexpat.pyexpat
    pyexpat=Shared.DC.xml.pyexpat.pyexpat
    if type(infile) is StringType:
        infile=open(infile)
    if type(outfile) is StringType:
        outfile=open(outfile,'w'+'b')
    data=infile.read()
    F=ppml.xmlPickler()
    F.end_handlers['record'] = save_record
    F.end_handlers['ZopeData'] = save_zopedata
    F.start_handlers['ZopeData'] = start_zopedata
    F.binary=1
    F.file=outfile
    p=pyexpat.ParserCreate()
    p.CharacterDataHandler=F.handle_data
    p.StartElementHandler=F.unknown_starttag
    p.EndElementHandler=F.unknown_endtag
    r=p.Parse(data)
    return r

def XMLrecord(oid,len,p):
    q=ppml.ToXMLUnpickler
    f=StringIO(p)
    u=q(f)
    u.idprefix=str(oid)+'.'
    p=u.load().__str__(4)
    if f.tell() < len:
        p=p+u.load().__str__(4)
    String='  <record id="%s">\n%s  </record>\n' % (oid, p)
    return String


def ExporttoXML(file):
    String=''
    if type(file) is StringType:
        file=open(file,'rb')
    read=file.read
    if read(4) !='ZEXP':
        raise POSException.ExportError, 'Invalid export header'

    String=String+'<?xml version="1.0"?>\012<ZopeData>\n'
    while 1:
        h=read(16)
        if h == export_end_marker: break
        if len(h) != 16: raise ExportError, 'Truncated export file'
        oid=ppml.u64(h[:8])
        l=ppml.u64(h[8:16])
        pos=file.tell()
        p=read(l)
        if len(p) != l: raise ExportError, 'Truncated export file'
        String=String+XMLrecord(oid,l,p)
        l=l+pos
        
    String=String+'</ZopeData>\n'
    return String


# End exportToXML    

def XMLstringToExport(data, outfile):
    import Shared.DC.xml.pyexpat
    if type(outfile) is StringType:
        outfile=open(outfile,'w'+'b')
    F=ppml.xmlPickler()
    F.end_handlers['record'] = save_record
    F.end_handlers['ZopeData'] = save_zopedata
    F.start_handlers['ZopeData'] = start_zopedata
    F.binary=1
    F.file=outfile
    p=xml.parsers.pyexpat.ParserCreate()
    p.CharacterDataHandler=F.handle_data
    p.StartElementHandler=F.unknown_starttag
    p.EndElementHandler=F.unknown_endtag
    r=p.Parse(data)
    return r
    

if __name__=='__main__': exportToXML(sys.argv[1])

