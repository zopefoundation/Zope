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
from collections import namedtuple
from thread import allocate_lock

from Acquisition import aq_base
from Acquisition import aq_parent
from Products.PluginIndexes.interfaces import IUniqueValueIndex

REPORTS_LOCK = allocate_lock()
REPORTS = {}

PRIORITYMAP_LOCK = allocate_lock()
PRIORITYMAP = {}

VALUE_INDEXES_LOCK = allocate_lock()
VALUE_INDEXES = frozenset()

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
    global VALUE_INDEXES
    if VALUE_INDEXES:
        # Calculating all the value indexes is quite slow, so we do this once
        # for the first query. Since this is an optimization only, slightly
        # outdated results based on index changes in the running process
        # can be ignored.
        return VALUE_INDEXES

    new_value_indexes = set()
    for name, index in indexes.items():
        if IUniqueValueIndex.providedBy(index):
            values = index.uniqueValues()
            if values and len(list(values)) < MAX_DISTINCT_VALUES:
                # Only consider indexes which actually return a number
                # greater than zero
                new_value_indexes.add(name)

    with VALUE_INDEXES_LOCK:
        VALUE_INDEXES = frozenset(new_value_indexes)

    return VALUE_INDEXES


def clear_value_indexes():
    global VALUE_INDEXES
    with VALUE_INDEXES_LOCK:
        VALUE_INDEXES = frozenset()


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


Duration = namedtuple('Duration', ['start', 'end'])
IndexMeasurement = namedtuple('IndexMeasurement',
                              ['name', 'duration', 'num'])
Benchmark = namedtuple('Benchmark', ['num', 'duration', 'hits'])
RecentQuery = namedtuple('RecentQuery', ['duration', 'details'])
Report = namedtuple('Report', ['hits', 'duration', 'last'])


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

    def benchmark(self):
        # holds the benchmark of each index
        bm = PRIORITYMAP.get(self.key, None)
        if bm is None:
            with PRIORITYMAP_LOCK:
                PRIORITYMAP[self.key] = {}
        return bm

    def plan(self):
        benchmark = self.benchmark()
        if not benchmark:
            return None

        # sort indexes on (mean result length, mean search time)
        ranking = [((value.num, value.duration), name)
                   for name, value in benchmark.items()]
        ranking.sort()
        return [r[1] for r in ranking]

    def start(self):
        self.init_timer()
        self.start_time = time.time()

    def start_split(self, name, result=None):
        self.interim[name] = Duration(time.time(), None)

    def stop_split(self, name, result=None):
        current = time.time()
        start_time, stop_time = self.interim.get(name, Duration(None, None))
        length = 0
        if result is not None:
            # TODO: calculating the length can be expensive
            length = len(result)
        self.interim[name] = Duration(start_time, current)
        dt = current - start_time
        self.res.append(IndexMeasurement(
            name=name, duration=current - start_time, num=length))

        # remember index's hits, search time and calls
        benchmark = self.benchmark()
        if name not in benchmark:
            with PRIORITYMAP_LOCK:
                benchmark[name] = Benchmark(num=length, duration=dt, hits=1)
        else:
            num, duration, hits = benchmark[name]
            num = int(((num * hits) + length) / float(hits + 1))
            duration = ((duration * hits) + dt) / float(hits + 1)
            # reset adaption
            if hits % REFRESH_RATE == 0:
                hits = 0
            hits += 1
            with PRIORITYMAP_LOCK:
                benchmark[name] = Benchmark(num, duration, hits)

    def stop(self):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

        key = self.key
        benchmark = self.benchmark()

        with PRIORITYMAP_LOCK:
            PRIORITYMAP[key] = benchmark

        self.log()

    def log(self):
        # result of stopwatch
        total = self.duration
        if total < self.threshold:
            return

        key = self.key
        recent = RecentQuery(duration=total, details=self.res)

        with REPORTS_LOCK:
            if self.cid not in REPORTS:
                REPORTS[self.cid] = {}

            previous = REPORTS[self.cid].get(key)
            if previous:
                counter, mean, last = previous
                mean = (mean * counter + total) / float(counter + 1)
                REPORTS[self.cid][key] = Report(counter + 1, mean, recent)
            else:
                REPORTS[self.cid][key] = Report(1, total, recent)

    def reset(self):
        with REPORTS_LOCK:
            REPORTS[self.cid] = {}

    def report(self):
        """Returns a statistic report of catalog queries as list of dicts.
        The duration is provided in millisecond.
        """
        rval = []
        for key, report in REPORTS.get(self.cid, {}).items():
            last = report.last
            info = {
                'query': key,
                'counter': report.hits,
                'duration': report.duration * 1000,
                'last': {'duration': last.duration * 1000,
                         'details': [dict(id=d.name,
                                          duration=d.duration * 1000,
                                          length=d.num)
                                     for d in last.details],
                        },
                }
            rval.append(info)

        return rval
