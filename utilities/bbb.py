#!/usr/bin/env python
"""Read and (re-)format BoboPOS 2 database files
"""

import struct, string, sys, time

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
        p=read(plen)
        t=split(read(tlen-plen-28),'\t')
        tname, user = (t+[''])[:2]
        t=join(t[2:],'\t')
        start,f=divmod(start,1)
        y,m,d,h,mn,s=gmtime(start)[:6]
        s=s+f
        start="%.4d-%.2d-%.2d %.2d:%.2d:%.3f" % (y,m,d,h,mn,s)
        rpt(pos, oid,start,tname,user,t,p)

    if err and both and not fromEnd:
        _read_and_report(file, rpt, 1, 0, n, show)



def none(*ignored): pass
def positions(pos, *ignored): sys.stdout.write("%s\n" % pos)
def tab_delimited(*args):
    sys.stdout.write("%s\n" % string.join(args[:-1],'\t'))


reports={
    'none': none,
    'positions': positions,
    'tab_delimited': tab_delimited,
    }

if __name__=='__main__':
    import getopt

    usage="""Usage: %s [options] filename

    where filename is the name of the database file.

    options:

       -r report

          Specify an output report.

          The valid reports are:
		%s

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
          
    """ % (sys.argv[0], string.join(reports.keys(), ',\n\t\t'))

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
            try: rpt=reports[v]
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

    try: file=open(filename)
    except: error('Coud not open %s' % filename,1,1)

    _read_and_report(file, rpt, fromEnd, both, n, show)

            
    




