#! /usr/bin/env python

"""Index a collection of HTML files on the filesystem.

usage: indexhtml.py [options] dir

Will create an index of all files in dir or its subdirectories.

options:
-f data.fs  -- the path to the filestorage datafile
"""

import os
from time import clock

import ZODB
from ZODB.FileStorage import FileStorage
from BTrees.IOBTree import IOBTree

from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex
from Products.ZCTextIndex.HTMLSplitter import HTMLWordSplitter
from Products.ZCTextIndex.Lexicon import Lexicon, StopWordRemover

def make_index():
    # there's an elaborate dance necessary to construct an index
    class Struct:
        pass
    extra = Struct()
    extra.doc_attr = "read"
    extra.lexicon_id = "lexicon"
    caller = Struct()
    caller.lexicon = Lexicon(HTMLWordSplitter(), StopWordRemover())
    return ZCTextIndex("read", extra, caller)

def main(db, root, dir):
    rt["index"] = index = make_index()
    rt["files"] = paths = IOBTree()
    get_transaction().commit()

    zodb_time = 0.0
    pack_time = 0.0

    files = [os.path.join(dir, file) for file in os.listdir(dir)]
    docid = 0
    t0 = clock()
    for file in files:
        if os.path.isdir(file):
            files += [os.path.join(file, sub) for sub in os.listdir(file)]
        else:
            if not file.endswith(".html"):
                continue
            docid += 1
            print "%5d" % docid, file
            f = open(file, "rb")
            paths[docid] = file
            index.index_object(docid, f)
            f.close()
            if docid % TXN_INTERVAL == 0:
                z0 = clock()
                get_transaction().commit()
                z1 = clock()
                zodb_time += z1 - z0
            if docid % PACK_INTERVAL == 0:
                p0 = clock()
                db.pack()
                p1 = clock()
                zodb_time += p1 - p0
                zodb_time += p1 - p0
    z0 = clock()
    get_transaction().commit()
    z1 = t1 = clock()
    total_time = t1 - t0
    zodb_time += z1 - z0
    if VERBOSE:
        print "Total index time", total_time
        print "Non-pack time", total_time - pack_time
        print "Non-ZODB time", total_time - zodb_time

if __name__ == "__main__":
    import sys
    import getopt

    VERBOSE = 0
    FSPATH = "Data.fs"
    TXN_INTERVAL = 100
    PACK_INTERVAL = 500
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vf:')
    except getopt.error, msg:
        print msg
        print __doc__
        sys.exit(2)

    for o, v in opts:
        if o == '-v':
            VERBOSE += 1
        if o == '-f':
            FSPATH = v

    if len(args) != 1:
        print "Expected on argument"
        print __doc__
        sys.exit(2)
    dir = args[0]

    fs = FileStorage(FSPATH)
    db = ZODB.DB(fs)
    cn = db.open()
    rt = cn.root()
    dir = os.path.join(os.getcwd(), dir)
    print dir
    main(db, rt, dir)
    cn.close()
    fs.close()
