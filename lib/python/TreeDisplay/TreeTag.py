
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
__rcs_id__='$Id: TreeTag.py,v 1.6 1997/11/10 16:32:48 jeffrey Exp $'
__version__='$Revision: 1.6 $'[11:-2]

from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_String import String

class Tree:
    name='tree'
    blockContinuations=()
    expand=None

    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name='', expand='')
	name=name_param(args)
	self.__name__ = name
	self.section=section
	if args.has_key('expand') and args['expand']:
	    self.expand=args['expand']

    def render(self,md):
	try: v=md[self.__name__]
	except: v=None
	if v is None: return ''
	expand=self.expand
	if expand: expand=md.getitem(expand,0)
	return tpRender(v,md,self.section, expand)

    __call__=render

String.commands['tree']=Tree

from string import join, split, rfind
from urllib import quote, unquote

pyid=id # Copy builtin


def tpRender(self, md, section, expand):
    data=[]

    try:
	# see if we are being run as a sub-document
	root=md['tree-root-url']
	url=md['tree-item-url']
	state=md['tree-state'] or md['state']
	substate=md['-tree-substate-']
	colspan=md['tree-colspan']	
	level=md['tree-level']
    except KeyError:
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
		    state=md['tree-state'] or md['state'] or md['-tree-state-']
		    if state[0] != '[': state=unquote(state)
		    state=list(eval(state,{'__builtins__':{}}))
		except:
		    state=[]
	colspan=1+tpStateLevel(state)
	level = 0
	substate=state

	root=md['URL']
	l=rfind(root, '/')
	if l >= 0: root=root[l+1:]
	url=''

    # Save state in a cookie
    if state: md['RESPONSE'].setCookie('tree-state',quote(str(state)[1:-1]+','))
    else:     md['RESPONSE'].expireCookie('tree-state')

    if substate==state: data.append('<TABLE CELLSPACING="0">\n')
    #level=0
    treeData={'tree-root-url': root,
	      'tree-colspan': colspan,
	      'tree-state': state }
    
    md.push(treeData)

    try:
	for item in self.tpValues():
	    data=tpRenderTABLE(item,root,url,state,substate,data,colspan,
			       section,md,treeData, level, expand)
	if state is substate: data.append('</TABLE>\n')
	result=join(data,'')
    finally: md.pop(1)
    return result

def tpStateLevel(state, level=0):
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
                  colspan, section, md, treeData, level=0, expand=None):
    try:    items=self.tpValues()
    except: items=None

    tpUrl=self.tpURL()
    url = (url and ('%s/%s' % (url, tpUrl))) or tpUrl
    treeData['tree-item-url']=url
    treeData['tree-level']=level
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
            output('<A HREF="%s?tree-state=%s">%s</A>' %
                   (root_url,quote(str(state)[1:-1]+','), icoMinus))
            substate.append(sub)
        else:
            substate.append([id])
            output('<A HREF="%s?tree-state=%s">%s</A>' %
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
	if expand is not None:
	    treeData['-tree-substate-']=sub
	    treeData['tree-level']=level+1
	    md.push(treeData)
	    output(expand(self,md))
	    md.pop(1)
	else:
	    for item in items:
		if len(sub)==1: sub.append([])
		data=tpRenderTABLE(item, root_url,url,state,sub[1],data,
				   colspan, section, md, treeData, level+1)
		if not sub[1]: del sub[1]
    return data


icoSpace='<IMG SRC="%s/TreeDisplay/Blank_icon.gif" BORDER="0">' % SOFTWARE_URL
icoPlus ='<IMG SRC="%s/TreeDisplay/Plus_icon.gif" BORDER="0">' % SOFTWARE_URL
icoMinus='<IMG SRC="%s/TreeDisplay/Minus_icon.gif" BORDER="0">' % SOFTWARE_URL











