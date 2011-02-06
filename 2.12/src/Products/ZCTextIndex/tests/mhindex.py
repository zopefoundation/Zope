"""MH mail indexer.

To index messages from a single folder (messages defaults to 'all'):
  mhindex.py [options] -u +folder [messages ...]

To bulk index all messages from several folders:
  mhindex.py [options] -b folder ...; the folder name ALL means all folders.

To execute a single query:
  mhindex.py [options] query

To enter interactive query mode:
  mhindex.py [options]

Common options:
  -d FILE -- specify the Data.fs to use (default ~/.Data.fs)
  -w -- dump the word list in alphabetical order and exit
  -W -- dump the word list ordered by word id and exit

Indexing options:
  -O -- do a prescan on the data to compute optimal word id assignments;
        this is only useful the first time the Data.fs is used
  -t N -- commit a transaction after every N messages (default 20000)
  -p N -- pack after every N commits (by default no packing is done)

Querying options:
  -m N -- show at most N matching lines from the message (default 3)
  -n N -- show the N best matching messages (default 3)
"""

import os
import re
import sys
import time
import mhlib
import getopt
import traceback
from StringIO import StringIO
from stat import ST_MTIME

DATAFS = "~/.Data.fs"
ZOPECODE = "~/projects/Zope/lib/python"

sys.path.append(os.path.expanduser(ZOPECODE))

from ZODB import DB
from ZODB.FileStorage import FileStorage
from Persistence import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.IIBTree import IIBTree
import transaction

from Products.ZCTextIndex.NBest import NBest
from Products.ZCTextIndex.OkapiIndex import OkapiIndex
from Products.ZCTextIndex.Lexicon import Lexicon, Splitter
from Products.ZCTextIndex.Lexicon import CaseNormalizer, StopWordRemover
from Products.ZCTextIndex.QueryParser import QueryParser
from Products.ZCTextIndex.StopDict import get_stopdict

NBEST = 3
MAXLINES = 3

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "bd:fhm:n:Op:t:uwW")
    except getopt.error, msg:
        print msg
        print "use -h for help"
        return 2
    update = 0
    bulk = 0
    optimize = 0
    nbest = NBEST
    maxlines = MAXLINES
    datafs = os.path.expanduser(DATAFS)
    pack = 0
    trans = 20000
    dumpwords = dumpwids = dumpfreqs = 0
    for o, a in opts:
        if o == "-b":
            bulk = 1
        if o == "-d":
            datafs = a
        if o == "-f":
            dumpfreqs = 1
        if o == "-h":
            print __doc__
            return
        if o == "-m":
            maxlines = int(a)
        if o == "-n":
            nbest = int(a)
        if o == "-O":
            optimize = 1
        if o == "-p":
            pack = int(a)
        if o == "-t":
            trans = int(a)
        if o == "-u":
            update = 1
        if o == "-w":
            dumpwords = 1
        if o == "-W":
            dumpwids = 1
    ix = Indexer(datafs, writable=update or bulk, trans=trans, pack=pack)
    if dumpfreqs:
        ix.dumpfreqs()
    if dumpwords:
        ix.dumpwords()
    if dumpwids:
        ix.dumpwids()
    if dumpwords or dumpwids or dumpfreqs:
        return
    if bulk:
        if optimize:
            ix.optimize(args)
        ix.bulkupdate(args)
    elif update:
        ix.update(args)
    elif args:
        for i in range(len(args)):
            a = args[i]
            if " " in a:
                if a[0] == "-":
                    args[i] = '-"' + a[1:] + '"'
                else:
                    args[i] = '"' + a + '"'
        ix.query(" ".join(args), nbest, maxlines)
    else:
        ix.interact(nbest)
    if pack:
        ix.pack()

