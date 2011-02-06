#! /usr/bin/env python
"""Dump statistics about each word in the index.

usage: wordstats.py data.fs [index key]
"""

import ZODB
from ZODB.FileStorage import FileStorage

def main(fspath, key):
    fs = FileStorage(fspath, read_only=1)
    db = ZODB.DB(fs)
    rt = db.open().root()
    index = rt[key]

    lex = index.lexicon
    idx = index.index
    print "Words", lex.length()
    print "Documents", idx.length()

    print "Word frequencies: count, word, wid"
    for word, wid in lex.items():
        docs = idx._wordinfo[wid]
        print len(docs), word, wid

    print "Per-doc scores: wid, (doc, score,)+"
    for wid in lex.wids():
        print wid,
        docs = idx._wordinfo[wid]
        for docid, score in docs.items():
            print docid, score,
        print

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    index_key = "index"
    if len(args) == 1:
        fspath = args[0]
    elif len(args) == 2:
        fspath, index_key = args
    else:
        print "Expected 1 or 2 args, got", len(args)
    main(fspath, index_key)
