##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
__doc__='''Simple module for writing tar files

$Id: tar.py,v 1.2 1998/12/04 20:15:25 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

import sys, time, zlib
try:
    from newstruct import pack
except:
    from struct import pack
    

from string import find, join

def oct8(i):
    i=oct(i)
    return '0'*(6-len(i))+i+' \0'

def oct12(i):
    i=oct(i)
    return '0'*(11-len(i))+i+' '
    
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
        header=join([
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
            ], '')
        if len(header) != 512: raise 'Bad Header Length', len(header)
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
    return join(r,'')

def tgz(entries):
    c=zlib.compressobj()
    compress=c.compress
    r=[]
    ra=r.append
    for name, data in entries:
        ra(compress(str(TarEntry(name,data))))
    ra(compress('\0'*1024))
    ra(c.flush())
    return join(r,'')

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
        return join(r,'')
