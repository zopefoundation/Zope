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
__doc__='''Zope-specific versions of ZTUTils classes

$Id: Zope.py,v 1.3 2001/08/16 17:42:53 evan Exp $'''
__version__='$Revision: 1.3 $'[11:-2]

import sys, cgi, urllib, cgi
from Tree import encodeExpansion, decodeExpansion, TreeMaker
from SimpleTree import SimpleTreeMaker
from Batch import Batch
from Products.ZCatalog.Lazy import Lazy
from AccessControl import getSecurityManager
from string import split, join
from types import StringType, ListType, IntType, FloatType
from DateTime import DateTime

try:
    from AccessControl.ZopeGuards import guarded_getitem
except ImportError:
    Unauthorized = 'Unauthorized'
    def guarded_getitem(object, index):
        v = object[index]
        if getSecurityManager().validate(object, object, index, v):
            return v
        raise Unauthorized, 'unauthorized access to element %s' % `i`
else:
    from AccessControl import Unauthorized

class LazyFilter(Lazy):
    # A LazyFilter that checks with the security policy

    def __init__(self, seq, test=None, skip=None):
        self._seq=seq
        self._data=[]
        self._eindex=-1
        self._test=test
        if not (skip is None or str(skip) == skip): 
            raise TypeError, 'Skip must be None or a string'
        self._skip = skip 

    def __getitem__(self,index):

        data=self._data
        try: s=self._seq
        except AttributeError: return data[index]

        i=index
        if i < 0: i=len(self)+i
        if i < 0: raise IndexError, index

        ind=len(data)
        if i < ind: return data[i]
        ind=ind-1

        test=self._test
        e=self._eindex
        skip = self._skip
        while i > ind:
            e = e + 1
            try:
                try: v = guarded_getitem(s, e)
                except 'Unauthorized', vv:
                    if skip is None:
                        msg = '(item %s): %s' % (index, vv)
                        raise Unauthorized, msg, sys.exc_info()[2]
                    skip_this = 1
                else:
                    skip_this = 0
            except IndexError:
                del self._test
                del self._seq
                del self._eindex
                raise IndexError, index
            if skip_this: continue
            if skip and not getSecurityManager().checkPermission(skip, v):
                continue
            if test is None or test(v):
                data.append(v)
                ind=ind+1
        self._eindex=e
        return data[i]

class TreeSkipMixin:
    '''Mixin class to make trees test security, and allow
    skipping of unauthorized objects. '''
    skip = None
    def setSkip(self, skip):
        self.skip = skip
        return self
    def getChildren(self, object):
        return LazyFilter(self._getChildren(object), skip=self.skip)

class TreeMaker(TreeSkipMixin, TreeMaker):
    _getChildren = TreeMaker.getChildren

class SimpleTreeMaker(TreeSkipMixin, SimpleTreeMaker):
    _getChildren = SimpleTreeMaker.getChildren
    def cookieTree(self, root_object):
        '''Make a tree with state stored in a cookie.'''
        tree_pre = self.tree_pre
        state_name = '%s-state' % tree_pre
        set_name = '%s-setstate' % tree_pre

        req = root_object.REQUEST
        state = req.get(state_name)
        if state:
            setst = req.form.get(set_name)
            if setst:
                st, pn, expid = split(setst, ',')
                state, (m, obid) = decodeExpansion(state, int(pn))
                if m is None:
                    pass
                elif st == 'e':
                    if m[obid] is None:
                        m[obid] = {expid: None}
                    else:
                        m[obid][expid] = None
                elif st == 'c' and m is not state and obid==expid:
                    del m[obid]
            else:
                state = decodeExpansion(state)
        tree = self.tree(root_object, state)
        rows = tree.flat()
        req.RESPONSE.setCookie(state_name, encodeExpansion(rows))
        return tree, rows

# Make the Batch class test security, and let it skip unauthorized.
_Batch = Batch
class Batch(Batch):
    def __init__(self, sequence, size, start=0, end=0,
                 orphan=3, overlap=0, skip_unauthorized=None):
        sequence = LazyFilter(sequence, skip=skip_unauthorized)
        _Batch.__init__(self, sequence, size, start, end,
                        orphan, overlap)

# These functions are meant to be used together in templates that use
# trees or batches.  For example, given a batch with a 'bstart' query
# argument, you would use "url_query(request, omit='bstart')" to get
# the base for the batching links, then append 
# "make_query(bstart=batch.previous.first)" to one and
# "make_query(bstart=batch.end)" to the other.

