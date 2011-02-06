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
"""Rendering object hierarchies as Trees
"""
__rcs_id__='$Id$'
__version__='$Revision: 1.58 $'[11:-2]

from binascii import a2b_base64
from binascii import b2a_base64
from cPickle import dumps
import re
from string import translate
from urllib import quote
from urllib import unquote
from zlib import compress
from zlib import decompressobj

#from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_Util import add_with_prefix
from DocumentTemplate.DT_Util import Eval
from DocumentTemplate.DT_Util import InstanceDict
from DocumentTemplate.DT_Util import name_param
from DocumentTemplate.DT_Util import parse_params
from DocumentTemplate.DT_Util import ParseError
from DocumentTemplate.DT_Util import render_blocks
from DocumentTemplate.DT_Util import simple_name
from DocumentTemplate.DT_String import String

tbl = ''.join(map(chr, range(256)))
tplus = tbl[:ord('+')]+'-'+tbl[ord('+')+1:]
tminus = tbl[:ord('-')]+'+'+tbl[ord('-')+1:]

class Tree:
    name='tree'
    blockContinuations=()
    expand=None

    def __init__(self, blocks):
        tname, args, section = blocks[0]
        args = parse_params(args,
                            name=None,
                            expr=None,
                            nowrap=1,
                            expand=None,
                            leaves=None,
                            header=None,
                            footer=None,
                            branches=None,
                            branches_expr=None,
                            sort=None,
                            reverse=1,
                            skip_unauthorized=1,
                            id=None,
                            single=1,
                            url=None,
                          # opened_decoration=None,
                          # closed_decoration=None,
                          # childless_decoration=None,
                            assume_children=1,
                            urlparam=None, prefix=None)
        has_key = args.has_key

        if has_key('') or has_key('name') or has_key('expr'):
            name, expr = name_param(args,'tree',1)

            if expr is not None:
                args['expr'] = expr
            elif has_key(''):
                args['name'] = name
        else:
            name='a tree tag'

        if has_key('branches_expr'):
            if has_key('branches'):
                raise ParseError, _tm(
                    'branches and  and branches_expr given', 'tree')
            args['branches_expr'] = Eval(args['branches_expr']).eval
        elif not has_key('branches'):
            args['branches']='tpValues'

        if not has_key('id'):
            args['id'] = 'tpId'
        if not has_key('url'):
            args['url'] = 'tpURL'
        if not has_key('childless_decoration'):
            args['childless_decoration']=''

        prefix = args.get('prefix')
        if prefix and not simple_name(prefix):
            raise ParseError, _tm(
                'prefix is not a simple name', 'tree')

        self.__name__ = name
        self.section = section.blocks
        self.args = args


    def render(self, md):
        args = self.args
        have = args.has_key

        if have('name'):
            v = md[args['name']]
        elif have('expr'):
            v = args['expr'].eval(md)
        else:
            v = md.this
        return tpRender(v, md, self.section, self.args)

    __call__ = render

String.commands['tree']=Tree

pyid=id # Copy builtin

simple_types = {str: 1, unicode: 1, int: 1, float: 1, long: 1,
                tuple: 1, list: 1, dict: 1}

def try_call_attr(ob, attrname, simple_types=simple_types):
    attr = getattr(ob, attrname)
    if type(attr) in simple_types:
        return attr
    try:
        return attr()
    except TypeError:
        return attr

