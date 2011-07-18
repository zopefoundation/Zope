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
'''Cache management support.

This class is mixed into the database manager in App.ApplicationManager.
'''

from AccessControl.class_init import InitializeClass
from App.special_dtml import DTMLFile
from App.ImageFile import ImageFile
from DateTime.DateTime import DateTime

class CacheManager:
    """Cache management mix-in
    """
    _cache_age = 60
    _vcache_age = 60
    _history_length = 3600  # Seconds

    manage_cacheParameters = DTMLFile('dtml/cacheParameters', globals())
    manage_cacheGC = DTMLFile('dtml/cacheGC', globals())

    transparent_bar = ImageFile('www/transparent_bar.gif', globals())
    store_bar = ImageFile('www/store_bar.gif', globals())
    load_bar = ImageFile('www/load_bar.gif', globals())

    def _getDB(self):
        return self._p_jar.db()

    def cache_length(self):
        return self._getDB().cacheSize()

    def cache_length_bytes(self):
        return self._getDB().getCacheSizeBytes()

    def cache_detail_length(self):
        return self._getDB().cacheDetailSize()

    def database_size(self):
        return self._getDB().objectCount()

    def cache_age(self):
        return self._cache_age

    def manage_cache_age(self,value,REQUEST):
        "set cache age"
        db = self._getDB()
        self._cache_age = value
        db.setCacheDeactivateAfter(value)

        if REQUEST is not None:
            response=REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1']+'/manage_cacheParameters')

    def cache_size(self):
        db = self._getDB()
        return db.getCacheSize()

    def manage_cache_size(self,value,REQUEST):
        "set cache size"
        db = self._getDB()
        db.setCacheSize(value)

        if REQUEST is not None:
            response=REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1']+'/manage_cacheParameters')

    def manage_full_sweep(self,value,REQUEST):
        "Perform a full sweep through the cache"
        db = self._getDB()
        db.cacheFullSweep(value)

        if REQUEST is not None:
            response=REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1']+'/manage_cacheGC')

    def manage_minimize(self,value=1,REQUEST=None):
        "Perform a full sweep through the cache"
        # XXX Add a deprecation warning about value?
        self._getDB().cacheMinimize()

        if REQUEST is not None:
            response=REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1']+'/manage_cacheGC')

    def cache_detail(self, REQUEST=None):
        """
        Returns the name of the classes of the objects in the cache
        and the number of objects in the cache for each class.
        """
        detail = self._getDB().cacheDetail()
        if REQUEST is not None:
            # format as text
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
            return '\n'.join('%6d %s'%(count, name) for count, name in detail)
        else:
            # raw
            return detail

    def cache_extreme_detail(self, REQUEST=None):
        """
        Returns information about each object in the cache.
        """
        detail = self._getDB().cacheExtremeDetail()
        if REQUEST is not None:
            # sort the list.
            lst = [((dict['conn_no'], dict['oid']), dict) for dict in detail]
            # format as text.
            res = [
                '# Table shows connection number, oid, refcount, state, '
                'and class.',
                '# States: L = loaded, G = ghost, C = changed']
            for sortkey, dict in lst:
                id = dict.get('id', None)
                if id:
                    idinfo = ' (%s)' % id
                else:
                    idinfo = ''
                s = dict['state']
                if s == 0:
                    state = 'L'  # loaded
                elif s == 1:
                    state = 'C'  # changed
                else:
                    state = 'G'  # ghost
                res.append('%d %-34s %6d %s %s%s' % (
                    dict['conn_no'], `dict['oid']`, dict['rc'],
                    state, dict['klass'], idinfo))
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
            return '\n'.join(res)
        else:
            # raw
            return detail

    def _getActivityMonitor(self):
        db = self._getDB()
        if not hasattr(db, 'getActivityMonitor'):
            return None
        am = db.getActivityMonitor()
        if am is None:
            return None
        return am

    def getHistoryLength(self):
        am = self._getActivityMonitor()
        if am is None:
            return 0
        return am.getHistoryLength()

    def manage_setHistoryLength(self, length, REQUEST=None):
        """Change the length of the activity monitor history.
        """
        am = self._getActivityMonitor()
        length = int(length)
        if length < 0:
            raise ValueError, 'length can not be negative'
        if am is not None:
            am.setHistoryLength(length)
        self._history_length = length  # Restore on startup

        if REQUEST is not None:
            response = REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1'] + '/manage_activity')

    def getActivityChartData(self, segment_height, REQUEST=None):
        """Returns information for generating an activity chart.
        """
        am = self._getActivityMonitor()
        if am is None:
            return None

        if REQUEST is not None:
            start = float(REQUEST.get('chart_start', 0))
            end = float(REQUEST.get('chart_end', 0))
            divisions = int(REQUEST.get('chart_divisions', 10))
            analysis = am.getActivityAnalysis(start, end, divisions)
        else:
            analysis = am.getActivityAnalysis()

        total_load_count = 0
        total_store_count = 0
        total_connections = 0
        limit = 0
        divs = []
        for div in analysis:
            total_store_count = total_store_count + div['stores']
            total_load_count = total_load_count + div['loads']
            total_connections = total_connections + div['connections']
            sum = div['stores'] + div['loads']
            if sum > limit:
                limit = sum

        if analysis:
            segment_time = analysis[0]['end'] - analysis[0]['start']
        else:
            segment_time = 0

        for div in analysis:
            stores = div['stores']
            if stores > 0:
                store_len = max(int(segment_height * stores / limit), 1)
            else:
                store_len = 0
            loads = div['loads']
            if loads > 0:
                load_len = max(int(segment_height * loads / limit), 1)
            else:
                load_len = 0

            t = div['end'] - analysis[-1]['end']  # Show negative numbers.
            if segment_time >= 3600:
                # Show hours.
                time_offset = '%dh' % (t / 3600)
            elif segment_time >= 60:
                # Show minutes.
                time_offset = '%dm' % (t / 60)
            elif segment_time >= 1:
                # Show seconds.
                time_offset = '%ds' % t
            else:
                # Show fractions.
                time_offset = '%.2fs' % t
            divs.append({
                'store_len': store_len,
                'load_len': load_len,
                'trans_len': max(segment_height - store_len - load_len, 0),
                'store_count': div['stores'],
                'load_count': div['loads'],
                'connections': div['connections'],
                'start': div['start'],
                'end': div['end'],
                'time_offset': time_offset,
                })

        if analysis:
            start_time = DateTime(divs[0]['start']).aCommonZ()
            end_time = DateTime(divs[-1]['end']).aCommonZ()
        else:
            start_time = ''
            end_time = ''

        res = {'start_time': start_time,
               'end_time': end_time,
               'divs': divs,
               'total_store_count': total_store_count,
               'total_load_count': total_load_count,
               'total_connections': total_connections,
               }
        return res

InitializeClass(CacheManager)
