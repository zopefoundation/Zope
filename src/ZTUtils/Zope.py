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
"""Zope-specific versions of ZTUtils classes
"""

import html
from urllib.parse import quote
from urllib.parse import unquote

from AccessControl import getSecurityManager
from AccessControl.unauthorized import Unauthorized
from AccessControl.ZopeGuards import guarded_getitem
from DateTime.DateTime import DateTime
from ZTUtils.Batch import Batch
from ZTUtils.Lazy import Lazy
from ZTUtils.SimpleTree import SimpleTreeMaker
from ZTUtils.Tree import TreeMaker
from ZTUtils.Tree import decodeExpansion
from ZTUtils.Tree import encodeExpansion


class LazyFilter(Lazy):
    # A LazyFilter that checks with the security policy

    def __init__(self, seq, test=None, skip=None):
        self._seq = seq
        self._data = []
        self._eindex = -1
        self._test = test
        if not (skip is None or str(skip) == skip):
            raise TypeError('Skip must be None or a string')
        self._skip = skip

    def __getitem__(self, index):
        data = self._data
        try:
            s = self._seq
        except AttributeError:
            return data[index]

        i = index
        if i < 0:
            i = len(self) + i
        if i < 0:
            raise IndexError(index)

        ind = len(data)
        if i < ind:
            return data[i]
        ind = ind - 1

        test = self._test
        e = self._eindex
        skip = self._skip
        while i > ind:
            e = e + 1
            try:
                try:
                    v = guarded_getitem(s, e)
                except Unauthorized as vv:
                    if skip is None:
                        self._eindex = e
                        msg = f'(item {index}): {vv}'
                        raise Unauthorized(msg)
                    skip_this = 1
                else:
                    skip_this = 0
            except IndexError:
                del self._test
                del self._seq
                del self._eindex
                raise IndexError(index)
            if skip_this:
                continue
            if skip and not getSecurityManager().checkPermission(skip, v):
                continue
            if test is None or test(v):
                data.append(v)
                ind = ind + 1
        self._eindex = e
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

    def filterChildren(self, children):
        if self._values_filter:
            return self._values_filter(LazyFilter(children, skip=self.skip))
        return children


class TreeMaker(TreeSkipMixin, TreeMaker):
    _getChildren = TreeMaker.getChildren


class SimpleTreeMaker(TreeSkipMixin, SimpleTreeMaker):
    _getChildren = SimpleTreeMaker.getChildren

    def cookieTree(self, root_object, default_state=None):
        '''Make a tree with state stored in a cookie.'''
        tree_pre = self.tree_pre
        state_name = '%s-state' % tree_pre
        set_name = '%s-setstate' % tree_pre

        req = root_object.REQUEST
        state = req.get(state_name)
        if state:
            setst = req.form.get(set_name)
            if setst:
                st, pn, expid = setst.split(',')
                state, (m, obid) = decodeExpansion(state, int(pn))
                if m is None:
                    pass
                elif st == 'e':
                    if m[obid] is None:
                        m[obid] = {expid: None}
                    else:
                        m[obid][expid] = None
                elif st == 'c' and m is not state and obid == expid:
                    del m[obid]
            else:
                state = decodeExpansion(state)
        else:
            state = default_state
        tree = self.tree(root_object, state)
        rows = tree.flat()
        req.RESPONSE.setCookie(state_name, encodeExpansion(rows))
        return tree, rows


# Make the Batch class test security, and let it skip unauthorized.
_Batch = Batch


class Batch(Batch):
    def __init__(self, sequence, size, start=0, end=0,
                 orphan=0, overlap=0, skip_unauthorized=None):
        sequence = LazyFilter(sequence, skip=skip_unauthorized)
        _Batch.__init__(self, sequence, size, start, end,
                        orphan, overlap)

# These functions are meant to be used together in templates that use
# trees or batches.  For example, given a batch with a 'bstart' query
# argument, you would use "url_query(request, omit='bstart')" to get
# the base for the batching links, then append
# "make_query(bstart=batch.previous.first)" to one and
# "make_query(bstart=batch.end)" to the other.


# Do not do this at import time.
# Call '_default_encoding()' at run time to retrieve it from config, if present
# If not configured, will be 'utf8' by default.
_DEFAULT_ENCODING = None


def _default_encoding():
    ''' Retrieve default encoding from config '''
    global _DEFAULT_ENCODING
    if _DEFAULT_ENCODING is None:
        from App.config import getConfiguration
        config = getConfiguration()
        try:
            _DEFAULT_ENCODING = config.zpublisher_default_encoding
        except AttributeError:
            _DEFAULT_ENCODING = 'utf8'
    return _DEFAULT_ENCODING


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

    qlist = complex_marshal(list(d.items()))
    for i in range(len(qlist)):
        k, m, v = qlist[i]
        qlist[i] = f'{quote(k)}{m}={quote(str(v))}'

    return '&'.join(qlist)


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

    def hq(x):
        return html.escape(x, quote=True)

    qlist = complex_marshal(list(d.items()))
    for i in range(len(qlist)):
        k, m, v = qlist[i]
        qlist[i] = ('<input type="hidden" name="%s%s" value="%s">'
                    % (hq(k), m, hq(str(v))))

    return '\n'.join(qlist)


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
    i = len(pairs)
    while i > 0:
        i = i - 1
        k, v = pairs[i]
        m = ''
        sublist = None
        if isinstance(v, str):
            pass
        elif hasattr(v, 'items'):
            sublist = []
            for sk, sv in v.items():
                if isinstance(sv, list):
                    for ssv in sv:
                        sm = simple_marshal(ssv)
                        sublist.append((f'{k}.{sk}',
                                        '%s:list:record' % sm, ssv))
                else:
                    sm = simple_marshal(sv)
                    sublist.append((f'{k}.{sk}', '%s:record' % sm, sv))
        elif isinstance(v, list):
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
    if isinstance(v, str):
        return ''
    if isinstance(v, bytes):
        return ':bytes'
    if isinstance(v, bool):
        return ':boolean'
    if isinstance(v, int):
        return ':int'
    if isinstance(v, float):
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
        qsparts = qs.split('&')

        if isinstance(omit, str):
            omits = {omit: None}
        else:
            omits = {}
            for name in omit:
                omits[name] = None

        for i in range(len(qsparts)):
            name = unquote(qsparts[i].split('=', 1)[0])
            if name in omits:
                qsparts[i] = ''
            name = name.split(':', 1)[0]
            if name in omits:
                qsparts[i] = ''
            name = name.split('.', 1)[0]
            if name in omits:
                qsparts[i] = ''

        qs = '&'.join([part for part in qsparts if part])

    # We always append '?' since arguments will be appended to the URL
    return f'{base}?{qs}'