def tpRender(self, md, section, args,
             try_call_attr=try_call_attr):
    """Render data organized as a tree.

    We keep track of open nodes using a cookie.  The cookie stored the
    tree state. State should be a tree represented like:

      []  # all closed
      ['eagle'], # eagle is open
      ['eagle'], ['jeep', [1983, 1985]]  # eagle, jeep, 1983 jeep and 1985 jeep

    where the items are object ids. The state will be pickled to a
    compressed and base64ed string that gets unencoded, uncompressed,
    and unpickled on the other side.

    Note that ids used in state need not be connected to urls, since
    state manipulation is internal to rendering logic.

    Note that to make unpickling safe, we use the MiniPickle module,
    that only creates safe objects
    """

    data=[]

    idattr=args['id']
    if hasattr(self, idattr):
        id = try_call_attr(self, idattr)
    elif hasattr(self, '_p_oid'): id=oid(self)
    else: id=pyid(self)

    try:
        # see if we are being run as a sub-document
        root=md['tree-root-url']
        url=md['tree-item-url']
        state=md['tree-state']
        diff=md['tree-diff']
        substate=md['-tree-substate-']
        colspan=md['tree-colspan']
        level=md['tree-level']

    except KeyError:
        # OK, we are a top-level invocation
        level=-1

        if md.has_key('collapse_all'):
            state=[id,[]],
        elif md.has_key('expand_all'):
            have_arg=args.has_key
            if have_arg('branches'):
                def get_items(node, branches=args['branches'], md=md):
                    get = md.guarded_getattr
                    if get is None:
                        get = getattr
                    items = get(node, branches)
                    return items()
            elif have_arg('branches_expr'):
                def get_items(node, branches_expr=args['branches_expr'], md=md):
                    md._push(InstanceDict(node, md))
                    items=branches_expr(md)
                    md._pop()
                    return items
            state=[id, tpValuesIds(self, get_items, args)],
        else:
            if md.has_key('tree-s'):
                state=md['tree-s']
                state=decode_seq(state)
                try:
                    if state[0][0] != id: state=[id,[]],
                except IndexError: state=[id,[]],
            else: state=[id,[]],

            if md.has_key('tree-e'):
                diff=decode_seq(md['tree-e'])
                apply_diff(state, diff, 1)

            if md.has_key('tree-c'):
                diff=decode_seq(md['tree-c'])
                apply_diff(state, diff, 0)

        colspan=tpStateLevel(state)
        substate=state
        diff=[]

        url=''
        root=md['URL']
        l=root.rfind('/')
        if l >= 0: root=root[l+1:]

    treeData={'tree-root-url': root,
              'tree-colspan': colspan,
              'tree-state': state }

    prefix = args.get('prefix')
    if prefix:
        for k, v in treeData.items():
            treeData[prefix + k[4:].replace('-', '_')] = v

    md._push(InstanceDict(self, md))
    md._push(treeData)

    try: tpRenderTABLE(self,id,root,url,state,substate,diff,data,colspan,
                       section,md,treeData, level, args)
    finally: md._pop(2)

    if state is substate and not (args.has_key('single') and args['single']):
        state=state or ([id],)
        state=encode_seq(state)
        md['RESPONSE'].setCookie('tree-s',state)

    return ''.join(data)