class Indexer:

    filestorage = database = connection = root = None

    def __init__(self, datafs, writable=0, trans=0, pack=0):
        self.trans_limit = trans
        self.pack_limit = pack
        self.trans_count = 0
        self.pack_count = 0
        self.stopdict = get_stopdict()
        self.mh = mhlib.MH()
        self.filestorage = FileStorage(datafs, read_only=(not writable))
        self.database = DB(self.filestorage)
        self.connection = self.database.open()
        self.root = self.connection.root()
        try:
            self.index = self.root["index"]
        except KeyError:
            self.index = self.root["index"] = TextIndex()
        try:
            self.docpaths = self.root["docpaths"]
        except KeyError:
            self.docpaths = self.root["docpaths"] = IOBTree()
        try:
            self.doctimes = self.root["doctimes"]
        except KeyError:
            self.doctimes = self.root["doctimes"] = IIBTree()
        try:
            self.watchfolders = self.root["watchfolders"]
        except KeyError:
            self.watchfolders = self.root["watchfolders"] = {}
        self.path2docid = OIBTree()
        for docid in self.docpaths.keys():
            path = self.docpaths[docid]
            self.path2docid[path] = docid
        try:
            self.maxdocid = max(self.docpaths.keys())
        except ValueError:
            self.maxdocid = 0
        print len(self.docpaths), "Document ids"
        print len(self.path2docid), "Pathnames"
        print self.index.lexicon.length(), "Words"

    def dumpfreqs(self):
        lexicon = self.index.lexicon
        index = self.index.index
        assert isinstance(index, OkapiIndex)
        L = []
        for wid in lexicon.wids():
            freq = 0
            for f in index._wordinfo.get(wid, {}).values():
                freq += f
            L.append((freq, wid, lexicon.get_word(wid)))
        L.sort()
        L.reverse()
        for freq, wid, word in L:
            print "%10d %10d %s" % (wid, freq, word)

    def dumpwids(self):
        lexicon = self.index.lexicon
        index = self.index.index
        assert isinstance(index, OkapiIndex)
        for wid in lexicon.wids():
            freq = 0
            for f in index._wordinfo.get(wid, {}).values():
                freq += f
            print "%10d %10d %s" % (wid, freq, lexicon.get_word(wid))

    def dumpwords(self):
        lexicon = self.index.lexicon
        index = self.index.index
        assert isinstance(index, OkapiIndex)
        for word in lexicon.words():
            wid = lexicon.get_wid(word)
            freq = 0
            for f in index._wordinfo.get(wid, {}).values():
                freq += f
            print "%10d %10d %s" % (wid, freq, word)

    def close(self):
        self.root = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        if self.database is not None:
            self.database.close()
            self.database = None
        if self.filestorage is not None:
            self.filestorage.close()
            self.filestorage = None

    def interact(self, nbest=NBEST, maxlines=MAXLINES):
        try:
            import readline
        except ImportError:
            pass
        text = ""
        top = 0
        results = []
        while 1:
            try:
                line = raw_input("Query: ")
            except EOFError:
                print "\nBye."
                break
            line = line.strip()
            if line.startswith("/"):
                self.specialcommand(line, results, top - nbest)
                continue
            if line:
                text = line
                top = 0
            else:
                if not text:
                    continue
            try:
                results, n = self.timequery(text, top + nbest)
            except KeyboardInterrupt:
                raise
            except:
                reportexc()
                text = ""
                continue
            if len(results) <= top:
                if not n:
                    print "No hits for %r." % text
                else:
                    print "No more hits for %r." % text
                text = ""
                continue
            print "[Results %d-%d from %d" % (top+1, min(n, top+nbest), n),
            print "for query %s]" % repr(text)
            self.formatresults(text, results, maxlines, top, top+nbest)
            top += nbest

    def specialcommand(self, line, results, first):
        assert line.startswith("/")
        line = line[1:]
        if not line:
            n = first
        else:
            try:
                n = int(line) - 1
            except:
                print "Huh?"
                return
        if n < 0 or n >= len(results):
            print "Out of range"
            return
        docid, score = results[n]
        path = self.docpaths[docid]
        i = path.rfind("/")
        assert i > 0
        folder = path[:i]
        n = path[i+1:]
        cmd = "show +%s %s" % (folder, n)
        if os.getenv("DISPLAY"):
            os.system("xterm -e  sh -c '%s | less' &" % cmd)
        else:
            os.system(cmd)

    def query(self, text, nbest=NBEST, maxlines=MAXLINES):
        results, n = self.timequery(text, nbest)
        if not n:
            print "No hits for %r." % text
            return
        print "[Results 1-%d from %d]" % (len(results), n)
        self.formatresults(text, results, maxlines)

    def timequery(self, text, nbest):
        t0 = time.time()
        c0 = time.clock()
        results, n = self.index.query(text, nbest)
        t1 = time.time()
        c1 = time.clock()
        print "[Query time: %.3f real, %.3f user]" % (t1-t0, c1-c0)
        return results, n

    def formatresults(self, text, results, maxlines=MAXLINES,
                      lo=0, hi=sys.maxint):
        stop = self.stopdict.has_key
        words = [w for w in re.findall(r"\w+\*?", text.lower()) if not stop(w)]
        pattern = r"\b(" + "|".join(words) + r")\b"
        pattern = pattern.replace("*", ".*") # glob -> re syntax
        prog = re.compile(pattern, re.IGNORECASE)
        print '='*70
        rank = lo
        qw = self.index.query_weight(text)
        for docid, score in results[lo:hi]:
            rank += 1
            path = self.docpaths[docid]
            score = 100.0*score/qw
            print "Rank:    %d   Score: %d%%   File: %s" % (rank, score, path)
            path = os.path.join(self.mh.getpath(), path)
            try:
                fp = open(path)
            except (IOError, OSError), msg:
                print "Can't open:", msg
                continue
            msg = mhlib.Message("<folder>", 0, fp)
            for header in "From", "To", "Cc", "Bcc", "Subject", "Date":
                h = msg.getheader(header)
                if h:
                    print "%-8s %s" % (header+":", h)
            text = self.getmessagetext(msg)
            if text:
                print
                nleft = maxlines
                for part in text:
                    for line in part.splitlines():
                        if prog.search(line):
                            print line
                            nleft -= 1
                            if nleft <= 0:
                                break
                    if nleft <= 0:
                        break
            print '-'*70

    def update(self, args):
        folder = None
        seqs = []

        for arg in args:
            if arg.startswith("+"):
                if folder is None:
                    folder = arg[1:]
                else:
                    print "only one folder at a time"
                    return
            else:
                seqs.append(arg)

        if not folder:
            folder = self.mh.getcontext()
        if not seqs:
            seqs = ['all']

        try:
            f = self.mh.openfolder(folder)
        except mhlib.Error, msg:
            print msg
            return

        dict = {}
        for seq in seqs:
            try:
                nums = f.parsesequence(seq)
            except mhlib.Error, msg:
                print msg or "unparsable message sequence: %s" % `seq`
                return
            for n in nums:
                dict[n] = n
        msgs = dict.keys()
        msgs.sort()

        self.updatefolder(f, msgs)
        self.commit()

    def optimize(self, args):
        uniqwords = {}
        for folder in args:
            if folder.startswith("+"):
                folder = folder[1:]
            print "\nOPTIMIZE FOLDER", folder
            try:
                f = self.mh.openfolder(folder)
            except mhlib.Error, msg:
                print msg
                continue
            self.prescan(f, f.listmessages(), uniqwords)
        L = [(uniqwords[word], word) for word in uniqwords.keys()]
        L.sort()
        L.reverse()
        for i in range(100):
            print "%3d. %6d %s" % ((i+1,) + L[i])
        self.index.lexicon.sourceToWordIds([word for (count, word) in L])

    def prescan(self, f, msgs, uniqwords):
        pipeline = [Splitter(), CaseNormalizer(), StopWordRemover()]
        for n in msgs:
            print "prescanning", n
            m = f.openmessage(n)
            text = self.getmessagetext(m, f.name)
            for p in pipeline:
                text = p.process(text)
            for word in text:
                uniqwords[word] = uniqwords.get(word, 0) + 1

    def bulkupdate(self, args):
        if not args:
            print "No folders specified; use ALL to bulk-index all folders"
            return
        if "ALL" in args:
            i = args.index("ALL")
            args[i:i+1] = self.mh.listfolders()
        for folder in args:
            if folder.startswith("+"):
                folder = folder[1:]
            print "\nFOLDER", folder
            try:
                f = self.mh.openfolder(folder)
            except mhlib.Error, msg:
                print msg
                continue
            self.updatefolder(f, f.listmessages())
            print "Total", len(self.docpaths)
        self.commit()
        print len(self.index.lexicon._words), "unique words."

    def updatefolder(self, f, msgs):
        self.watchfolders[f.name] = self.getmtime(f.name)
        for n in msgs:
            path = "%s/%s" % (f.name, n)
            docid = self.path2docid.get(path, 0)
            if docid and self.getmtime(path) == self.doctimes.get(docid, 0):
                print "unchanged", docid, path
                continue
            docid = self.newdocid(path)
            try:
                m = f.openmessage(n)
            except IOError:
                print "disappeared", docid, path
                self.unindexpath(path)
                continue
            text = self.getmessagetext(m, f.name)
            if not text:
                self.unindexpath(path)
                continue
            print "indexing", docid, path
            self.index.index_text(docid, text)
            self.maycommit()
        # Remove messages from the folder that no longer exist
        for path in list(self.path2docid.keys(f.name)):
            if not path.startswith(f.name + "/"):
                break
            if self.getmtime(path) == 0:
                self.unindexpath(path)
        print "done."

    def unindexpath(self, path):
        if self.path2docid.has_key(path):
            docid = self.path2docid[path]
            print "unindexing", docid, path
            del self.docpaths[docid]
            del self.doctimes[docid]
            del self.path2docid[path]
            try:
                self.index.unindex(docid)
            except KeyError, msg:
                print "KeyError", msg
            self.maycommit()

    def getmessagetext(self, m, name=None):
        L = []
        if name:
            L.append("_folder " + name) # To restrict search to a folder
            self.getheaders(m, L)
        try:
            self.getmsgparts(m, L, 0)
        except KeyboardInterrupt:
            raise
        except:
            print "(getmsgparts failed:)"
            reportexc()
        return L

    def getmsgparts(self, m, L, level):
        ctype = m.gettype()
        if level or ctype != "text/plain":
            print ". "*level + str(ctype)
        if ctype == "text/plain":
            L.append(m.getbodytext())
        elif ctype in ("multipart/alternative", "multipart/mixed"):
            for part in m.getbodyparts():
                self.getmsgparts(part, L, level+1)
        elif ctype == "message/rfc822":
            f = StringIO(m.getbodytext())
            m = mhlib.Message("<folder>", 0, f)
            self.getheaders(m, L)
            self.getmsgparts(m, L, level+1)

    def getheaders(self, m, L):
        H = []
        for key in "from", "to", "cc", "bcc", "subject":
            value = m.get(key)
            if value:
                H.append(value)
        if H:
            L.append("\n".join(H))

    def newdocid(self, path):
        docid = self.path2docid.get(path)
        if docid is not None:
            self.doctimes[docid] = self.getmtime(path)
            return docid
        docid = self.maxdocid + 1
        self.maxdocid = docid
        self.docpaths[docid] = path
        self.doctimes[docid] = self.getmtime(path)
        self.path2docid[path] = docid
        return docid

    def getmtime(self, path):
        path = os.path.join(self.mh.getpath(), path)
        try:
            st = os.stat(path)
        except os.error, msg:
            return 0
        return int(st[ST_MTIME])

    def maycommit(self):
        self.trans_count += 1
        if self.trans_count >= self.trans_limit > 0:
            self.commit()

    def commit(self):
        if self.trans_count > 0:
            print "committing..."
            transaction.commit()
            self.trans_count = 0
            self.pack_count += 1
            if self.pack_count >= self.pack_limit > 0:
                self.pack()

    def pack(self):
        if self.pack_count > 0:
            print "packing..."
            self.database.pack()
            self.pack_count = 0

class TextIndex(Persistent):

    def __init__(self):
        self.lexicon = Lexicon(Splitter(), CaseNormalizer(), StopWordRemover())
        self.index = OkapiIndex(self.lexicon)

    def index_text(self, docid, text):
        self.index.index_doc(docid, text)
        self._p_changed = 1 # XXX

    def unindex(self, docid):
        self.index.unindex_doc(docid)
        self._p_changed = 1 # XXX

    def query(self, query, nbest=10):
        # returns a total hit count and a mapping from docids to scores
        parser = QueryParser(self.lexicon)
        tree = parser.parseQuery(query)
        results = tree.executeQuery(self.index)
        if results is None:
            return [], 0
        chooser = NBest(nbest)
        chooser.addmany(results.items())
        return chooser.getbest(), len(results)

    def query_weight(self, query):
        parser = QueryParser(self.lexicon)
        tree = parser.parseQuery(query)
        terms = tree.terms()
        return self.index.query_weight(terms)

def reportexc():
    traceback.print_exc()

if __name__ == "__main__":
    sys.exit(main())
