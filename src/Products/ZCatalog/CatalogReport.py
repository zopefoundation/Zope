##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import time
import logging
from thread import allocate_lock

from Products.PluginIndexes.interfaces import IUniqueValueIndex

reportlock = allocate_lock()
reports = {}

MAX_DISTINCT_VALUES = 10

LOG = logging.getLogger('CatalogReport')


def determine_value_indexes(catalog):
    # This function determines all indexes whose values should be respected
    # in the report key. The number of unique values for the index needs to be
    # lower than the MAX_DISTINCT_VALUES watermark.

    # TODO: Ideally who would only consider those indexes with a small number
    # of unique values, where the number of items for each value differs a
    # lot. If the number of items per value is similar, the duration of a
    # query is likely similar as well.
    valueindexes = []
    for name, index in catalog.indexes.items():
        if IUniqueValueIndex.providedBy(index):
            values = index.uniqueValues()
            if values and len(values) < MAX_DISTINCT_VALUES:
                # Only consider indexes which actually return a number
                # greater than zero
                valueindexes.append(name)
    return frozenset(valueindexes)


def make_key(catalog,request):
    valueindexes = determine_value_indexes(catalog)
    
    if isinstance(request, dict):
        keydict = request.copy()
    else:
        keydict = {}
        keydict.update(request.keywords)
        if isinstance(request.request, dict):
            keydict.update(request.request)
    key = keys = keydict.keys()
    
    values = [name for name in keys if name in valueindexes]
    if values:
        # If we have indexes whose values should be considered, we first
        # preserve all normal indexes and then add the keys whose values
        # matter including their value into the key
        key = [name for name in keys if name not in values]
        for name in values:

            v = keydict.get(name, [])
            if type(v) in [type(tuple()),type(list())]:
                v = list(v)
                v.sort()

            # We need to make sure the key is immutable, repr() is an easy way
            # to do this without imposing restrictions on the types of values         
            key.append((name, repr(v)))

    key = tuple(sorted(key))

    return key

#
#
#
#######################################################################


class StopWatch(object):
    """ Simple stopwatch class """
    
    def __init__(self):
        self.init()
        
    def init(self):
        self.res = []
        self.start_time = None
        self.interim = {}
        self.stop_time = None

    def start(self):
        self.init()
        self.start_time = time.time()

    def split(self,label):

        current = time.time()
        start_time,stop_time = self.interim.get(label,(None,None))
        
        if start_time is None:
            self.interim[label] = (current,None)
            return
        
        self.interim[label] = (start_time,current)
        
        self.res.append((label, current - start_time))

    def stop(self):
        self.end_time = time.time()

    def result(self):
        return (self.end_time-self.start_time,tuple(self.res))


class CatalogReport(StopWatch):
    """ catalog report class to meassure and to identify slow catalog queries """

    def __init__(self, catalog, request=None, threshold=0):
        super(CatalogReport,self).__init__()
        
        self.catalog = catalog
        self.request = request
        self.threshold = threshold
        
        ## TODO: how to get an unique id?
        getPhysicalPath = getattr(catalog.aq_parent,'getPhysicalPath',lambda: ['','DummyCatalog'])
        self.cid = tuple(getPhysicalPath())

    def stop(self):
        super(CatalogReport,self).stop()
        self.log()
    
    def log(self):

        # query key
        key = make_key(self.catalog,self.request)

        # result of stopwatch
        res = self.result()

        if res[0] < self.threshold:
            return
        
        reportlock.acquire()
        try:
            if not reports.has_key(self.cid):
                reports[self.cid] = {}

            previous = reports[self.cid].get(key)
            if previous:
                counter , mean, last = previous
                mean = (mean*counter + res[0])/float(counter+1)
                reports[self.cid][key] = (counter+1,mean,res)
            else:
                reports[self.cid][key] = (1,res[0],res)

        finally:
            reportlock.release()


    def reset(self):
        reportlock.acquire()
        try:
            reports[self.cid] = {}
        finally:
            reportlock.release()        


    def report(self):
        """
        returns a statistic report of catalog queries as list of dicts as follows:

        [ { 'query':     <query_key>,
            'counter':   <hits>
            'duration':  <mean duration>,
            'last':      <details of recent query>,
          },

          ...,
        ]

        <details of recent query> := { 'duration': <duration of last query>,
                                       'details':  <duration of single indexes>,
                                     }

        
        <duration of single indexes> := [ { 'id':       <index_name1>,
                                            'duration': <duration>,
                                          },
                                          ...
                                        ]

        scale unit of duration is [ms]
 
        """

        rval = []
        for k,v in reports.get(self.cid,{}).items():
            info = {

                'query': k,
                'counter': v[0], 
                'duration':  v[1] * 1000,
                'last' : { 'duration' : v[2][0] * 1000,
                           'details'  : [dict(id=i[0],duration=i[1]*1000) for i in v[2][1]]
                         },
                }

            
            rval.append(info)
            
        return rval

    
