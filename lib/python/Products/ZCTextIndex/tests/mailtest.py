"""Test an index with a Unix mailbox file.

usage: python mailtest.py [options] <data.fs>

options:
    -v     -- verbose
    -n NNN -- max number of messages to read from mailbox
    -q query
    -i mailbox
    -p NNN -- pack <data.fs> every NNN messages (default: 500), and at end
    -p 0   -- don't pack at all
    -b NNN -- return the NNN best matches (default: 10)
    -x     -- exclude the message text from the data.fs
    -t NNN -- commit a transaction every NNN messages (default: 1)

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
from Products.ZCTextIndex.Lexicon import Lexicon, \
     CaseNormalizer, Splitter, StopWordRemover
from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex
from BTrees.IOBTree import IOBTree

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

def index(rt, mboxfile, db):
    global NUM
    idx_time = 0
    pack_time = 0

    lexicon = Lexicon(Splitter(), CaseNormalizer(), StopWordRemover())
    extra = Extra()
    extra.lexicon_id = 'lexicon'
    extra.doc_attr = 'text'
    caller = Extra()
    caller.lexicon = lexicon
    rt["index"] = idx = ZCTextIndex("index", extra, caller)
    if not EXCLUDE_TEXT:
        rt["documents"] = docs = IOBTree()
    get_transaction().commit()

    mbox = mailbox.UnixMailbox(open(mboxfile))
    if VERBOSE:
        print "opened", mboxfile
    if not NUM:
        NUM = sys.maxint
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
            get_transaction().commit()
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

    get_transaction().commit()

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
        print "Index time", idx_time
        print "Index bytes", Message.total_bytes
        rate = (Message.total_bytes / idx_time) / 1024
        print "Index rate %d KB/sec" % int(rate)

def query(rt, query_str):
    idx = rt["index"]
    docs = rt["documents"]
    results, num_results = idx.query(query_str, BEST)
    print "query:", query_str
    print "# results:", len(results)
    for docid, score in results:
        print "docid %4d score %2d" % (docid, score)
        if VERBOSE:
            msg = docs[docid]
            # print 3 lines of context
            CONTEXT = 5
            ctx = msg.text.split("\n", CONTEXT)
            del ctx[-1]
            print "-" * 60
            print "message:"
            for l in ctx:
                print l
            print "-" * 60


def main(fs_path, mbox_path, query_str):
    f = ZODB.FileStorage.FileStorage(fs_path)
    db = ZODB.DB(f, cache_size=CACHE_SIZE)
    cn = db.open()
    rt = cn.root()

    if mbox_path is not None:
        index(rt, mbox_path, db)
    if query_str is not None:
        query(rt, query_str)

    cn.close()
    db.close()
    f.close()

if __name__ == "__main__":
    import getopt

    NUM = 0
    BEST = 10
    VERBOSE = 0
    PACK_INTERVAL = 500
    EXCLUDE_TEXT = 0
    CACHE_SIZE = 10000
    TXN_SIZE = 1
    query_str = None
    mbox_path = None
    profile = None
    old_profile = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vn:p:i:q:b:xt:',
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
        elif o == '--profile':
            profile = v
        elif o == '--old-profile':
            old_profile = v
    fs_path, = args
    if profile:
        import hotshot
        profiler = hotshot.Profile(profile, lineevents=1, linetimings=1)
        profiler.runcall(main, fs_path, mbox_path, query_str)
        profiler.close()
    elif old_profile:
        import profile, pstats
        profiler = profile.Profile()
        profiler.runcall(main, fs_path, mbox_path, query_str)
        profiler.dump_stats(old_profile)
        stats = pstats.Stats(old_profile)
        stats.strip_dirs().sort_stats('time').print_stats(20)
    else:
        main(fs_path, mbox_path, query_str)
