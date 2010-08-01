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
from thread import allocate_lock

from Acquisition import aq_base
from Acquisition import aq_parent
from Products.PluginIndexes.interfaces import IUniqueValueIndex

reports_lock = allocate_lock()
reports = {}

value_indexes_lock = allocate_lock()
value_indexes = frozenset()

MAX_DISTINCT_VALUES = 10
REFRESH_RATE = 100


def determine_value_indexes(indexes):
    # This function determines all indexes whose values should be respected
    # in the report key. The number of unique values for the index needs to be
    # lower than the MAX_DISTINCT_VALUES watermark.

    # TODO: Ideally who would only consider those indexes with a small number
    # of unique values, where the number of items for each value differs a
    # lot. If the number of items per value is similar, the duration of a
    # query is likely similar as well.
    global value_indexes
    if value_indexes:
        # Calculating all the value indexes is quite slow, so we do this once
        # for the first query. Since this is an optimization only, slightly
        # outdated results based on index changes in the running process
        # can be ignored.
        return value_indexes

    new_value_indexes = set()
    for name, index in indexes.items():
        if IUniqueValueIndex.providedBy(index):
            values = index.uniqueValues()
            if values and len(list(values)) < MAX_DISTINCT_VALUES:
                # Only consider indexes which actually return a number
                # greater than zero
                new_value_indexes.add(name)
    try:
        value_indexes_lock.acquire()
        value_indexes = frozenset(new_value_indexes)
    finally:
        value_indexes_lock.release()

    return value_indexes


def clear_value_indexes():
    global value_indexes
    try:
        value_indexes_lock.acquire()
        value_indexes = frozenset()
    finally:
        value_indexes_lock.release()


from zope.testing.cleanup import addCleanUp
addCleanUp(clear_value_indexes)
del addCleanUp


def make_key(catalog, query):
    if not query:
        return None

    indexes = catalog.indexes
    valueindexes = determine_value_indexes(indexes)
    key = keys = query.keys()

    values = [name for name in keys if name in valueindexes]
    if values:
        # If we have indexes whose values should be considered, we first
        # preserve all normal indexes and then add the keys whose values
        # matter including their value into the key
        key = [name for name in keys if name not in values]
        for name in values:

            v = query.get(name, [])
            if isinstance(v, (tuple, list)):
                v = list(v)
                v.sort()

            # We need to make sure the key is immutable, repr() is an easy way
            # to do this without imposing restrictions on the types of values
            key.append((name, repr(v)))

    key = tuple(sorted(key))
    return key


class CatalogPlan(object):
    """Catalog plan class to measure and identify catalog queries and plan
    their execution.
    """

    def __init__(self, catalog, query=None, threshold=0.1):
        self.catalog = catalog
        self.query = query
        self.key = make_key(catalog, query)
        self.threshold = threshold
        self.cid = self.get_id()
        self.init_timer()

    def get_id(self):
        parent = aq_parent(self.catalog)
        path = getattr(aq_base(parent), 'getPhysicalPath', None)
        if path is None:
            path = ('', 'NonPersistentCatalog')
        else:
            path = tuple(parent.getPhysicalPath())
        return path

    def init_timer(self):
        self.res = []
        self.start_time = None
        self.interim = {}
        self.stop_time = None
        self.duration = None

    def prioritymap(self):
        # holds the benchmark of each index
        prioritymap = getattr(self.catalog, '_v_prioritymap', None)
        if prioritymap is None:
            prioritymap = self.catalog._v_prioritymap = {}
        return prioritymap

    def benchmark(self):
        # holds the benchmark of each index
        bm = self.prioritymap().get(self.key, None)
        if bm is None:
            self.prioritymap()[self.key] = {}
        return bm

    def plan(self):
        benchmark = self.benchmark()
        if not benchmark:
            return None

        # sort indexes on (mean hits, mean search time)
        ranking = [((v[0], v[1]), k) for k, v in benchmark.items()]
        ranking.sort()
        return [i[1] for i in ranking]

    def start(self):
        self.init_timer()
        self.start_time = time.time()

    def start_split(self, label, result=None):
        self.interim[label] = (time.time(), None)

    def stop_split(self, name, result=None):
        current = time.time()
        start_time, stop_time = self.interim.get(name, (None, None))
        length = 0
        if result is not None:
            # TODO: calculating the length can be expensive
            length = len(result)
        self.interim[name] = (start_time, current)
        dt = current - start_time
        self.res.append((name, current - start_time, length))

        # remember index's hits, search time and calls
        benchmark = self.benchmark()
        if name not in benchmark:
            benchmark[name] = (length, dt, 1)
        else:
            n, t, c = benchmark[name]
            n = int(((n*c) + length) / float(c + 1))
            t = ((t*c) + dt) / float(c + 1)
            # reset adaption
            if c % REFRESH_RATE == 0:
                c = 0
            c += 1
            benchmark[name] = (n, t, c)

    def stop(self):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

        key = self.key
        benchmark = self.benchmark()
        prioritymap = self.prioritymap()
        prioritymap[key] = benchmark

        # calculate mean time of search
        stats = getattr(self.catalog, '_v_stats', None)
        if stats is None:
            stats = self.catalog._v_stats = {}

        if key not in stats:
            mt = self.duration
            c = 1
        else:
            mt, c = stats[key]
            mt = ((mt * c) + self.duration) / float(c + 1)
            c += 1

        stats[key] = (mt, c)
        self.log()

    def result(self):
        return (self.duration, tuple(self.res))

    def log(self):
        # result of stopwatch
        res = self.result()
        if res[0] < self.threshold:
            return

        key = self.key
        reports_lock.acquire()
        try:
            if self.cid not in reports:
                reports[self.cid] = {}

            previous = reports[self.cid].get(key)
            if previous:
                counter, mean, last = previous
                mean = (mean * counter + res[0]) / float(counter + 1)
                reports[self.cid][key] = (counter + 1, mean, res)
            else:
                reports[self.cid][key] = (1, res[0], res)

        finally:
            reports_lock.release()

    def reset(self):
        reports_lock.acquire()
        try:
            reports[self.cid] = {}
        finally:
            reports_lock.release()

    def report(self):
        """Returns a statistic report of catalog queries as list of dicts as
        follows:

        [{'query': <query_key>,
          'counter': <hits>
          'duration': <mean duration>,
          'last': <details of recent query>,
         },
         ...
        ]

        <details of recent query> := {'duration': <duration of last query>,
                                      'details': <duration of single indexes>,
                                     }

        <duration of single indexes> := [{'id': <index_name1>,
                                          'duration': <duration>,
                                          'length': <resultset length>,
                                         },
                                         ...
                                        ]

        The duration is provided in millisecond.
        """
        rval = []
        for k, v in reports.get(self.cid, {}).items():
            info = {
                'query': k,
                'counter': v[0],
                'duration': v[1] * 1000,
                'last': {'duration': v[2][0] * 1000,
                         'details': [dict(id=i[0],
                                          duration=i[1]*1000,
                                          length=i[2])
                                     for i in v[2][1]],
                        },
                }
            rval.append(info)

        return rval
