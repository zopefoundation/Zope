import os
from time import clock

import ZODB
from ZODB.FileStorage import FileStorage

QUERIES = ["nested recursive functions",
           "explicit better than implicit",
           "build hpux",
           "cannot create 'method-wrapper' instances",
            "extension module C++",
           "class method",
           "instance variable",
           "articulate information",
           "import default files",
           "gopher ftp http",
           ]

def main(rt):
    index = rt["index"]
    files = rt["files"]
    times = {}
    for i in range(11):
        for q in QUERIES:
            terms = q.split()
            for c in " OR ", " AND ":
                query = c.join(terms)
                t0 = clock()
                results, num = index.query(query)
                t1 = clock()
                print num, query, t1 - t0
                key = query
                if i == 0:
                    for docid, score in results:
                        print score, files[docid]
                    continue
                l = times.setdefault(key, [])
                l.append(t1 - t0)

    l = times.keys()
    l.sort()
    print
    for k in l:
        v = times[k]
        print min(v), k, " ".join(map(str, v))

if __name__ == "__main__":
    import sys
    import getopt
    
    VERBOSE = 0
    FSPATH = "Data.fs"

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

    fs = FileStorage(FSPATH, read_only=1)
    db = ZODB.DB(fs)
    cn = db.open()
    rt = cn.root()
    main(rt)