def tpRenderTABLE(self, id, root_url, url, state, substate, diff, data,
                  colspan, section, md, treeData, level=0, args=None,
                  try_call_attr=try_call_attr,
                  ):
    "Render a tree as a table"

    have_arg=args.has_key
    exp=0

    if level >= 0:
        urlattr=args['url']
        if urlattr and hasattr(self, urlattr):
            tpUrl = try_call_attr(self, urlattr)
            url = (url and ('%s/%s' % (url, tpUrl))) or tpUrl
            root_url = root_url or tpUrl

    ptreeData = add_with_prefix(treeData, 'tree', args.get('prefix'))
    ptreeData['tree-item-url']=url
    ptreeData['tree-level']=level
    ptreeData['tree-item-expanded']=0
    idattr=args['id']

    output=data.append

    items=None
    if (have_arg('assume_children') and args['assume_children']
        and substate is not state):
        # We should not compute children unless we have to.
        # See if we've been asked to expand our children.
        for i in range(len(substate)):
            sub=substate[i]
            if sub[0]==id:
                exp=i+1
                break
        if not exp: items=1

    get=md.guarded_getattr
    if get is None:
        get = getattr

    if items is None:
        if have_arg('branches') and hasattr(self, args['branches']):
            items = get(self, args['branches'])
            items = items()
        elif have_arg('branches_expr'):
            items=args['branches_expr'](md)

        if not items and have_arg('leaves'): items=1

    if items and items != 1:

        getitem = getattr(md, 'guarded_getitem', None)
        if getitem is not None:
            unauth=[]
            for index in range(len(items)):
                try:
                    getitem(items, index)
                except ValidationError:
                    unauth.append(index)
            if unauth:
                if have_arg('skip_unauthorized') and args['skip_unauthorized']:
                    items=list(items)
                    unauth.reverse()
                    for index in unauth: del items[index]
                else:
                    raise ValidationError, unauth

        if have_arg('sort'):
            # Faster/less mem in-place sort
            if type(items)==type(()):
                items=list(items)
            sort=args['sort']
            size=range(len(items))
            for i in size:
                v=items[i]
                k=getattr(v,sort)
                try:    k=k()
                except: pass
                items[i]=(k,v)
            items.sort()
            for i in size:
                items[i]=items[i][1]

        if have_arg('reverse'):
            items=list(items)           # Copy the list
            items.reverse()

    diff.append(id)


    _td_colspan='<td colspan="%s" style="white-space: nowrap"></td>'
    _td_single ='<td width="16" style="white-space: nowrap"></td>'

    sub=None
    if substate is state:
        output('<table cellspacing="0">\n')
        sub=substate[0]
        exp=items
    else:
        # Add prefix
        output('<tr>\n')

        # Add +/- icon
        if items:
            if level:
                if level > 3:   output(_td_colspan % (level-1))
                elif level > 1: output(_td_single * (level-1))
                output(_td_single)
                output('\n')
            output('<td width="16" valign="top" style="white-space: nowrap">')
            for i in range(len(substate)):
                sub=substate[i]
                if sub[0]==id:
                    exp=i+1
                    break

            ####################################
            # Mostly inline encode_seq for speed
            s=compress(dumps(diff,1))
            if len(s) > 57: s=encode_str(s)
            else:
                s=b2a_base64(s)[:-1]
                l=s.find('=')
                if l >= 0: s=s[:l]
            s=translate(s, tplus)
            ####################################

            script=md['BASEPATH1']

            # Propagate extra args through tree.
            if args.has_key( 'urlparam' ):
                param = args['urlparam']
                param = "%s&" % param
            else:
                param = ""

            if exp:
                ptreeData['tree-item-expanded']=1
                output('<a name="%s" href="%s?%stree-c=%s#%s">'
                       '<img src="%s/p_/mi" alt="-" border="0" /></a>' %
                       (id, root_url, param, s, id, script))
            else:
                output('<a name="%s" href="%s?%stree-e=%s#%s">'
                       '<img src="%s/p_/pl" alt="+" border="0" /></a>' %
                       (id, root_url, param, s, id, script))
            output('</td>\n')

        else:
            if level > 2:   output(_td_colspan % level)
            elif level > 0: output(_td_single  * level)
            output(_td_single)
            output('\n')


        # add item text
        dataspan=colspan-level
        output('<td%s%s valign="top" align="left">' %
               ((dataspan > 1 and (' colspan="%s"' % dataspan) or ''),
               (have_arg('nowrap') and
                args['nowrap'] and ' style="white-space: nowrap"' or ''))
               )
        output(render_blocks(section, md))
        output('</td>\n</tr>\n')


    if exp:

        level=level+1
        dataspan=colspan-level
        if level > 2:   h=_td_colspan % level
        elif level > 0: h=_td_single  * level
        else: h=''

        if have_arg('header'):
            doc=args['header']
            if md.has_key(doc): doc=md.getitem(doc,0)
            else: doc=None
            if doc is not None:
                output(doc(
                    None, md,
                    standard_html_header=(
                        '<tr>%s'
                        '<td width="16" style="white-space: nowrap"></td>'
                        '<td%s valign="top">'
                        % (h,
                           (dataspan > 1 and (' colspan="%s"' % dataspan)
                            or ''))),
                    standard_html_footer='</td></tr>',
                    ))

        if items==1:
            # leaves
            if have_arg('leaves'):
                doc=args['leaves']
                if md.has_key(doc): doc=md.getitem(doc,0)
                else: doc=None
                if doc is not None:
                    treeData['-tree-substate-']=sub
                    ptreeData['tree-level']=level
                    md._push(treeData)
                    try: output(doc(
                        None,md,
                        standard_html_header=(
                            '<tr>%s'
                            '<td width="16" style="white-space: nowrap"></td>'
                            '<td%s valign="top">'
                            % (h,
                               (dataspan > 1 and
                                (' colspan="%s"' % dataspan) or ''))),
                        standard_html_footer='</td></tr>',
                        ))
                    finally: md._pop(1)
        elif have_arg('expand'):
            doc=args['expand']
            if md.has_key(doc): doc=md.getitem(doc,0)
            else: doc=None
            if doc is not None:
                treeData['-tree-substate-']=sub
                ptreeData['tree-level']=level
                md._push(treeData)
                try: output(doc(
                    None,md,
                    standard_html_header=(
                        '<tr>%s<td width="16" style="white-space: nowrap"></td>'
                        '<td%s valign="top">'
                        % (h,
                           (dataspan > 1 and
                            (' colspan="%s"' % dataspan) or ''))),
                    standard_html_footer='</td></tr>',
                    ))
                finally: md._pop(1)
        else:
            __traceback_info__=sub, args, state, substate
            ids={}
            for item in items:
                if hasattr(item, idattr):
                    id = try_call_attr(item, idattr)
                elif hasattr(item, '_p_oid'): id=oid(item)
                else: id=pyid(item)
                if len(sub)==1: sub.append([])
                substate=sub[1]
                ids[id]=1
                md._push(InstanceDict(item,md))
                try: data=tpRenderTABLE(
                    item,id,root_url,url,state,substate,diff,data,
                    colspan, section, md, treeData, level, args)
                finally: md._pop()
                if not sub[1]: del sub[1]

            ids=ids.has_key
            for i in range(len(substate)-1,-1):
                if not ids(substate[i][0]): del substate[i]

        if have_arg('footer'):
            doc=args['footer']
            if md.has_key(doc): doc=md.getitem(doc,0)
            else: doc=None
            if doc is not None:
                output(doc(
                    None, md,
                    standard_html_header=(
                        '<tr>%s<td width="16" style="white-space: nowrap"></td>'
                        '<td%s valign="top">'
                        % (h,
                           (dataspan > 1 and (' colspan="%s"' % dataspan)
                            or ''))),
                    standard_html_footer='</td></tr>',
                    ))

    del diff[-1]
    if not diff: output('</table>\n')

    return data


