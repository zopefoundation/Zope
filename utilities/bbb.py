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
"""Read and (re-)format BoboPOS 2 database files
"""

import struct, string, sys, time, os

try: from cStringIO import StringIO
except: from StringIO import StringIO

ppml=None

file__version__=3.0
packed_version='SDBMV'+struct.pack(">f",file__version__)

def error(message, fatal=0, exc=0):
    if exc:
        sys.stderr.write('%s: %s' % (sys.exc_info()[0], sys.exc_info()[1]))
    sys.stderr.write("\n%s\n" % message)
    if fatal: sys.exit(fatal)

def _read_and_report(file, rpt=None, fromEnd=0, both=0, n=99999999, show=0):
    """\
    Read a file's index up to the given time.
    """
    first=1
    file.flush()
    seek=file.seek
    read=file.read
    unpack=struct.unpack
    split=string.split
    join=string.join
    find=string.find
    seek(0,2)
    file_size=file.tell()
    gmtime=time.gmtime

    if fromEnd: pos=file_size
    else:       pos=newpos=len(packed_version)
     
    tlast=0
    err=0
    while 1:
        if fromEnd:
            seek(pos-4)
            l=unpack(">i", read(4))[0]
            if l==0:
                b=pos
                p=pos-4
                while l==0:
                    p=p-4
                    seek(p)
                    l=unpack(">i", read(4))[0]

                pos=p+4
                error("nulls skipped from %s to %s" % (pos,b)) 
            p=pos-l
            if p < 0:
                error('Corrupted data before %s' % pos)
                if show > 0:
                    p=pos-show
                    if p < 0: p=0
                    seek(p)
                    p=read(pos-p)
                else:
                    p=''
                error(p,1)
            pos=p
        else:
            pos=newpos

        seek(pos)
        h=read(24) # 24=header_size
        if not h: break
        if len(h) !=  24: break
        oid,prev,start,tlen,plen=unpack(">iidii",h)
        if (prev < 0 or prev >= pos or start < tlast
            or plen > tlen or plen < 0 or oid < -999):
            __traceback_info__=pos, oid,prev,start,tlen,plen
            error('Corrupted data record at %s' % pos)
            if show > 0: error(read(show))
            err=1
            break


        newpos=pos+tlen
        if newpos > file_size:
            error('Truncated data record at %s' % pos)
            if show > 0: error(read(show))
            err=1
            break

        seek(newpos-4)
        if read(4) != h[16:20]:
            __traceback_info__=pos, oid,prev,start,tlen,plen
            error('Corrupted data record at %s' % pos)
            if show > 0:
                seek(pos+24)
                error(read(show))
            err=1
            break

        tlast=start-100

        if rpt is None: continue
        n=n-1
        if n < 1: break

        seek(pos+24)
        if plen > 0:
            p=read(plen)
            if p[-1:] != '.': 
                error('Corrupted pickle at %s %s %s' % (pos,plen,len(p)))
                if show > 0:
                    seek(pos+24)
                    error(read(show))
                err=1
                break

        else: p=''
        t=split(read(tlen-plen-28),'\t')
        tname, user = (t+[''])[:2]
        t=join(t[2:],'\t')
        start,f=divmod(start,1)
        y,m,d,h,mn,s=gmtime(start)[:6]
        s=s+f
        start="%.4d-%.2d-%.2d %.2d:%.2d:%.3f" % (y,m,d,h,mn,s)
        rpt(pos,oid,start,tname,user,t,p,first)
        first=0

    if err and both and not fromEnd:
        _read_and_report(file, rpt, 1, 0, n, show)

    rpt(None, None, None, None, None, None, None, None)


def none(*ignored): pass

def positions(pos, *ignored): 
    if pos is not None: sys.stdout.write("%s\n" % pos)

def oids(pos, oid, *ignored): 
    if pos is not None: sys.stdout.write("%s\n" % oid)

def tab_delimited(*args):
    sys.stdout.write("%s\n" % string.join(args[:6],'\t'))

def xml(pos, oid, start, tname, user, t, p, first):
    
    global ppml
    if ppml is None: import ppml
    u=ppml.ToXMLUnpickler
    
    write=sys.stdout.write

    if first: write('<?xml version="1.0">\n<ZopeData>\n')
    if pos is None: 
        write('</transaction>\n')
        write('</ZopeData>\n')
        return

    if user or t or first:
        if pos > 9: write('</transaction>\n')
        write('<transaction name="%s" user="%s">\n%s\n' % (tname, user,t))
    l=len(p)
    pp=p
    f=StringIO(p)
    u=u(f)
    u.idprefix='%s.' % pos
    p=u.load().__str__(4)
    if f.tell() < l:
        p=p+u.load().__str__(4)
    write('  <rec id="%s" time="%s">\n%s  </rec>\n' % (oid, start, p))

def xmls(pos, oid, start, tname, user, t, p, first):
    write=sys.stdout.write

    if first: write('<?xml version="1.0">\n<transactions>\n')
    if pos is None: 
        write('</transaction>\n')
        write('</transactioons>\n')
        return

    if user or t or first:
        if pos > 9: write('</transaction>\n')
        write('<transaction name="%s" user="%s">\n%s\n' % (tname, user,t))
        
reports={
    'none': (none,
             ('Read a database file checking for errors',
              'but producing no output')
             ),
    'xml': (xml,
            ('Convert the database to XML format',)
            ),
    'transactions': (xmls,
                     ('Output a summary of the database',
                      'transactions in XML')
                     ),
    'oids': (oids,
             ('Read the database and output object ids',)),
    'positions': (positions,
                  ('Read the database and output record positions',)),
    'tab_delimited': (tab_delimited,
                      ('Output record meta-data in tab-delimited format',)),
    }

if __name__=='__main__':
    import getopt

    items=reports.items()
    items.sort()
    
    usage="""Usage: python %s [options] filename

    where filename is the name of the database file.

    options:

       -r report

          Specify an output report.

          The valid reports are:\n\n\t\t%s

       -e

          Read the file from back to front

       -l n

          Show only n records

       -b

          If an error is encountered while reading from front,
          ret reading from the back.

       -s n

          If a corrupted data record is found, show the first n
          bytes of the corrupted record.
          
    """ % (sys.argv[0],
           string.join(map(
               lambda i:
               ("%s --\n\t\t\t%s" % (i[0], string.join(i[1][1],'\n\t\t\t'))),
               items),
               ',\n\n\t\t'))

    sys.path.append(os.path.split(sys.argv[0])[0])

    try:
        opts, args = getopt.getopt(sys.argv[1:],'r:ebl:s:')
        filename,=args
    except: error(usage,1,1)
    
    rpt=none
    fromEnd=0
    both=0
    n=99999999
    show=0
    for o, v in opts:
        o=o[1:]
        if o=='r':
            try: rpt=reports[v][0]
            except: error('Invalid report: %s' % v, 1)
        elif o=='l':
            try: n=string.atoi(v)
            except: error('The number of records, %s, shuld ne an integer'
                          % v, 1)
        elif o=='s':
            try: show=string.atoi(v)
            except: error('The number of bytes, %s, shuld ne an integer'
                          % v, 1)
        elif o=='e':
            fromEnd=1
        elif o=='b':
            both=1
        else:
            error('Unrecognized option: -%s' % o, 1)

    try: file=open(filename,'rb')
    except: error('Coud not open %s' % filename,1,1)

    _read_and_report(file, rpt, fromEnd, both, n, show)
