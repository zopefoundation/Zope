##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Object Histories"""

__version__='$Revision: 1.3 $'[11:-2]

import Globals, ndiff, ExtensionClass
from DateTime import DateTime
from Acquisition import Implicit
from string import join, split, atoi, strip
from struct import pack, unpack
from DocumentTemplate.DT_Util import html_quote

class TemporalParadox(Exception): pass

class HistorySelectionError(Exception): pass

class HystoryJar:
    """A ZODB Connection-like object that provides access to data
    but prevents history from being changed."""

    def __init__(self, base):
        self.__base__=base

    def __getattr__(self, name):
        return getattr(self.__base__, name)

    def commit(*args, **kw):
        raise TemporalParadox, "You can\'t change history!"

    tpc_begin = tpc_finish = commit

    def abort(*args, **kw): pass

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
    """An Historian\'s job is to find hysterical revisions of
    objects, given a time."""

    def __getitem__(self, key):
        self=self.aq_parent

        serial=apply(pack, ('>HHHH',)+tuple(map(atoi, split(key,'.'))))

        if serial == self._p_serial: return self

        rev=historicalRevision(self, serial)

        return rev.__of__(self.aq_parent)

    def manage_workspace(self, REQUEST):
        "We aren\'t real, so we delegate to that that spawned us!"
        raise 'Redirect', REQUEST['URL2']+'/manage_change_history_page'

class Historical(ExtensionClass.Base):
    """Mix-in class to provide a veiw that shows hystorical changes

    The display is similar to that used for undo, except that the transactions
    are limited to those that effect the displayed object and that the
    interface doesn't provide an undo capability.

    This interface is generally *only* interesting for objects, such
    as methods, and documents, that are self-contained, meaning that
    they don't have persistent sub-objects.
    """

    HistoricalRevisions=Historian()

    __ac_permissions__=(
        ('Undo changes',
         ('manage_change_history_page','manage_change_history')),
        )
    
    manage_options=({'label':'History', 'action':'manage_change_history_page',
                     'help':('OFSP','History.stx')
                     },
                   )

    manage_change_history_page=Globals.HTMLFile(
        'history', globals(),
        HistoryBatchSize=20,
        first_transaction=0, last_transaction=20)

    def manage_change_history(self):
        first=0
        last=20
        request=getattr(self, 'REQUEST', None)
        if request is not None:
            first=request.get('first_transaction', first)
            last=request.get('last_transaction',last)
        

        r=self._p_jar.db().history(self._p_oid, None, last)
        r=r[first:]

        for d in r:
            d['time']=DateTime(d['time'])
            d['key']=join(map(str, unpack(">HHHH", d['serial'])),'.')

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
        serial=apply(pack, ('>HHHH',)+tuple(map(atoi, split(key,'.'))))

        if serial != self._p_serial:
            self.manage_beforeHistoryCopy()
            state=self._p_jar.oldstate(self, serial)
            self.__setstate__(state)
            self._p_changed=1
            self.manage_afterHistoryCopy()

        if RESPONSE is not None and URL1 is not None:
            RESPONSE.redirect(URL1+'/manage_workspace')

    def manage_afterHistoryCopy(self): pass # ? (Hook)

    
    _manage_historyComparePage=Globals.HTMLFile(
        'historyCompare', globals(), management_view='History')
    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        dt1=DateTime(rev1._p_mtime)
        dt2=DateTime(rev2._p_mtime)
        return self._manage_historyComparePage(
            self, REQUEST,
            dt1=dt1, dt2=dt2,
            historyComparisonResults=historyComparisonResults)

    def manage_historicalComparison(self, REQUEST, keys=[]):
        "Compare two selected revisions"
        if not keys:
            raise HistorySelectionError, (
                "No historical revision was selected.<p>")
        if len(keys) > 2:
            raise HistorySelectionError, (
                "Only two historical revision can be compared<p>")
        
        serial=apply(pack, ('>HHHH',)+tuple(map(atoi, split(keys[-1],'.'))))
        rev1=historicalRevision(self, serial)
        
        if len(keys)==2:
            serial=apply(pack,
                         ('>HHHH',)+tuple(map(atoi, split(keys[0],'.'))))

            rev2=historicalRevision(self, serial)
        else:
            rev2=self

        return self.manage_historyCompare(rev1, rev2, REQUEST)
        
Globals.default__class_init__(Historical)

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
            % (join(r1,'\n'), html_quote(join(r2, '\n'))))

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
            % (join(rx1, '\n'), join(ry1, '\n'),
               html_quote(join(rx2, '\n')), html_quote(join(ry2, '\n'))))

def html_diff(s1, s2):
    a=split(s1,'\n')
    b=split(s2,'\n')
    cruncher=ndiff.SequenceMatcher(isjunk=split, a=a, b=b)

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

    return join(r, '\n')
