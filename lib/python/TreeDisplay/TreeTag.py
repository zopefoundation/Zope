
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
__rcs_id__='$Id: TreeTag.py,v 1.12 1997/12/02 01:06:31 jim Exp $'
__version__='$Revision: 1.12 $'[11:-2]

from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_String import String


class Tree:
    name='tree'
    blockContinuations=()
    expand=None

    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name=None, expr=None,
			  expand=None, leaves=None,
			  header=None, footer=None,
			  nowrap=1, branches=None)
	has_key=args.has_key

	if has_key('name'): name=args['name']
	elif has_key(''): name=args['name']=args['']
	else: name='a tree tag'

	if not has_key('branches'): args['branches']='tpValues'
	
	self.__name__ = name
	self.section=section
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

from string import join, split, rfind
from urllib import quote, unquote

pyid=id # Copy builtin

def tpRender(self, md, section, args):
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
		state=tpValuesIds(self, args['branches'])
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
    
    md._push(treeData)

    try:
	for item in getattr(self, args['branches'])():
	    data=tpRenderTABLE(item,root,url,state,substate,data,colspan,
			       section,md,treeData, level, args)
	if state is substate: data.append('</TABLE>\n')
	result=join(data,'')
    finally: md._pop(1)
    return result

def tpStateLevel(state, level=0):
    for sub in state:
        if len(sub)==2: level = max(level, 1+tpStateLevel(sub[1]))
        else: level=max(level,1)
    return level

def tpValuesIds(self, branches):
    # This should build the ids of subitems which are
    # expandable (non-empty). Leaves should never be
    # in the state - it will screw the colspan counting.
    r=[]
    try:
	try: items=getattr(self, branches)()
	except AttributeError: items=()
	for item in items:
	    try:
		if getattr(item, branches)():

		    if hasattr(item, 'tpId'): id=item.tpId()
		    elif hasattr(item, '_p_oid'): id=item._p_oid
		    else: id=pyid(item)

		    e=tpValuesIds(item, branches)
		    if e: id=[id,e]
		    else: id=[id]
		    r.append(id)
	    except: pass
    except: pass
    return r
    

def tpRenderTABLE(self, root_url, url, state, substate, data,
                  colspan, section, md, treeData, level=0, args=None):

    have_arg=args.has_key
    try:    items=getattr(self, args['branches'])()
    except: items=None
    if not items and have_arg('leaves'): items=1

    tpUrl=self.tpURL()
    url = (url and ('%s/%s' % (url, tpUrl))) or tpUrl
    treeData['tree-item-url']=url
    treeData['tree-level']=level
    treeData['tree-item-expanded']=0


    if hasattr(self, 'tpId'): id=self.tpId()
    elif hasattr(self, '_p_oid'): id=self._p_oid
    else: id=pyid(self)

    exp=0
    sub=None
    output=data.append

    # Add prefix
    output('<TR>\n')

    # Add +/- icon
    if items:
	if level:
	    if level > 3: output(  '<TD COLSPAN="%s"></TD>' % (level-1))
	    elif level > 1: output('<TD></TD>' * (level-1))
	    output('<TD WIDTH="16"></TD>\n')
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
	output('</TD>\n')
    else:
	if level > 2: output('<TD COLSPAN="%s"></TD>' % level)
	elif level > 0: output('<TD></TD>' * level)
	output('<TD WIDTH="16"></TD>\n')
	


    # add item text
    dataspan=colspan-level
    output('<TD%s%s VALIGN="TOP">' %
	   ((dataspan > 1 and (' COLSPAN="%s"' % dataspan) or ''),
	   (have_arg('nowrap') and args['nowrap'] and ' NOWRAP' or ''))
	   )
    output(section(self, md))
    output('</TD>\n</TR>\n')


    if exp:

	level=level+1
	dataspan=colspan-level
	if level > 3: h='<TD COLSPAN="%s"></TD>' % (level-1)
	elif level > 1: h='<TD></TD>' * (level-1)
	else: h=''

	if have_arg('header'):
	    if md.has_key(args['header']):
		output(md.getitem(args['header'],0)(
		    self, md,
		    standard_html_header=(
			'<TR>%s<TD WIDTH="16"></TD>'
			'<TD%s VALIGN="TOP">'
			% (h,
			   (dataspan > 1 and (' COLSPAN="%s"' % dataspan)
			    or ''))),
		    standard_html_footer='</TD></TR>',
		    ))
	    
	if items==1:
	    # leaves
	    treeData['-tree-substate-']=sub
	    treeData['tree-level']=level
	    md._push(treeData)
	    output(md.getitem(args['leaves'],0)(
		self,md,
		standard_html_header=(
		    '<TR>%s<TD WIDTH="16"></TD>'
		    '<TD%s VALIGN="TOP">'
		    % (h,
		       (dataspan > 1 and (' COLSPAN="%s"' % dataspan) or ''))),
		standard_html_footer='</TD></TR>',
		))
	    md._pop(1)
	elif have_arg('expand'):
	    treeData['-tree-substate-']=sub
	    treeData['tree-level']=level
	    md._push(treeData)
	    output(md.getitem(args['expand'],0)(self,md))
	    md._pop(1)
	else:
	    __traceback_info__=sub, args, state, substate
	    for item in items:
		if len(sub)==1: sub.append([])
		data=tpRenderTABLE(item, root_url,url,state,sub[1],data,
				   colspan, section, md, treeData, level, args)
		if not sub[1]: del sub[1]

	if have_arg('footer'):
	    if md.has_key(args['footer']):
		output(md.getitem(args['footer'],0)(
		    self, md,
		    standard_html_header=(
			'<TR>%s<TD WIDTH="16"></TD>'
			'<TD%s VALIGN="TOP">'
			% (h,
			   (dataspan > 1 and (' COLSPAN="%s"' % dataspan)
			    or ''))),
		    standard_html_footer='</TD></TR>',
		    ))

    return data


icoSpace='<IMG SRC="%s/TreeDisplay/Blank_icon.gif" BORDER="0">' % SOFTWARE_URL
icoPlus ='<IMG SRC="%s/TreeDisplay/Plus_icon.gif" BORDER="0">' % SOFTWARE_URL
icoMinus='<IMG SRC="%s/TreeDisplay/Minus_icon.gif" BORDER="0">' % SOFTWARE_URL