def apply_diff(state, diff, expand):
    if not diff: return
    s=[None, state]
    diff.reverse()
    __traceback_info__=s, diff
    while diff:
        id=diff[-1]
        del diff[-1]
        if len(s)==1: s.append([])
        s=s[1]
        if type(s)==type(()):
            s=list(s)
        loc=-1
        for i in range(len(s)):
            if s[i][0]==id:
                loc=i
                break

        if loc >= 0:
            if not diff and not expand:
                del s[loc]
            else:
                s=s[loc]
        elif diff or expand:
            s.append([id,[]])
            s=s[-1][1]
            while diff:
                id=diff[-1]
                del diff[-1]
                if diff or expand:
                    s.append([id,[]])
                    s=s[-1][1]


def encode_seq(state):
    "Convert a sequence to an encoded string"
    state=compress(dumps(state))
    l=len(state)

    if l > 57:
        states=[]
        for i in range(0,l,57):
            states.append(b2a_base64(state[i:i+57])[:-1])
        state=''.join(states)
    else: state=b2a_base64(state)[:-1]

    l=state.find('=')
    if l >= 0: state=state[:l]

    state=translate(state, tplus)
    return state

def encode_str(state):
    "Convert a sequence to an encoded string"
    l=len(state)

    if l > 57:
        states=[]
        for i in range(0,l,57):
            states.append(b2a_base64(state[i:i+57])[:-1])
        state=''.join(states)
    else: state=b2a_base64(state)[:-1]

    l=state.find('=')
    if l >= 0: state=state[:l]

    state=translate(state, tplus)
    return state

