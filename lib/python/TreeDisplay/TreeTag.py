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
"""Rendering object hierarchies as Trees
"""
__rcs_id__='$Id: TreeTag.py,v 1.42 2000/06/01 13:48:08 jim Exp $'
__version__='$Revision: 1.42 $'[11:-2]

from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_String import String

from string import join, split, rfind, find, translate
from urllib import quote, unquote
from zlib import compress, decompress
from binascii import b2a_base64, a2b_base64

tbl=join(map(chr, range(256)),'')
tplus=tbl[:ord('+')]+'-'+tbl[ord('+')+1:]
tminus=tbl[:ord('-')]+'+'+tbl[ord('-')+1:]

class Tree:
    name='tree'
    blockContinuations=()
    expand=None

    def __init__(self, blocks):
        tname, args, section = blocks[0]
        args=parse_params(args, name=None, expr=None, nowrap=1, 
                          expand=None, leaves=None,
                          header=None, footer=None,
                          branches=None, branches_expr=None,
                          sort=None, reverse=1, skip_unauthorized=1,
                          id=None, single=1, url=None,
                          # opened_decoration=None,
                          # closed_decoration=None,
                          # childless_decoration=None,
                          assume_children=1,
                          urlparam=None)
        has_key=args.has_key

        if has_key('name'): name=args['name']
        elif has_key(''): name=args['name']=args['']
        else: name='a tree tag'

        if has_key('branches_expr'):
            if has_key('branches'):
                raise ParseError, _tm(
                    'branches and  and branches_expr given', 'tree')
            args['branches_expr']=VSEval.Eval(
                args['branches_expr'], expr_globals).eval
        elif not has_key('branches'): args['branches']='tpValues'

        if not has_key('id'): args['id']='tpId'
        if not has_key('url'): args['url']='tpURL'
        if not has_key('childless_decoration'):
            args['childless_decoration']=''
        
        self.__name__ = name
        self.section=section.blocks
        self.args=args
        if args.has_key('expr'):
            if args.has_key('name'):
                raise ParseError, _tm('name and expr given', 'tree')
            args['expr']=VSEval.Eval(args['expr'], expr_globals)
            

    def render(self,md):
        args=self.args
        have=args.has_key

        if have('name'): v=md[args['name']]
        elif have('expr'): v=args['expr'].eval(md)
        else: v=md.this
        return tpRender(v,md,self.section, self.args)

    __call__=render

String.commands['tree']=Tree

pyid=id # Copy builtin

def tpRender(self, md, section, args,
             simple_type={type(''):0, type(1):0, type(1.0):0}.has_key):
    """Render data organized as a tree.

    We keep track of open nodes using a cookie.  The cookie stored the
    tree state. State should be a tree represented like:

      []  # all closed
      ['eagle'], # eagle is open
      ['eagle'], ['jeep', [1983, 1985]]  # eagle, jeep, 1983 jeep and 1985 jeep

    where the items are object ids. The state will be converted to a
    compressed and base64ed string that gets unencoded, uncompressed, 
    and evaluated on the other side.

    Note that ids used in state need not be connected to urls, since
    state manipulation is internal to rendering logic.

    Note that to make eval safe, we do not allow the character '*' in
    the state.
    """

    data=[]

    idattr=args['id']
    if hasattr(self, idattr):
        id=getattr(self, idattr)
        if not simple_type(type(id)): id=id()            
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
                    validate=md.validate
                    if validate is None or not hasattr(node, 'aq_acquire'):
                        items=getattr(node, branches)
                    else:
                        items=node.aq_acquire(branches, validate, md)
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
        l=rfind(root,'/')
        if l >= 0: root=root[l+1:]

    treeData={'tree-root-url': root,
              'tree-colspan': colspan,
              'tree-state': state }
    
    md._push(InstanceDict(self, md))
    md._push(treeData)

    try: tpRenderTABLE(self,id,root,url,state,substate,diff,data,colspan,
                       section,md,treeData, level, args)
    finally: md._pop(2)

    if state is substate and not (args.has_key('single') and args['single']):
        state=state or ([id],)
        state=encode_seq(state)
        md['RESPONSE'].setCookie('tree-s',state)

    return join(data,'')

