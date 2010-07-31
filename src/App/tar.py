##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Simple module for writing tar files
"""

import sys, time, zlib
try:
    from newstruct import pack
except:
    from struct import pack


def oct8(i):
    i=oct(i)
    return '0'*(6-len(i))+i+' \0'

def oct12(i):
    i=oct(i)
    v = '0'*(11-len(i))+i+' '
    if len(v) > 12:
        left = v[:-12]
        for c in left:
            if c != '0':
                raise ValueError, 'value too large for oct12'
        return v[-12:]
    return v

def pad(s,l):
    ls=len(s)
    if ls >= l: raise ValueError, 'value, %s, too wide for field (%d)' % (s,l)
    return s+'\0'*(l-ls)

class TarEntry:

    def __init__(self, path, data,
                 mode=0644, uid=0, gid=0, mtime=None, typeflag='0',
                 linkname='', uname='jim', gname='system', prefix=''):
        "Initialize a Tar archive entry"
        self.data=data
        if mtime is None: mtime=int(time.time())
        header=''.join([
            pad(path,      100),
            oct8(mode),
            oct8(uid),
            oct8(gid),
            oct12(len(data)),
            oct12(mtime),
            ' ' * 8,
            typeflag,
            pad(linkname,  100),
            'ustar\0',
            '00',
            pad(uname,      32),
            pad(gname,      32),
            '000000 \0',
            '000000 \0',
            pad(prefix,    155),
            '\0'*12,
            ])
        if len(header) != 512:
            raise ValueError, 'Bad Header Length: %d' % len(header)
        header=(header[:148]+
                oct8(reduce(lambda a,b: a+b, map(ord,header)))+
                header[156:])
        self.header=header

    def __str__(self):
        data=self.data
        l=len(data)
        if l%512: data=data+'\0'*(512-l%512)
        return self.header+data

def tar(entries):
    r=[]
    ra=r.append
    for name, data in entries:
        ra(str(TarEntry(name,data)))
    ra('\0'*1024)
    return ''.join(r)

def tgz(entries):
    c=zlib.compressobj()
    compress=c.compress
    r=[]
    ra=r.append
    for name, data in entries:
        ra(compress(str(TarEntry(name,data))))
    ra(compress('\0'*1024))
    ra(c.flush())
    return ''.join(r)

class tgzarchive:

    def __init__(self, name, time=None):
        self._f=gzFile('%s.tar' % name, time)

    def add(self, name, data):
        self._f.write(str(TarEntry(name,data)))

    def finish(self):
        self._f.write('\0'*1024)

    def __str__(self):
        return self._f.getdata()

class gzFile:
    _l=0
    _crc=zlib.crc32("")

    def __init__(self, name, t=None):
        self._c=zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS,
                                 zlib.DEF_MEM_LEVEL, 0)
        if t is None: t=time.time()
        self._r=['\037\213\010\010',
                 pack("<i", int(t)),
                 '\2\377',
                 name,
                 '\0'
                 ]

    def write(self, s):
        self._crc=zlib.crc32(s, self._crc)
        self._r.append(self._c.compress(s))
        self._l=self._l+len(s)

    def getdata(self):
        r=self._r
        append=r.append
        append(self._c.flush())
        append(pack("<i", self._crc))
        append(pack("<i", self._l))
        return ''.join(r)