def decode_seq(state):
    "Convert an encoded string to a sequence"
    state=translate(state, tminus)
    l=len(state)

    if l > 76:
        states=[]
        j=0
        for i in range(l/76):
            k=j+76
            states.append(a2b_base64(state[j:k]))
            j=k

        if j < l:
            state=state[j:]
            l=len(state)
            k=l%4
            if k: state=state+'='*(4-k)
            states.append(a2b_base64(state))
        state=''.join(states)
    else:
        l=len(state)
        k=l%4
        if k: state=state+'='*(4-k)
        state=a2b_base64(state)

    state=decompress(state)
    try: return list(MiniUnpickler(StringIO(state)).load())
    except: return []

def decompress(input,max_size=10240):
    # This sillyness can go away in python 2.2
    d = decompressobj()
    output = ''
    while input:
        fragment_size = max(1,(max_size-len(output))/1000)
        fragment,input = input[:fragment_size],input[fragment_size:]
        output += d.decompress(fragment)
        if len(output)>max_size:
            raise ValueError('Compressed input too large')
    return output+d.flush()

def tpStateLevel(state, level=0):
    for sub in state:
        if len(sub)==2: level = max(level, 1+tpStateLevel(sub[1]))
        else: level=max(level,1)
    return level

def tpValuesIds(self, get_items, args,
                try_call_attr=try_call_attr,
                ):
    # get_item(node) is a function that returns the subitems of node

    # This should build the ids of subitems which are
    # expandable (non-empty). Leaves should never be
    # in the state - it will screw the colspan counting.
    r=[]
    idattr=args['id']
    try:
        try: items=get_items(self)
        except AttributeError: items=()
        for item in items:
            try:
                if get_items(item):

                    if hasattr(item, idattr):
                        id = try_call_attr(item, idattr)
                    elif hasattr(item, '_p_oid'): id=oid(item)
                    else: id=pyid(item)

                    e=tpValuesIds(item, get_items, args)
                    if e: id=[id,e]
                    else: id=[id]
                    r.append(id)
            except: pass
    except: pass
    return r


def oid(self):
    return b2a_base64(str(self._p_oid))[:-1]


#icoSpace='<IMG SRC="Blank_icon" BORDER="0">'
#icoPlus ='<IMG SRC="Plus_icon" BORDER="0">'
#icoMinus='<IMG SRC="Minus_icon" BORDER="0">'





###############################################################################
## Everthing below here should go in a MiniPickle.py module, but keeping it
## internal makes an easier patch


import pickle
from cStringIO import StringIO


if pickle.format_version!="2.0":
    # Maybe the format changed, and opened a security hole
    raise 'Invalid pickle version'


class MiniUnpickler(pickle.Unpickler):
    """An unpickler that can only handle simple types.
    """
    def refuse_to_unpickle(self):
        raise pickle.UnpicklingError, 'Refused'

    dispatch = pickle.Unpickler.dispatch.copy()

    for k,v in dispatch.items():
        if k=='' or k in '().012FGIJKLMNTUVXS]adeghjlpqrstu}':
            # This key is necessary and safe, so leave it in the map
            pass
        else:
            dispatch[k] = refuse_to_unpickle
            # Anything unnecessary is banned, but here is some logic to explain why
            if k in [pickle.GLOBAL, pickle.OBJ, pickle.INST, pickle.REDUCE, pickle.BUILD]:
                # These are definite security holes
                pass
            elif k in [pickle.PERSID, pickle.BINPERSID]:
                # These are just unnecessary
                pass
    del k
    del v

def _should_succeed(x,binary=1):
    if x != MiniUnpickler(StringIO(pickle.dumps(x,binary))).load():
        raise ValueError(x)

def _should_fail(x,binary=1):
    try:
        MiniUnpickler(StringIO(pickle.dumps(x,binary))).load()
        raise ValueError(x)
    except pickle.UnpicklingError, e:
        if e[0]!='Refused': raise ValueError(x)

class _junk_class:
    pass

def _test():
    _should_succeed('hello')
    _should_succeed(1)
    _should_succeed(1L)
    _should_succeed(1.0)
    _should_succeed((1,2,3))
    _should_succeed([1,2,3])
    _should_succeed({1:2,3:4})
    _should_fail(open)
    _should_fail(_junk_class)
    _should_fail(_junk_class())

# Test MiniPickle on every import
_test()
