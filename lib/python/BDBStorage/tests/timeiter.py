#! /usr/bin/env python

##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Time transaction commits and normalize vs. pickle size and #objects.

Actually just counts the size of pickles in the transaction via the iterator
protocol, so storage overheads aren't counted.

Usage: %(PROGRAM)s [options]
Options:
    -h/--help
        Print this message and exit.

    -s filename
    --source=filename
        Use database in filename as the source (must be a FileStorage)

    -d filename
    --dest=filename
        Use database in filename as the destination (must be a BDB storage)

    -o filename
    --output=filename
        Print results in filename, otherwise stdout.

    -m txncount
    --max=txncount
        Stop after committing txncount transactions.

    -k txncount
    --skip=txncount
        Skip the first txncount transactions.

    -p/--profile
        Turn on specialized profiling.

    -q/--quiet
        Be quite.
"""

import sys
import os
import getopt
import time
import errno
import profile
import traceback
import marshal

from bsddb3 import db

from ZODB import utils
from persistent.TimeStamp import TimeStamp
from ZODB.FileStorage import FileStorage
from BDBStorage.BDBFullStorage import BDBFullStorage

PROGRAM = sys.argv[0]
ZERO = '\0'*8



def usage(code, msg=''):
    print >> sys.stderr, __doc__ % globals()
    if msg:
        print >> sys.stderr, msg
    sys.exit(code)



def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hs:d:qo:l:pm:k:',
                                   ['help', 'source=', 'dest=', 'quiet',
                                    'output=', 'logfile=', 'profile',
                                    'max=', 'skip='])
    except getopt.error, msg:
        usage(1, msg)

    class Options:
        source = None
        dest = None
        verbose = 1
        outfile = None
        logfile = None
        profilep = 0
        maxtxn = -1
        skiptxn = -1

    options = Options()

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-s', '--source'):
            options.source = arg
        elif opt in ('-d', '--dest'):
            options.dest = arg
        elif opt in ('-q', '--quiet'):
            options.verbose = 0
        elif opt in ('-o', '--output'):
            options.outfile = arg
        elif opt in ('-l', '--logfile'):
            options.logfile = arg
        elif opt in ('-p', '--profile'):
            options.profilep = 1
        elif opt in ('-m', '--max'):
            options.maxtxn = int(arg)
        elif opt in ('-k', '--skip'):
            options.skiptxn = int(arg)

    if args:
        usage(1)

    if not options.source or not options.dest:
        usage(1, 'Source and destination databases must be provided')

    # Open the output file
    if options.outfile is None:
        options.outfp = sys.stdout
        options.outclosep = 0
    else:
        options.outfp = open(options.outfile, 'w')
        options.outclosep = 1

    # Open the logfile
    if options.logfile is None:
        options.logfp = sys.stdout
        options.logclosep = 0
    else:
        options.logfp = open(options.logfile, 'w')
        options.logclosep = 1

    # Print a comment, this is a hack
    print >> options.outfp, '# FS->BDB 3.3.11'
    print >> options.outfp, '#', time.ctime()

    print >>sys.stderr, 'Opening source FileStorage...'
    t0 = time.time()
    srcdb = FileStorage(options.source, read_only=1)
    t1 = time.time()
    print >>sys.stderr, 'Opening source FileStorage done. %s seconds' % (t1-t0)
#
# Uncomment this section to do a FS->BDB migration
#
    print >>sys.stderr, 'Opening destination BDB...'
    t0 = time.time()
    dstdb = BDBFullStorage(options.dest)
    t1 = time.time()
    print >>sys.stderr, 'Opening destination BDB done. %s seconds' % (t1-t0)

#
# Uncomment this section to do a FS->FS migration
#
##    print >>sys.stderr, 'Opening destination FileStorage...'
##    t0 = time.time()
##    dstdb = FileStorage(dest)
##    t1 = time.time()
##    print >>sys.stderr, 'Opening destination FileStorage done. %s seconds' % (
##        t1-t0)

    try:
        t0 = time.time()
        doit(srcdb, dstdb, options)
        t1 = time.time()
        print 'Total time:', t1-t0
    finally:
        # Done
        srcdb.close()
        dstdb.close()
        if options.outclosep:
            options.outfp.close()
        if options.logclosep:
            options.logfp.close()



def doit(srcdb, dstdb, options):
    outfp = options.outfp
    logfp = options.logfp
    profilep = options.profilep
    verbose = options.verbose
    # some global information
    largest_pickle = 0
    largest_txn_in_size = 0
    largest_txn_in_objects = 0
    # Ripped from BaseStorage.copyTransactionsFrom()
    ts = None
    ok = 1
    prevrevids = {}
    counter = 0
    skipper = 0
    for txn in srcdb.iterator():
        skipper += 1
        if skipper <= options.skiptxn:
            continue
        counter += 1
        if counter > options.maxtxn > 0:
            break
        tid = txn.tid
        if ts is None:
            ts = TimeStamp(tid)
        else:
            t = TimeStamp(tid)
            if t <= ts:
                if ok:
                    print 'Time stamps are out of order %s, %s' % (ts, t)
                    ok = 0
                    ts = t.laterThan(ts)
                    tid = `ts`
                else:
                    ts = t
                    if not ok:
                        print 'Time stamps are back in order %s' % t
                        ok = 1
        if verbose:
            print ts

        prof = None
        if profilep and (counter % 100) == 0:
            prof = profile.Profile()
        objects = 0
        size = 0
        t0 = time.time()
        dstdb.tpc_begin(txn, tid, txn.status)
        t1 = time.time()
        try:
            for r in txn:
                oid = r.oid
                objects += 1
                thissize = len(r.data)
                size += thissize
                if thissize > largest_pickle:
                    largest_pickle = thissize
                if verbose:
                    if not r.version:
                        vstr = 'norev'
                    else:
                        vstr = r.version
                    print utils.U64(oid), vstr, len(r.data)
                oldrevid = prevrevids.get(oid, ZERO)
                newrevid = dstdb.store(oid, oldrevid, r.data, r.version, txn)
                prevrevids[oid] = newrevid
            t2 = time.time()
            dstdb.tpc_vote(txn)
            t3 = time.time()
            # Profile every 100 transactions
            if prof:
                prof.runcall(dstdb.tpc_finish, txn)
            else:
                dstdb.tpc_finish(txn)
            t4 = time.time()
        except KeyError, e:
            traceback.print_exc(file=logfp)

        # record the results
        if objects > largest_txn_in_objects:
            largest_txn_in_objects = objects
        if size > largest_txn_in_size:
            largest_txn_in_size = size
        print >> outfp, utils.U64(tid), objects, size, t4-t0, \
              t1-t0, t2-t1, t3-t2, t4-t3

        if prof:
            prof.create_stats()
            fp = open('profile-%02d.txt' % (counter / 100), 'wb')
            marshal.dump(prof.stats, fp)
            fp.close()
    print >> outfp, largest_pickle, largest_txn_in_size, largest_txn_in_objects



if __name__ == '__main__':
    main()