def make_query(*args, **kwargs):
    '''Construct a URL query string, with marshalling markup.

    If there are positional arguments, they must be dictionaries.
    They are combined with the dictionary of keyword arguments to form
    a dictionary of query names and values.

    Query names (the keys) must be strings.  Values may be strings,
    integers, floats, or DateTimes, and they may also be lists or
    namespaces containing these types.  Names and string values
    should not be URL-quoted.  All arguments are marshalled with
    complex_marshal().
    '''

    d = {}
    for arg in args:
        d.update(arg)
    d.update(kwargs)

    uq = urllib.quote
    qlist = complex_marshal(d.items())
    for i in range(len(qlist)):
        k, m, v = qlist[i]
        qlist[i] = '%s%s=%s' % (uq(k), m, uq(str(v)))

    return join(qlist, '&')
                
def make_hidden_input(*args, **kwargs):
    '''Construct a set of hidden input elements, with marshalling markup.

    If there are positional arguments, they must be dictionaries.
    They are combined with the dictionary of keyword arguments to form
    a dictionary of query names and values.

    Query names (the keys) must be strings.  Values may be strings,
    integers, floats, or DateTimes, and they may also be lists or
    namespaces containing these types.  All arguments are marshalled with
    complex_marshal().
    '''

    d = {}
    for arg in args:
        d.update(arg)
    d.update(kwargs)

    hq = cgi.escape
    qlist = complex_marshal(d.items())
    for i in range(len(qlist)):
        k, m, v = qlist[i]
        qlist[i] = ('<input type="hidden" name="%s%s" value="%s">'
                    % (hq(k), m, hq(str(v))))

    return join(qlist, '\n')
                
def complex_marshal(pairs):
    '''Add request marshalling information to a list of name-value pairs.

    Names must be strings.  Values may be strings,
    integers, floats, or DateTimes, and they may also be lists or
    namespaces containing these types.

    The list is edited in place so that each (name, value) pair
    becomes a (name, marshal, value) triple.  The middle value is the
    request marshalling string.  Integer, float, and DateTime values
    will have ":int", ":float", or ":date" as their marshal string.
    Lists will be flattened, and the elements given ":list" in
    addition to their simple marshal string.  Dictionaries will be
    flattened and marshalled using ":record".
    '''

    for i in range(len(pairs)):
        k, v = pairs[i]
        m = ''
        sublist = None
        if isinstance(v, StringType):
            pass
        elif hasattr(v, 'items'):
            sublist = []
            for sk, sv in v.items():
                sm = simple_marshal(sv)
                sublist.append(('%s.%s' % (k, sk), '%s:record' % sm,  sv))
        elif isinstance(v, ListType):
            sublist = []
            for sv in v:
                sm = simple_marshal(sv)
                sublist.append((k, '%s:list' % sm, sv))
        else:
            m = simple_marshal(v)
        if sublist is None:
            pairs[i] = (k, m, v)
        else:
            pairs[i:i + 1] = sublist

    return pairs

def simple_marshal(v):
    if isinstance(v, StringType):
        return ''
    if isinstance(v, IntType):
        return ':int'
    if isinstance(v, FloatType):
        return ':float'
    if isinstance(v, DateTime):
        return ':date'
    return ''

def url_query(request, req_name="URL", omit=None):
    '''Construct a URL with a query string, using the current request.

    request: the request object
    req_name: the name, such as "URL1" or "BASEPATH1", to get from request
    omit: sequence of name of query arguments to omit.  If a name
    contains a colon, it is treated literally.  Otherwise, it will
    match each argument name that starts with the name and a period or colon. 
    '''

    base = request[req_name]
    qs = request.get('QUERY_STRING', '')
    
    if qs and omit:
        qsparts = split(qs, '&')

        if isinstance(omit, StringType):
            omits = {omit: None}
        else:
            omits = {}
            for name in omit:
                omits[name] = None
        omitted = omits.has_key

        unq = urllib.unquote
        for i in range(len(qsparts)):
            name = unq(split(qsparts[i], '=', 1)[0])
            if omitted(name):
                qsparts[i] = ''
            name = split(name, ':', 1)[0]
            if omitted(name):
                qsparts[i] = ''
            name = split(name, '.', 1)[0]
            if omitted(name):
                qsparts[i] = ''
            
        qs = join(filter(None, qsparts), '&')

    # We alway append '?' since arguments will be appended to the URL
    return '%s?%s' % (base, qs)
