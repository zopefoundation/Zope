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
"""Cache management support.

This class is mixed into the application manager in App.ApplicationManager.
"""

from AccessControl.class_init import InitializeClass
from Acquisition import aq_parent


class CacheManager:
    """Cache management mix-in
    """

    def _getDB(self):
        try:
            return self._p_jar.db()
        except AttributeError:
            return aq_parent(self)._p_jar.db()

    def cache_size(self):
        db = self._getDB()
        return db.getCacheSize()

    def cache_detail(self, REQUEST=None):
        """
        Returns the name of the classes of the objects in the cache
        and the number of objects in the cache for each class.
        """
        detail = self._getDB().cacheDetail()
        if REQUEST is not None:
            # format as text
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
            return '\n'.join(
                ['%6d %s' % (count, name) for name, count in detail])
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
                    dict['conn_no'], repr(dict['oid']), dict['rc'],
                    state, dict['klass'], idinfo))
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
            return '\n'.join(res)
        else:
            # raw
            return detail


InitializeClass(CacheManager)