def tpRenderTABLE(self, id, root_url, url, state, substate, diff, data,
                  colspan, section, md, treeData, level=0, args=None,
                  simple_type={type(''):0, type(1):0, type(1.0):0}.has_key,
                  ):
    "Render a tree as a table"

    have_arg=args.has_key
    exp=0

    if level >= 0:
        urlattr=args['url']
        if urlattr and hasattr(self, urlattr):
            tpUrl=getattr(self, urlattr)
            if not simple_type(type(tpUrl)): tpUrl=tpUrl()            
            url = (url and ('%s/%s' % (url, tpUrl))) or tpUrl
            root_url = root_url or tpUrl

    treeData['tree-item-url']=url
    treeData['tree-level']=level
    treeData['tree-item-expanded']=0
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

    if items is None:
        validate=md.validate
        if have_arg('branches') and hasattr(self, args['branches']):
            if validate is None or not hasattr(self, 'aq_acquire'):
                items=getattr(self, args['branches'])
            else:
                items=self.aq_acquire(args['branches'],validate,md)
            items=items()
        elif have_arg('branches_expr'):
            items=args['branches_expr'](md)

        if not items and have_arg('leaves'): items=1

    if items and items != 1:

        if validate is not None:
            unauth=[]
            index=0
            for i in items:
                try: v=validate(items,items,None,i,md)
                except: v=0
                if not v: unauth.append(index)
                index=index+1

            if unauth:
                if have_arg('skip_unauthorized') and args['skip_unauthorized']:
                    items=list(items)
                    unauth.reverse()
                    for i in unauth: del items[i]
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


    _td_colspan='<TD COLSPAN="%s" NOWRAP></TD>'
    _td_single ='<TD WIDTH="16" NOWRAP></TD>'

    sub=None
    if substate is state:
        output('<TABLE CELLSPACING="0">\n')
        sub=substate[0]
        exp=items
    else:
        # Add prefix
        output('<TR>\n')

        # Add +/- icon
        if items:
            if level:
                if level > 3:   output(_td_colspan % (level-1))
                elif level > 1: output(_td_single * (level-1))
                output(_td_single)
                output('\n')
            output('<TD WIDTH="16" VALIGN="TOP" NOWRAP>')
            for i in range(len(substate)):
                sub=substate[i]
                if sub[0]==id:
                    exp=i+1
                    break

            ####################################
            # Mostly inline encode_seq for speed
            s=compress(str(diff))
            if len(s) > 57: s=encode_str(s)
            else:
                s=b2a_base64(s)[:-1]
                l=find(s,'=')
                if l >= 0: s=s[:l]
            s=translate(s, tplus)
            ####################################

            script=md['SCRIPT_NAME']

            # Propagate extra args through tree.
            if args.has_key( 'urlparam' ):
                param = args['urlparam']
                param = "%s&" % param
            else:
                param = ""

            if exp:
                treeData['tree-item-expanded']=1
                output('<A NAME="%s" HREF="%s?%stree-c=%s#%s">'
                       '<IMG SRC="%s/p_/mi" ALT="-" BORDER=0></A>' %
                       (id, root_url, param, s, id, script))
            else:
                output('<A NAME="%s" HREF="%s?%stree-e=%s#%s">'
                       '<IMG SRC="%s/p_/pl" ALT="+" BORDER=0></A>' %
                       (id, root_url, param, s, id, script))
            output('</TD>\n')

        else:
            if level > 2:   output(_td_colspan % level)
            elif level > 0: output(_td_single  * level)
            output(_td_single)
            output('\n')
            
    
        # add item text
        dataspan=colspan-level
        output('<TD%s%s VALIGN="TOP" ALIGN="LEFT">' %
               ((dataspan > 1 and (' COLSPAN="%s"' % dataspan) or ''),
               (have_arg('nowrap') and args['nowrap'] and ' NOWRAP' or ''))
               )
        output(render_blocks(section, md))
        output('</TD>\n</TR>\n')


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
                        '<TR>%s<TD WIDTH="16" NOWRAP></TD>'
                        '<TD%s VALIGN="TOP">'
                        % (h,
                           (dataspan > 1 and (' COLSPAN="%s"' % dataspan)
                            or ''))),
                    standard_html_footer='</TD></TR>',
                    ))
            
        if items==1:
            # leaves
            if have_arg('leaves'):
                doc=args['leaves']
                if md.has_key(doc): doc=md.getitem(doc,0)
                else: doc=None
                if doc is not None:
                    treeData['-tree-substate-']=sub
                    treeData['tree-level']=level
                    md._push(treeData)
                    try: output(doc(
                        None,md,
                        standard_html_header=(
                            '<TR>%s<TD WIDTH="16" NOWRAP></TD>'
                            '<TD%s VALIGN="TOP">'
                            % (h,
                               (dataspan > 1 and
                                (' COLSPAN="%s"' % dataspan) or ''))),
                        standard_html_footer='</TD></TR>',
                        ))
                    finally: md._pop(1)
        elif have_arg('expand'):
            doc=args['expand']
            if md.has_key(doc): doc=md.getitem(doc,0)
            else: doc=None
            if doc is not None:
                treeData['-tree-substate-']=sub
                treeData['tree-level']=level
                md._push(treeData)
                try: output(doc(
                    None,md,
                    standard_html_header=(
                        '<TR>%s<TD WIDTH="16" NOWRAP></TD>'
                        '<TD%s VALIGN="TOP">'
                        % (h,
                           (dataspan > 1 and
                            (' COLSPAN="%s"' % dataspan) or ''))),
                    standard_html_footer='</TD></TR>',
                    ))
                finally: md._pop(1)
        else:
            __traceback_info__=sub, args, state, substate
            ids={}
            for item in items:
                if hasattr(item, idattr):
                    id=getattr(item, idattr)
                    if not simple_type(type(id)): id=id()
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
                        '<TR>%s<TD WIDTH="16" NOWRAP></TD>'
                        '<TD%s VALIGN="TOP">'
                        % (h,
                           (dataspan > 1 and (' COLSPAN="%s"' % dataspan)
                            or ''))),
                    standard_html_footer='</TD></TR>',
                    ))

    del diff[-1]
    if not diff: output('</TABLE>\n')

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
    state=compress(str(state))
    l=len(state)

    if l > 57:
        states=[]
        for i in range(0,l,57):
            states.append(b2a_base64(state[i:i+57])[:-1])
        state=join(states,'')
    else: state=b2a_base64(state)[:-1]

    l=find(state,'=')
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
        state=join(states,'')
    else: state=b2a_base64(state)[:-1]

    l=find(state,'=')
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
        state=join(states,'')
    else:
        l=len(state)
        k=l%4
        if k: state=state+'='*(4-k)
        state=a2b_base64(state)

    state=decompress(state)
    if find(state,'*') >= 0: raise 'Illegal State', state
    try: return list(eval(state,{'__builtins__':{}}))
    except: return []
    

def tpStateLevel(state, level=0):
    for sub in state:
        if len(sub)==2: level = max(level, 1+tpStateLevel(sub[1]))
        else: level=max(level,1)
    return level

def tpValuesIds(self, get_items, args,
                simple_type={type(''):0, type(1):0, type(1.0):0}.has_key,
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
                        id=getattr(item, idattr)
                        if not simple_type(type(id)): id=id()            
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
