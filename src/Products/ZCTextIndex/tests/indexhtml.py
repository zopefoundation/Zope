#! /usr/bin/env python
"""Index a collection of HTML files on the filesystem.

usage: indexhtml.py [options] dir

Will create an index of all files in dir or its subdirectories.

options:
-f data.fs  -- the path to the filestorage datafile
"""
# XXX: Products.PluginIndexes.TextIndex no longer exists
from __future__ import nested_scopes

import os
from time import clock

import ZODB
from ZODB.FileStorage import FileStorage
from BTrees.IOBTree import IOBTree
import transaction

from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex
from Products.ZCTextIndex.HTMLSplitter import HTMLWordSplitter
from Products.ZCTextIndex.Lexicon import Lexicon, StopWordRemover

def make_zc_index():
    # there's an elaborate dance necessary to construct an index
    class Struct:
        pass
    extra = Struct()
    extra.doc_attr = "read"
    extra.lexicon_id = "lexicon"
    caller = Struct()
    caller.lexicon = Lexicon(HTMLWordSplitter(), StopWordRemover())
    return ZCTextIndex("read", extra, caller)

# XXX make a splitter more like the HTMLSplitter for TextIndex
# signature is
# Splitter(string, stop_words, encoding,
#          singlechar, indexnumbers, casefolding)

class MySplitter:
    def __init__(self):
        self._v_splitter = HTMLWordSplitter()
    def __call__(self, text, stopdict, *args, **kwargs):
        words = self._v_splitter._split(text)
        def lookup(w):
            return stopdict.get(w, w)
        return filter(None, map(lookup, words))

#def make_old_index():
#    from Products.PluginIndexes.TextIndex.TextIndex import TextIndex
#    from Products.PluginIndexes.TextIndex.Lexicon  import Lexicon
#    from Products.ZCTextIndex.StopDict import get_stopdict
#
#    l = Lexicon(get_stopdict())
#    l.SplitterFunc = MySplitter()
#    return TextIndex("read", lexicon=l)

def main(db, root, dir):
    rt["index"] = index = INDEX()
    rt["files"] = paths = IOBTree()
    transaction.commit()

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
            if LIMIT is not None and docid > LIMIT:
                break
            if VERBOSE:
                print "%5d" % docid, file
            f = open(file, "rb")
            paths[docid] = file
            index.index_object(docid, f)
            f.close()
            if docid % TXN_INTERVAL == 0:
                z0 = clock()
                transaction.commit()
                z1 = clock()
                zodb_time += z1 - z0
                if VERBOSE:
                    print "commit took", z1 - z0, zodb_time
            if docid % PACK_INTERVAL == 0:
                p0 = clock()
                db.pack()
                p1 = clock()
                zodb_time += p1 - p0
                pack_time += p1 - p0
                if VERBOSE:
                    print "pack took", p1 - p0, pack_time
    z0 = clock()
    transaction.commit()
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
    LIMIT = None
    INDEX = make_zc_index
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vf:t:p:n:T')
    except getopt.error, msg:
        print msg
        print __doc__
        sys.exit(2)

    for o, v in opts:
        if o == '-v':
            VERBOSE += 1
        if o == '-f':
            FSPATH = v
        if o == '-t':
            TXN_INTERVAL = int(v)
        if o == '-p':
            PACK_INTERVAL = int(v)
        if o == '-n':
            LIMIT = int(v)
#        if o == '-T':
#            INDEX = make_old_index

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
