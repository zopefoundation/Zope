import sys

__doc__="""Fix BoboPOS time stamps

If a system has a problem with it's clock setting, it may cause
database records to be written with time stamps in the future.  This
causes problems when the clock is fixed or when the data are moved to
a system that doesn't have a broken clock.

The database has a requirement that records should be chronologically
ordered and that times not be in the future.

This copies a database, restamping the times as it goes.

%s [options] file1 file2

Copy file1 to file2 restamping the records.

  options:

    -o offset

       Records that are later offset seconds in the past
       are moved back to offset seconds in the past plus
       some small offset chosen so that times are not the same and
       are chronological.

""" % sys.argv[0]

InvalidFormat='Format Error'
Corrupted='Data Corruption'


def main():
    import getopt, string, struct, time
    file__version__=3.0
    packed_version='SDBMV'+struct.pack(">f",file__version__)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:')
        file1, file2 = args
        offset=86400
        for o, v in opts:
            if o=='-o':
                offset=string.atoi(v)
    except:
        print __doc__
        print "%s: %s" % sys.exc_info()[:2]

    start=time.time()-offset
    next=start+0.001
    input=open(file1,'rb')
    read=input.read
    output=open(file2,'wb')
    write=output.write
    pack=struct.pack
    unpack=struct.unpack
    
    h=read(len(packed_version))
    if h != packed_version:
        raise InvalidFormat, 'This is not a BoboPOS file'
    write(h)

    pos=len(h)

    while 1:
        h=read(24)
        if not h: break
        if len(h) < 24: raise Corrupted, pos
        oid, prev, t, tlen, plen = unpack(">iidii", h)
        if start is None or t > start:
            t=next
            next=next+0.001
            start=None
        if plen > tlen or tlen < 28: raise Corrupted, pos
        
        write(pack(">iidii", oid, prev, t, tlen, plen))
        l=tlen-28
        s=8196
        while l > 0:
            if s > l: s=l
            d=read(s)
            if not d: raise Corrupted, pos
            write(d)
            l=l-len(d)
        d=read(4)
        if d != h[16:20]: raise Corrupted, pos
        write(d)
        pos=pos+tlen

if __name__=='__main__': main()

