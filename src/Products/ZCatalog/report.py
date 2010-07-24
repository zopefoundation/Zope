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
            if values and len(values) < MAX_DISTINCT_VALUES:
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


def make_query(indexes, request):
    # This is a bit of a mess, but the ZCatalog API supports passing
    # in query restrictions in almost arbitary ways
    if isinstance(request, dict):
        query = request.copy()
    else:
        query = {}
        query.update(request.keywords)
        real_req = request.request
        if isinstance(real_req, dict):
            query.update(real_req)

        known_keys = query.keys()
        # The request has too many places where an index restriction might be
        # specified. Putting all of request.form, request.other, ... into the
        # key isn't what we want either, so we iterate over all known indexes
        # instead and see if they are in the request.
        for iid in indexes.keys():
            if iid in known_keys:
                continue
            value = real_req.get(iid)
            if value:
                query[iid] = value
    return query


def make_key(catalog, request):
    indexes = catalog.indexes
    valueindexes = determine_value_indexes(indexes)

    query = make_query(indexes, request)
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

    def split(self, label):
        current = time.time()
        start_time, stop_time = self.interim.get(label, (None, None))

        if start_time is None:
            self.interim[label] = (current, None)
            return

        self.interim[label] = (start_time, current)
        self.res.append((label, current - start_time))

    def stop(self):
        self.end_time = time.time()

    def result(self):
        return (self.end_time - self.start_time, tuple(self.res))


class CatalogReport(StopWatch):
    """Catalog report class to meassure and identify catalog queries.
    """

    def __init__(self, catalog, request=None, threshold=0.1):
        super(CatalogReport, self).__init__()

        self.catalog = catalog
        self.request = request
        self.threshold = threshold

        parent = aq_parent(catalog)
        path = getattr(aq_base(parent), 'getPhysicalPath', None)
        if path is None:
            path = ('', 'NonPersistentCatalog')
        else:
            path = tuple(parent.getPhysicalPath())
        self.cid = path

    def stop(self):
        super(CatalogReport, self).stop()
        self.log()

    def log(self):
        # result of stopwatch
        res = self.result()
        if res[0] < self.threshold:
            return

        # The key calculation takes a bit itself, we want to avoid that for
        # any fast queries. This does mean that slow queries get the key
        # calculation overhead added to their runtime.
        key = make_key(self.catalog, self.request)

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
                                          duration=i[1]*1000)
                                     for i in v[2][1]],
                        },
                }
            rval.append(info)

        return rval
