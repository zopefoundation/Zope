"""Test an index with a Unix mailbox file.

usage: python mailtest.py [options] <data.fs>

options:
    -v     -- verbose

    Index Generation
    -i mailbox
    -n NNN -- max number of messages to read from mailbox
    -t NNN -- commit a transaction every NNN messages (default: 1)
    -p NNN -- pack <data.fs> every NNN messages (default: 500), and at end
    -p 0   -- don't pack at all
    -x     -- exclude the message text from the data.fs

    Queries
    -q query
    -b NNN -- return the NNN best matches (default: 10)
    -c NNN -- context; if -v, show the first NNN lines of results (default: 5)

The script either indexes or queries depending on whether -q or -i is
passed as an option.

For -i mailbox, the script reads mail messages from the mailbox and
indexes them.  It indexes one message at a time, then commits the
transaction.

For -q query, it performs a query on an existing index.

If both are specified, the index is performed first.

You can also interact with the index after it is completed. Load the
index from the database:

    import ZODB
    from ZODB.FileStorage import FileStorage
    fs = FileStorage(<data.fs>
    db = ZODB.DB(fs)
    index = cn.open().root()["index"]
    index.search("python AND unicode")
"""

import ZODB
import ZODB.FileStorage
import transaction
from Products.ZCTextIndex.Lexicon import \
     Lexicon, CaseNormalizer, Splitter, StopWordRemover
from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex
from BTrees.IOBTree import IOBTree
from Products.ZCTextIndex.QueryParser import QueryParser

import sys
import mailbox
import time

def usage(msg):
    print msg
    print __doc__
    sys.exit(2)

class Message:

    total_bytes = 0

    def __init__(self, msg):
        subject = msg.getheader('subject', '')
        author = msg.getheader('from', '')
        if author:
            summary = "%s (%s)\n" % (subject, author)
        else:
            summary = "%s\n" % subject
        self.text = summary + msg.fp.read()
        Message.total_bytes += len(self.text)

class Extra:
    pass

def index(rt, mboxfile, db, profiler):
    global NUM
    idx_time = 0
    pack_time = 0
    start_time = time.time()

    lexicon = Lexicon(Splitter(), CaseNormalizer(), StopWordRemover())
    extra = Extra()
    extra.lexicon_id = 'lexicon'
    extra.doc_attr = 'text'
    extra.index_type = 'Okapi BM25 Rank'
    caller = Extra()
    caller.lexicon = lexicon
    rt["index"] = idx = ZCTextIndex("index", extra, caller)
    if not EXCLUDE_TEXT:
        rt["documents"] = docs = IOBTree()
    else:
        docs = None
    transaction.commit()

    mbox = mailbox.UnixMailbox(open(mboxfile, 'rb'))
    if VERBOSE:
        print "opened", mboxfile
    if not NUM:
        NUM = sys.maxint

    if profiler:
        itime, ptime, i = profiler.runcall(indexmbox, mbox, idx, docs, db)
    else:
        itime, ptime, i = indexmbox(mbox, idx, docs, db)
    idx_time += itime
    pack_time += ptime

    transaction.commit()

    if PACK_INTERVAL and i % PACK_INTERVAL != 0:
        if VERBOSE >= 2:
            print "packing one last time..."
        p0 = time.clock()
        db.pack(time.time())
        p1 = time.clock()
        if VERBOSE:
            print "pack took %s sec" % (p1 - p0)
        pack_time += p1 - p0

    if VERBOSE:
        finish_time = time.time()
        print
        print "Index time", round(idx_time / 60, 3), "minutes"
        print "Pack time", round(pack_time / 60, 3), "minutes"
        print "Index bytes", Message.total_bytes
        rate = (Message.total_bytes / idx_time) / 1024
        print "Index rate %.2f KB/sec" % rate
        print "Indexing began", time.ctime(start_time)
        print "Indexing ended", time.ctime(finish_time)
        print "Wall clock minutes", round((finish_time - start_time)/60, 3)

