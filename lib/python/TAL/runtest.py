# runtest.py

import sys
import os
import string
from cStringIO import StringIO
import glob

import driver

def showdiff(a, b):
    import ndiff
    cruncher = ndiff.SequenceMatcher(ndiff.IS_LINE_JUNK, a, b)
    for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
        if tag == 'replace':
            print nicerange(alo, ahi) + "r" + nicerange(blo, bhi)
            ndiff.dump('<', a, alo, ahi)
            print "---"
            ndiff.dump('>', b, blo, bhi)
        elif tag == 'delete':
            print nicerange(alo, ahi) + "d" + nicerange(blo, bhi)
            ndiff.dump('<', a, alo, ahi)
        elif tag == 'insert':
            print nicerange(alo, ahi), "i", nicerange(blo, bhi)
            ndiff.dump('>', b, blo, bhi)
        elif tag == 'equal':
            pass
        else:
            raise ValueError, 'unknown tag ' + `tag`

def nicerange(lo, hi):
    if hi <= lo+1:
        return str(lo+1)
    else:
        return "%d,%d" % (lo+1, hi)

def main():
    opts = []
    args = sys.argv[1:]
    while args and args[0][:1] == '-':
        opts.append(args[0])
        del args[0]
    if not args:
        args = glob.glob(os.path.join("test", "test*.xml"))
    for arg in args:
        print
        print arg,
        sys.stdout.flush()
        save = sys.stdout, sys.argv
        try:
            sys.stdout = stdout = StringIO()
            sys.argv = [""] + opts + [arg]
            driver.main()
        finally:
            sys.stdout, sys.argv = save
        head, tail = os.path.split(arg)
        outfile = os.path.join(
            head,
            string.replace(tail, "test", "out"))
        try:
            f = open(outfile)
        except IOError:
            expected = None
        else:
            expected = f.readlines()
            f.close()
        stdout.seek(0)
        actual = stdout.readlines()
        if actual == expected:
            print "OK"
        else:
            print "not OK"
            showdiff(expected, actual)

if __name__ == "__main__":
    main()
