##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

import struct, tempfile, string, time, pickle
from struct import pack, unpack
from cStringIO import StringIO

class FS:
    """FileStorage 'report' writer for converting BoboPOS to FileStorage
    """


    def __init__(self, fname):
        self.__name__=fname
        self._file=open(fname,'w+b')
        self._file.write('FS21')

        self._index={}
        self._indexpos=self._index.get
        self._tindex=[]
        self._tappend=self._tindex.append
        self._tfile=tempfile.TemporaryFile()
        self._pos=4
        

    def rpt(self, pos, oid, start, tname, user, t, p, first, newtrans):
        if pos is None:
            self.tpc_finish()
            return
        if newtrans:
            try: string.atof(tname)
            except:
                # Ugh, we have a weird tname.  We'll just ignore the transaction
                # boundary and merge transactions
                if first:
                    # But we can't ignore the first one, so we'll hack in a
                    # bogus start date
                    self.tpc_begin('100', user, t)
            else:
                if not first: self.tpc_finish()
                self.tpc_begin(tname, user, t)
        self.store(oid, p)

    def store(self, oid, data):
        old=self._indexpos(oid, 0)
        pnv=None

        tfile=self._tfile
        write=tfile.write
        pos=self._pos
        here=tfile.tell()+pos+self._thl
        self._tappend(oid, here)
        serial=self._serial
        data=fixpickle(data, oid)
        write(pack(">8s8s8s8sH8s",
                   p64(oid+1),serial,p64(old),p64(pos),
                   0,p64(len(data))
                   )
              )

        write(data)

    def tpc_begin(self, tname, user, desc):
        del self._tindex[:]   # Just to be sure!
        self._tfile.seek(0)

        t=string.atof(tname)
        y,m,d,h,mi=time.gmtime(t)[:5]
        s=t%60
        self._serial=struct.pack(
            ">II",
            (((((y-1900)*12)+m-1)*31+d-1)*24+h)*60+mi,
            long(s * (1L << 32) / 60)
            )

        # Ugh, we have to record the transaction header length
        # so that we can get version pointers right.
        self._thl=23+len(user)+len(desc)

        # And we have to save the data used to compute the
        # header length. It's unlikely that this stuff would
        # change, but if it did, it would be a disaster.
        self._ud=user, desc

    def tpc_finish(self):
        file=self._file
        write=file.write
        tfile=self._tfile
        dlen=tfile.tell()
        tfile.seek(0)
        id=self._serial
        user, desc = self._ud
        self._ud=None
                        
        tlen=self._thl
        pos=self._pos
        tl=tlen+dlen
        stl=p64(tl)
        write(pack(
            ">8s" "8s" "c"  "H"        "H"        "H"
            ,id, stl, ' ', len(user), len(desc), 0,
            ))
        if user: write(user)
        if desc: write(desc)
            
        cp(tfile, file, dlen)
                
        write(stl)
        self._pos=pos+tl+8

        tindex=self._tindex
        index=self._index
        for oid, pos in tindex: index[oid]=pos
        del tindex[:]


t32 = 1L << 32

def p64(v, pack=struct.pack):
    if v < t32: h=0
    else:
        h=v/t32
        v=v%t32
    return pack(">II", h, v)

def cp(f1, f2, l):
    read=f1.read
    write=f2.write
    n=8192
    
    while l > 0:
        if n > l: n=l
        d=read(n)
        write(d)
        l = l - len(d)

    
class Ghost: pass

class Global:
    __safe_for_unpickling__=1
    
    def __init__(self, m, n):
        self._module, self._name = m, n

    def __call__(self, *args):
        return Inst(self, args)

    __basicnew__=__call__

def _global(m, n):
    if m[:8]=='BoboPOS.':
        if m=='BoboPOS.PickleDictionary' and n=='Root':
            m='ZODB.conversionhack'
            n='hack'
        elif m=='BoboPOS.PersistentMapping': m='Persistence'
        else:
            raise 'Unexpected BoboPOS class', (m, n)

    return Global(m,n)
    

class Inst:

    _state=None
    
    def __init__(self, c, args):
        self._cls=c
        self._args=args

    def __setstate__(self, state): self._state=state


from pickle import INST, GLOBAL, MARK, BUILD, OBJ

InstanceType=type(Ghost())

class Unpickler(pickle.Unpickler):

    dispatch={}
    dispatch.update(pickle.Unpickler.dispatch)

    def load_inst(self):
        k = self.marker()
        args = tuple(self.stack[k+1:])
        del self.stack[k:]
        module = self.readline()[:-1]
        name = self.readline()[:-1]
        klass = _global(module, name)
        value=Inst(klass, args)
        self.append(value)
            
    dispatch[INST] = load_inst

    def load_global(self):
        module = self.readline()[:-1]
        name = self.readline()[:-1]
        klass = _global(module, name)
        self.append(klass)
    dispatch[GLOBAL] = load_global

    def persistent_load(self, oid,
                        TupleType=type(()), Ghost=Ghost, p64=p64):
        "Remap object ids from ZODB 2 stype to ZODB 3 style"

        if type(oid) is TupleType:
            oid, klass = oid
            oid = p64(oid+1), klass
        else:
            oid = p64(oid+1)
            
        Ghost=Ghost()
        Ghost.oid=oid
        return Ghost


class Pickler(pickle.Pickler):

    dispatch={}
    dispatch.update(pickle.Pickler.dispatch)

    def persistent_id(self, object, Ghost=Ghost):
        if hasattr(object, '__class__') and object.__class__ is Ghost:
            return object.oid

    def save_inst(self, object):
        d = id(object)
        cls = object.__class__

        memo  = self.memo
        write = self.write
        save  = self.save

        if cls is Global:
            memo_len = len(memo)
            write(GLOBAL + object._module + '\n' + object._name + '\n' +
                  self.put(memo_len))
            memo[d] = (memo_len, object)
            return

        args=object._args

        write(MARK)

        self.save_inst(object._cls)

        if args:
            for arg in args:
                save(arg)

        memo_len = len(memo)
        write(OBJ + self.put(len(memo)))

        memo[d] = (memo_len, object)

        stuff=object._state
        save(stuff)
        write(BUILD)

    dispatch[InstanceType] = save_inst

    def save_global(self, object, name = None):
        write = self.write
        memo = self.memo

        if (name is None):
            name = object._name

        module=object._module

        memo_len = len(memo)
        write(GLOBAL + module + '\n' + name + '\n' +
            self.put(memo_len))
        memo[id(object)] = (memo_len, object)

    dispatch[type(Ghost)] = save_global
    
    
def fixpickle(p, oid):
    
    pfile=StringIO(p)
    unpickler=Unpickler(pfile)

    newp=StringIO()
    pickler=Pickler(newp,1)

    pickler.dump(unpickler.load())
    state=unpickler.load()
    if oid==-1: state={'_container': state}
    pickler.dump(state)
    p=newp.getvalue()

    return p
