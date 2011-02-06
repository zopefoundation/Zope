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

""" 
A utility to perform external reindex operations for ZCatalogs

Usage:

   zopectl run reindex_catalog.py [options]

   Use --help to get a list of all options.

Author: Andreas Jung (andreas@andreas-jung.com)

$Id$
"""

import sys
from optparse import OptionParser

import transaction
from Products.ZCatalog.ProgressHandler import StdoutHandler


def path2catalog(path):
    """ lookup catalog by path """

    catalog = app.restrictedTraverse(path, None)
    if not catalog:
        raise ValueError('No catalog found at %s' % path)
    return catalog


def getHandler(options):
    """ return a progress handler """
    
    if options.silent:
        return None
    else:
        return StdoutHandler(options.steps)


def listIndexes(options, args):
    """ print a list of all indexes to stdout """

    catalog = path2catalog(options.catalog)
    indexes = catalog._catalog.indexes    

    print 'Listing of all indexes at %s' % options.catalog
    print

    for id, idx in indexes.items():
        print '%-20s %-50s %d' % (id, idx.meta_type, idx.numObjects())


def reindexIndexes(optioons, args):
    """ reindex given list of indexes """

    catalog = path2catalog(options.catalog)
    handler = getHandler(options)

    for id in args:
        print 'Reindexing index %s at %s' % (id, options.catalog)
        catalog.reindexIndex(id, None, handler)
    transaction.commit()


def refreshMetadata(options, args):
    """ reindex metadata """

    catalog = path2catalog(options.catalog)
    handler = getHandler(options)

    print 'Refresh metadata at %s' % options.catalog
    catalog.refreshMetadata(handler)
    transaction.commit()


def reindexAll(options, args):
    """ reindex complete catalog """

    catalog = path2catalog(options.catalog)
    handler = getHandler(options)

    print 'Reindexing complete ZCatalog at %s' % options.catalog
    catalog.refreshCatalog(options.clearCatalog, handler)
    transaction.commit()


if __name__ == '__main__':
   
    parser = OptionParser()
    parser.add_option('-c', '--catalog', dest='catalog',
                     help='path to ZCatalog')
    parser.add_option('-i', '--indexes', action="store_true", dest="listIndexes",
                     help='list all indexes')
    parser.add_option('-C', '--clear', action="store_true", dest="clearCatalog", default=False,
                     help='clear catalog before reindexing the complete catalog (--all only)')
    parser.add_option('-a', '--all', action="store_true", dest="reindexAll",
                     help='reindex the complete catalog and update all metadata')
    parser.add_option('-r', '--reindex', action="store_true", dest="reindexIndexes",
                     help='reindex specified indexes')
    parser.add_option('-m', '--metadata', action="store_true", dest="refreshMetadata",
                     help='refresh all metadata')
    parser.add_option('-n', '--steps', dest="steps", default=100, type="int",
                     help='log progress every N objects')
    parser.add_option('-s', '--silent', action="store_true", dest="silent", default=False,
                     help='do not log reindexing progress to stdout')

    options,args = parser.parse_args()

    if options.listIndexes: listIndexes(options, args)
    if options.reindexIndexes: reindexIndexes(options, args)
    if options.refreshMetadata: refreshMetadata(options, args)
    if options.reindexAll: reindexAll(options, args)