def indexmbox(mbox, idx, docs, db):
    idx_time = 0
    pack_time = 0
    i = 0
    while i < NUM:
        _msg = mbox.next()
        if _msg is None:
            break
        i += 1
        msg = Message(_msg)
        if VERBOSE >= 2:
            print "indexing msg", i
        i0 = time.clock()
        idx.index_object(i, msg)
        if not EXCLUDE_TEXT:
            docs[i] = msg
        if i % TXN_SIZE == 0:
            transaction.commit()
        i1 = time.clock()
        idx_time += i1 - i0
        if VERBOSE and i % 50 == 0:
            print i, "messages indexed"
            print "cache size", db.cacheSize()
        if PACK_INTERVAL and i % PACK_INTERVAL == 0:
            if VERBOSE >= 2:
                print "packing..."
            p0 = time.clock()
            db.pack(time.time())
            p1 = time.clock()
            if VERBOSE:
                print "pack took %s sec" % (p1 - p0)
            pack_time += p1 - p0
    return idx_time, pack_time, i


def query(rt, query_str, profiler):
    idx = rt["index"]
    docs = rt["documents"]

    start = time.clock()
    if profiler is None:
        results, num_results = idx.query(query_str, BEST)
    else:
        if WARM_CACHE:
            print "Warming the cache..."
            idx.query(query_str, BEST)
        start = time.clock()
        results, num_results = profiler.runcall(idx.query, query_str, BEST)
    elapsed = time.clock() - start

    print "query:", query_str
    print "# results:", len(results), "of", num_results, \
          "in %.2f ms" % (elapsed * 1000)

    tree = QueryParser(idx.lexicon).parseQuery(query_str)
    qw = idx.index.query_weight(tree.terms())

    for docid, score in results:
        scaled = 100.0 * score / qw
        print "docid %7d score %6d scaled %5.2f%%" % (docid, score, scaled)
        if VERBOSE:
            msg = docs[docid]
            ctx = msg.text.split("\n", CONTEXT)
            del ctx[-1]
            print "-" * 60
            print "message:"
            for l in ctx:
                print l
            print "-" * 60


def main(fs_path, mbox_path, query_str, profiler):
    f = ZODB.FileStorage.FileStorage(fs_path)
    db = ZODB.DB(f, cache_size=CACHE_SIZE)
    cn = db.open()
    rt = cn.root()

    if mbox_path is not None:
        index(rt, mbox_path, db, profiler)
    if query_str is not None:
        query(rt, query_str, profiler)

    cn.close()
    db.close()
    f.close()

if __name__ == "__main__":
    import getopt

    NUM = 0
    VERBOSE = 0
    PACK_INTERVAL = 500
    EXCLUDE_TEXT = 0
    CACHE_SIZE = 10000
    TXN_SIZE = 1
    BEST = 10
    CONTEXT = 5
    WARM_CACHE = 0
    query_str = None
    mbox_path = None
    profile = None
    old_profile = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vn:p:i:q:b:c:xt:w',
                                   ['profile=', 'old-profile='])
    except getopt.error, msg:
        usage(msg)
    if len(args) != 1:
        usage("exactly 1 filename argument required")
    for o, v in opts:
        if o == '-n':
            NUM = int(v)
        elif o == '-v':
            VERBOSE += 1
        elif o == '-p':
            PACK_INTERVAL = int(v)
        elif o == '-q':
            query_str = v
        elif o == '-i':
            mbox_path = v
        elif o == '-b':
            BEST = int(v)
        elif o == '-x':
            EXCLUDE_TEXT = 1
        elif o == '-t':
            TXN_SIZE = int(v)
        elif o == '-c':
            CONTEXT = int(v)
        elif o == '-w':
            WARM_CACHE = 1
        elif o == '--profile':
            profile = v
        elif o == '--old-profile':
            old_profile = v
    fs_path, = args

    if profile:
        import hotshot
        profiler = hotshot.Profile(profile, lineevents=1, linetimings=1)
    elif old_profile:
        import profile
        profiler = profile.Profile()
    else:
        profiler = None

    main(fs_path, mbox_path, query_str, profiler)

    if profile:
        profiler.close()
    elif old_profile:
        import pstats
        profiler.dump_stats(old_profile)
        stats = pstats.Stats(old_profile)
        stats.strip_dirs().sort_stats('time').print_stats(20)
