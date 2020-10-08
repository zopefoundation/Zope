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
Objects for packages that have been uninstalled.
"""
import html
from _thread import allocate_lock
from logging import getLogger

from Acquisition import Acquired
from Acquisition import Explicit
from App.special_dtml import DTMLFile
from OFS.SimpleItem import Item
from Persistence import Overridable
from ZODB.broken import Broken as ZODB_Broken
from ZODB.broken import persistentBroken


broken_klasses = {}
broken_klasses_lock = allocate_lock()
LOG = getLogger('OFS.Uninstalled')


class BrokenClass(ZODB_Broken, Explicit, Item, Overridable):
    _p_changed = 0
    meta_type = 'Broken Because Product is Gone'

    product_name = 'unknown'
    id = 'broken'

    manage_page_header = Acquired
    manage_page_footer = Acquired

    def __getattr__(self, name):
        if name[:3] == '_p_':
            return BrokenClass.inheritedAttribute('__getattr__')(self, name)
        raise AttributeError(html.escape(name, True))

    manage = DTMLFile('dtml/brokenEdit', globals())
    manage_main = DTMLFile('dtml/brokenEdit', globals())
    manage_workspace = DTMLFile('dtml/brokenEdit', globals())


def Broken(self, oid, pair):
    broken_klasses_lock.acquire()
    try:
        if pair in broken_klasses:
            klass = broken_klasses[pair]
        else:
            module, klassname = pair
            d = {'BrokenClass': BrokenClass}
            exec("class %s(BrokenClass): ' '; __module__=%r" %
                 (klassname, module), d)
            klass = broken_klasses[pair] = d[klassname]
            module = module.split('.')
            if len(module) > 2 and module[0] == 'Products':
                klass.product_name = module[1]
            klass.title = (
                'This object from the %s product '
                'is broken!' %
                klass.product_name)
            klass.info = (
                'This object\'s class was %s in module %s.' %
                (klass.__name__, klass.__module__))
            klass = persistentBroken(klass)
            LOG.warning(
                'Could not import class %r '
                'from module %r' % (klass.__name__, klass.__module__))
    finally:
        broken_klasses_lock.release()
    if oid is None:
        return klass
    i = klass()
    i._p_oid = oid
    i._p_jar = self
    return i
