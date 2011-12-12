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
"""Patch for Persistent to support IPersistentExtra.
"""

from DateTime.DateTime import DateTime

class PersistentUtil:

    def bobobase_modification_time(self):
        jar = self._p_jar
        oid = self._p_oid
        if jar is None or oid is None:
            return DateTime()

        try:
            t = self._p_mtime
        except AttributeError:
            t = 0
        return DateTime(t)


_patched = False

def patchPersistent():
    global _patched
    if _patched:
        return

    _patched = True

    from zope.interface import classImplements
    from Persistence import Persistent
    from App.interfaces import IPersistentExtra

    for k, v in PersistentUtil.__dict__.items():
        if k[0] != '_':
            setattr(Persistent, k, v)

    classImplements(Persistent, IPersistentExtra)
