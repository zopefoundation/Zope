
"""Rendering object hierarchies as Trees
"""
############################################################################
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################ 
__rcs_id__='$Id: TreeTag.py,v 1.3 1997/09/04 22:08:19 brian Exp $'
__version__='$Revision: 1.3 $'[11:-2]

from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_String import String

class Tree:
    name='tree'
    blockContinuations=()

    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name='')
	name=name_param(args)
	self.__name__ = name
	self.section=section

    def render(self,md):
	try: v=md[self.__name__]
	except: v=None
	if v is None: return ''
	return tpRender(v,md,self.section)

    __call__=render

String.commands['tree']=Tree

from string import join, split, rfind
from urllib import quote, unquote

pyid=id # Copy builtin


def tpRender(self, md, section):
    # Check for collapse all, expand all, and state
    try:    collapse_all=md['collapse_all']
    except: collapse_all=None
    if collapse_all:
	state=[]
    else:
	try:    expand_all=md['expand_all']
	except: expand_all=None
	if expand_all:
            state=tpValuesIds(self)
	else:
            try:
                state=md['state']
                if state[0] != '[': state=unquote(state)
                state=list(eval(state,{'__builtins__':{}}))
            except:
		state=[]

    # Save state in a cookie
    if state: md['RESPONSE'].setCookie('state',quote(str(state)[1:-1]+','))
    else:     md['RESPONSE'].expireCookie('state')
    
    root=md['URL']
    l=rfind(root, '/')
    if l >= 0: root=root[l+1:]
    url=''
    data =[]

    data.append('<TABLE CELLSPACING="0">\n')
    colspan=1+tpStateLevel(state)

    treeData={'tree-root-url': root}
    md.push(treeData)
    try:
	for item in self.tpValues():
	    data=tpRenderTABLE(item,root,url,state,state,data,colspan,
			       section,md,treeData)
	data.append('</TABLE>\n')
	result=join(data,'')
    finally: md.pop(1)
    return result

def tpStateLevel(state):
    level=0
    for sub in state:
        if len(sub)==2: level = max(level, 1+tpStateLevel(sub[1]))
        else: level=max(level,1)
    return level

def tpValuesIds(self):
    # This should build the ids of subitems which are
    # expandable (non-empty). Leaves should never be
    # in the state - it will screw the colspan counting.
    r=[]
    try:
	for item in self.tpValues():
	    try:
		if item.tpValues():
		    id=item.tpId()
		    e=tpValuesIds(item)
		    if e: id=[id,e]
		    else: id=[id]
		    r.append(id)
	    except: pass
    except: pass
    return r
    

def tpRenderTABLE(self, root_url, url, state, substate, data,
                  colspan, section, md, treeData, level=0):
    try:    items=self.tpValues()
    except: items=None

    tpUrl=self.tpURL()
    url = (url and ('%s/%s' % (url, tpUrl))) or tpUrl
    treeData['tree-item-url']=url
    treeData['tree-item-expanded']=0


    try:    id=self.tpId()
    except: id=None
    if id is None:
	try:    id=self._p_oid
	except: id=None
	if id is None: id=pyid(self)

    exp=0
    sub=None
    output=data.append

    # Add prefix
    output('<TR>\n')
    if level: output('<TD WIDTH="16"></TD>\n' * level)

    # Add +/- icon
    if items:
        output('<TD WIDTH="16" VALIGN="TOP">')
        for i in range(len(substate)):
            sub=substate[i]
            if sub[0]==id:
                exp=i+1
                break
        if exp:
	    treeData['tree-item-expanded']=1
            del substate[exp-1]
            output('<A HREF="%s?state=%s">%s</A>' %
                   (root_url,quote(str(state)[1:-1]+','), icoMinus))
            substate.append(sub)
        else:
            substate.append([id])
            output('<A HREF="%s?state=%s">%s</A>' %
                   (root_url,quote(str(state)[1:-1]+','), icoPlus))
            del substate[-1]
    else:
        output('<TD WIDTH="16">')
    output('</TD>\n')

    # add item text
    output('<TD COLSPAN="%s" VALIGN="TOP">' % (colspan-level))
    output(section(self, md))
    output('</TD>\n</TR>\n')
    
    if exp:
        for item in items:
            if len(sub)==1: sub.append([])
            data=tpRenderTABLE(item, root_url,url,state,sub[1],data,
			       colspan, section, md, treeData, level+1)
            if not sub[1]: del sub[1]
    return data


icoSpace='<IMG SRC="%s/TreeDisplay/Blank_icon.gif" BORDER="0">' % SOFTWARE_URL
icoPlus ='<IMG SRC="%s/TreeDisplay/Plus_icon.gif" BORDER="0">' % SOFTWARE_URL
icoMinus='<IMG SRC="%s/TreeDisplay/Minus_icon.gif" BORDER="0">' % SOFTWARE_URL

