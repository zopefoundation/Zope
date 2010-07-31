##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Script to check consistency of a ZCatalog
"""

import Zope2
import os,sys,re,getopt
from types import IntType
from BTrees.IIBTree import IISet,difference,intersection

def checkCatalog(path,indexes):
    """ perform some consistency checks on a ZCatalog instance"""

    root = Zope2.app()

    try:
        catalog = root.unrestrictedTraverse(path)
    except AttributeError:
        print 'Error: catalog object not found'
        sys.exit(1)

    # get Catalog instance
    _cat = catalog._catalog

    # check Catalog internal BTrees
    l_data  = list(_cat.data.keys())
    l_data.sort()
    l_uids  = list(_cat.uids.values())
    l_uids.sort()
    l_paths = list(_cat.data.keys())
    l_paths.sort()

    print "Checking catalog internal BTrees"
    print "\tINFO: Mapping data:  %d entries" % len(l_data)
    print "\tINFO: Mapping uids:  %d entries" % len(l_uids)
    print "\tINFO: Mapping paths: %d entries" % len(l_paths)

    if l_data == l_uids:
        print "\tOK:  Mapping data equals Mapping uids"
    else:
        print "\tERR: Mapping data does not equal Mapping uids"

    if l_data == l_paths:
        print "\tOK:  Mapping data equals Maaping paths"
    else:
        print "\tERR: Mapping data does not equal Maaping paths"


    # check BTrees of indexes

    for id,idx in _cat.indexes.items():

        if indexes and not idx.meta_type in indexes: continue

        print "Checking index '%s' (type: %s)" % (id, idx.meta_type)

        if idx.meta_type in ['FieldIndex','KeywordIndex']:

            # check forward entries
            RIDS = IISet()
            for key, rids in idx._index.items():
                if isinstance(rids,IntType):
                    RIDS.insert(  rids  )
                else:
                    map(RIDS.insert , rids.keys())

            diff = difference(RIDS, IISet(_cat.data.keys()))
            if len(diff)!=0:
                print '\tERR: Problem with forward entries'
                print '\tERR: too much forward entries:', diff
            else:
                print '\tOK:  Forward entries (%d entries)'  % (len(RIDS))


        elif idx.meta_type in ['PathIndex']:

            RIDS = IISet()

            for rids in map(None,idx._index.values()):
                map(RIDS.insert , rids.values()[0])

            diff = difference(RIDS, IISet(_cat.data.keys()))
            if len(diff)!=0:
                print '\tERR: Problem with forward entries'
                print '\tERR: too much forward entries:', diff
            else:
                print '\tOK:  Forward entries (%d entries)'  % (len(RIDS))


        if idx.meta_type in ['FieldIndex','KeywordIndex','PathIndex']:

            # check backward entries
            RIDS = IISet(idx._unindex.keys())
            diff = difference(RIDS, IISet(_cat.data.keys()))
            if len(diff)!=0:
                print '\tERR: Problem with backward entries'
                print '\tERR: too much backward entries:', diff
            else:
                print '\tOK:  Backward entries (%d entries)'  % (len(RIDS))







def usage():
    print "Usage: %s [--FieldIndex|KeywordIndex|PathIndex] /path/to/ZCatalog" % \
                os.path.basename(sys.argv[0])
    print
    print "This scripts checks the consistency of the internal"
    print "BTrees of a ZCatalog and its indexes."
    sys.exit(1)


def main():

    opts,args = getopt.getopt(sys.argv[1:],'h',\
            ['help','FieldIndex','KeywordIndex','PathIndex'])

    indexes = []

    for o,v in opts:

        if o in ['-h','--help']: usage()
        if o in ['--FieldIndex','--KeywordIndex','--PathIndex']:
            indexes.append(o[2:])

    checkCatalog(args,indexes)


if __name__=='__main__':
    main()
