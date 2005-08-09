#! /usr/bin/env python

import cPickle
import os.path
import sys

from hotshot.log import LogReader

def load_line_info(log):
    byline = {}
    prevloc = None
    for what, place, tdelta in log:
        if tdelta > 0:
            t, nhits = byline.get(prevloc, (0, 0))
            byline[prevloc] = (tdelta + t), (nhits + 1)
            prevloc = place
    return byline

def basename(path, cache={}):
    try:
        return cache[path]
    except KeyError:
        fn = os.path.split(path)[1]
        cache[path] = fn
        return fn

def print_results(results):
    for info, place in results:
        if place is None:
            # This is the startup time for the profiler, and only
            # occurs at the very beginning.  Just ignore it, since it
            # corresponds to frame setup of the outermost call, not
            # anything that's actually interesting.
            continue
        filename, line, funcname = place
        print '%8d %8d' % info, basename(filename), line

def annotate_results(results):
    files = {}
    for stats, place in results:
        if not place:
            continue
        time, hits = stats
        file, line, func = place
        l = files.get(file)
        if l is None:
            l = files[file] = []
        l.append((line, hits, time))
    order = files.keys()
    order.sort()
    for k in order:
        if os.path.exists(k):
            v = files[k]
            v.sort()
            annotate(k, v)

def annotate(file, lines):
    print "-" * 60
    print file
    print "-" * 60
    f = open(file)
    i = 1
    match = lines[0][0]
    for line in f:
        if match == i:
            print "%6d %8d " % lines[0][1:], line,
            del lines[0]
            if lines:
                match = lines[0][0]
            else:
                match = None
        else:
            print " " * 16, line,
        i += 1
    print

def get_cache_name(filename):
    d, fn = os.path.split(filename)
    cache_dir = os.path.join(d, '.hs-tool')
    cache_file = os.path.join(cache_dir, fn)
    return cache_dir, cache_file

def cache_results(filename, results):
    cache_dir, cache_file = get_cache_name(filename)
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    fp = open(cache_file, 'wb')
    try:
        cPickle.dump(results, fp, 1)
    finally:
        fp.close()

def main(filename, annotate):
    cache_dir, cache_file = get_cache_name(filename)

    if (  os.path.isfile(cache_file)
          and os.path.getmtime(cache_file) > os.path.getmtime(filename)):
        # cached data is up-to-date:
        fp = open(cache_file, 'rb')
        results = cPickle.load(fp)
        fp.close()
    else:
        log = LogReader(filename)
        byline = load_line_info(log)
        # Sort
        results = [(v, k) for k, v in byline.items()]
        results.sort()
        cache_results(filename, results)

    if annotate:
        annotate_results(results)
    else:
        print_results(results)


if __name__ == "__main__":
    import getopt

    annotate_p = 0
    opts, args = getopt.getopt(sys.argv[1:], 'A')
    for o, v in opts:
        if o == '-A':
            annotate_p = 1
    if args:
        filename, = args
    else:
        filename = "profile.dat"

    main(filename, annotate_p)
