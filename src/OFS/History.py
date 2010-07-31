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
"""Object Histories
"""

from cgi import escape
import difflib
from struct import pack, unpack

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_history
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import Implicit
from App.special_dtml import DTMLFile
from DateTime.DateTime import DateTime
from ExtensionClass import Base
from zExceptions import Redirect

class TemporalParadox(Exception):
    pass

class HistorySelectionError(Exception):
    pass

class HystoryJar:
    """A ZODB Connection-like object that provides access to data
    but prevents history from being changed."""

    def __init__(self, base):
        self.__base__=base

    def __getattr__(self, name):
        return getattr(self.__base__, name)

    def commit(self, object, transaction):
        if object._p_changed:
            raise TemporalParadox, "You can't change history!"

    def abort(*args, **kw): pass

    tpc_begin = tpc_finish = abort

def historicalRevision(self, serial):
    state=self._p_jar.oldstate(self, serial)
    rev=self.__class__.__basicnew__()
    rev._p_jar=HystoryJar(self._p_jar)
    rev._p_oid=self._p_oid
    rev._p_serial=serial
    rev.__setstate__(state)
    rev._p_changed=0
    return rev

class Historian(Implicit):
    """An Historian's job is to find hysterical revisions of
    objects, given a time."""

    def __getitem__(self, key):
        self=self.aq_parent

        serial=apply(pack, ('>HHHH',)+tuple(map(int, key.split('.'))))

        if serial == self._p_serial: return self

        rev=historicalRevision(self, serial)

        return rev.__of__(self.aq_parent)

    def manage_workspace(self, REQUEST):
        "We aren't real, so we delegate to that that spawned us!"
        raise Redirect, REQUEST['URL2']+'/manage_change_history_page'

class Historical(Base):
    """Mix-in class to provide a veiw that shows hystorical changes

    The display is similar to that used for undo, except that the transactions
    are limited to those that effect the displayed object and that the
    interface doesn't provide an undo capability.

    This interface is generally *only* interesting for objects, such
    as methods, and documents, that are self-contained, meaning that
    they don't have persistent sub-objects.
    """

    security = ClassSecurityInfo()

    HistoricalRevisions=Historian()

    manage_options=(
        {'label':'History', 'action':'manage_change_history_page'},
        )

    security.declareProtected(view_history, 'manage_change_history_page')
    manage_change_history_page = DTMLFile(
        'dtml/history', globals(),
        HistoryBatchSize=20,
        first_transaction=0, last_transaction=20)

    security.declareProtected(view_history, 'manage_change_history')
    def manage_change_history(self):
        first=0
        last=20
        request=getattr(self, 'REQUEST', None)
        if request is not None:
            first=request.get('first_transaction', first)
            last=request.get('last_transaction',last)

        r=self._p_jar.db().history(self._p_oid, size=last)
        if r is None:
            # storage doesn't support history
            return ()
        r=r[first:]

        for d in r:
            d['time']=DateTime(d['time'])
            d['key']='.'.join(map(str, unpack(">HHHH", d['tid'])))

        return r

    def manage_beforeHistoryCopy(self): pass # ? (Hook)

    def manage_historyCopy(self, keys=[], RESPONSE=None, URL1=None):
        "Copy a selected revision to the present"
        if not keys:
            raise HistorySelectionError, (
                "No historical revision was selected.<p>")

        if len(keys) > 1:
            raise HistorySelectionError, (
                "Only one historical revision can be "
                "copied to the present.<p>")

        key=keys[0]
        serial=apply(pack, ('>HHHH',)+tuple(map(int, key.split('.'))))

        if serial != self._p_serial:
            self.manage_beforeHistoryCopy()
            state=self._p_jar.oldstate(self, serial)
            base = aq_base(self)
            base._p_activate()       # make sure we're not a ghost 
            base.__setstate__(state) # change the state
            base._p_changed = True   # marke object as dirty 
            self.manage_afterHistoryCopy()
            
        if RESPONSE is not None and URL1 is not None:
            RESPONSE.redirect(URL1+'/manage_workspace')

    def manage_afterHistoryCopy(self): pass # ? (Hook)


    _manage_historyComparePage = DTMLFile(
        'dtml/historyCompare', globals(), management_view='History')
    security.declareProtected(view_history, 'manage_historyCompare')
    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        dt1=DateTime(rev1._p_mtime)
        dt2=DateTime(rev2._p_mtime)
        return self._manage_historyComparePage(
            self, REQUEST,
            dt1=dt1, dt2=dt2,
            historyComparisonResults=historyComparisonResults)

    security.declareProtected(view_history, 'manage_historicalComparison')
    def manage_historicalComparison(self, REQUEST, keys=[]):
        "Compare two selected revisions"
        if not keys:
            raise HistorySelectionError, (
                "No historical revision was selected.<p>")
        if len(keys) > 2:
            raise HistorySelectionError, (
                "Only two historical revision can be compared<p>")

        serial=apply(pack, ('>HHHH',)+tuple(map(int, keys[-1].split('.'))))
        rev1=historicalRevision(self, serial)

        if len(keys)==2:
            serial=apply(pack,
                         ('>HHHH',)+tuple(map(int, keys[0].split('.'))))

            rev2=historicalRevision(self, serial)
        else:
            rev2=self

        return self.manage_historyCompare(rev1, rev2, REQUEST)

InitializeClass(Historical)

def dump(tag, x, lo, hi, r):
    r1=[]
    r2=[]
    for i in xrange(lo, hi):
        r1.append(tag)
        r2.append(x[i])
    r.append("<tr>\n"
            "<td><pre>\n%s\n</pre></td>\n"
            "<td><pre>\n%s\n</pre></td>\n"
            "</tr>\n"
            % ('\n'.join(r1), escape('\n'.join(r2))))

def replace(x, xlo, xhi, y, ylo, yhi, r):

    rx1=[]
    rx2=[]
    for i in xrange(xlo, xhi):
        rx1.append('-')
        rx2.append(x[i])

    ry1=[]
    ry2=[]
    for i in xrange(ylo, yhi):
        ry1.append('+')
        ry2.append(y[i])


    r.append("<tr>\n"
            "<td><pre>\n%s\n%s\n</pre></td>\n"
            "<td><pre>\n%s\n%s\n</pre></td>\n"
            "</tr>\n"
            % ('\n'.join(rx1), '\n'.join(ry1),
               escape('\n'.join(rx2)), escape('\n'.join(ry2))))

def html_diff(s1, s2):
    a=s1.split('\n')
    b=s2.split('\n')
    cruncher=difflib.SequenceMatcher()
    cruncher.set_seqs(a,b)

    r=['<table border=1>']
    for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
        if tag == 'replace':
            replace(a, alo, ahi, b, blo, bhi, r)
        elif tag == 'delete':
            dump('-', a, alo, ahi, r)
        elif tag == 'insert':
            dump('+', b, blo, bhi, r)
        elif tag == 'equal':
            dump(' ', a, alo, ahi, r)
        else:
            raise ValueError, 'unknown tag ' + `tag`
    r.append('</table>')

    return '\n'.join(r)
