#! /usr/bin/env python2.1

"""MH mail indexer."""

import re
import sys
import time
import mhlib
import getopt
import traceback
from StringIO import StringIO

DATAFS = "/home/guido/.Data.fs"
ZOPECODE = "/home/guido/projects/ds9/lib/python"

sys.path.append(ZOPECODE)

from ZODB import DB
from ZODB.FileStorage import FileStorage
from Persistence import Persistent
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree

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
        opts, args = getopt.getopt(sys.argv[1:], "bd:m:n:Opu")
    except getopt.error, msg:
        print msg
        sys.exit(2)
    update = 0
    bulk = 0
    optimize = 0
    nbest = NBEST
    maxlines = MAXLINES
    datafs = DATAFS
    pack = 0
    for o, a in opts:
        if o == "-b":
            bulk = 1
        if o == "-d":
            datafs = a
        if o == "-m":
            maxlines = int(a)
        if o == "-n":
            nbest = int(a)
        if o == "-O":
            optimize = 1
        if o == "-p":
            pack = 1
        if o == "-u":
            update = 1
    ix = Indexer(datafs, update or bulk)
    if bulk:
        if optimize:
            ix.optimize(args)
        ix.bulkupdate(args)
    elif update:
        ix.update(args)
        if pack:
            ix.pack()
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

class Indexer:

    filestorage = database = connection = root = None

    def __init__(self, datafs, writable=0):
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
        while 1:
            try:
                line = raw_input("Query: ")
            except EOFError:
                print "\nBye."
                break
            line = line.strip()
            if line:
                text = line
                top = 0
            else:
                if not text:
                    continue
            try:
                results, n = self.timequery(text, top + nbest)
            except:
                reportexc()
                text = ""
                top = 0
                continue
            if len(results) <= top:
                if not n:
                    print "No hits for %r." % text
                else:
                    print "No more hits for %r." % text
                text = ""
                top = 0
                continue
            print "[Results %d-%d from %d" % (top+1, min(n, top+nbest), n),
            print "for query %s]" % repr(text)
            self.formatresults(text, results, maxlines, top, top+nbest)
            top += nbest

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
        qw = max(1, self.index.query_weight(text))
        factor = 100.0 / qw / 1024
        for docid, score in results[lo:hi]:
            rank += 1
            path = self.docpaths[docid]
            score = min(100, int(score * factor))
            print "Rank:    %d   Score: %d%%   File: %s" % (rank, score, path)
            fp = open(path)
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
            text = self.getmessagetext(m)
            for p in pipeline:
                text = p.process(text)
            for word in text:
                uniqwords[word] = uniqwords.get(word, 0) + 1

    def bulkupdate(self, args):
        chunk = 5000
        target = len(self.docpaths) + chunk
        for folder in args:
            if len(self.docpaths) >= target:
                self.pack()
                target = len(self.docpaths) + chunk
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
        self.pack()
        print "Indexed", self.index.lexicon._nbytes, "bytes and",
        print self.index.lexicon._nwords, "words;",
        print len(self.index.lexicon._words), "unique words."

    def updatefolder(self, f, msgs):
        done = 0
        new = 0
        for n in msgs:
            print "indexing", n
            m = f.openmessage(n)
            text = self.getmessagetext(m)
            path = f.getmessagefilename(n)
            self.unindexpath(path)
            if not text:
                continue
            docid = self.newdocid(path)
            self.index.index_text(docid, text)
            done += 1
            new = 1
            if done%500 == 0:
                self.commit()
                new = 0
        if new:
            self.commit()
        print "done."

    def unindexpath(self, path):
        if self.path2docid.has_key(path):
            docid = self.path2docid[path]
            print "unindexing", docid, path
            del self.docpaths[docid]
            del self.path2docid[path]
            try:
                self.index.unindex(docid)
            except KeyError, msg:
                print "KeyError", msg

    def getmessagetext(self, m):
        L = []
        try:
            self.getmsgparts(m, L, 0)
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
            self.getmsgparts(m, L, level+1)

    def newdocid(self, path):
        docid = self.maxdocid + 1
        self.maxdocid = docid
        self.docpaths[docid] = path
        self.path2docid[path] = docid
        return docid

    def commit(self):
        print "committing..."
        get_transaction().commit()

    def pack(self):
        print "packing..."
        self.database.pack()

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
    main()
