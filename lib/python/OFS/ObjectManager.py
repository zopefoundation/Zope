
__doc__="""Object Manager

$Id: ObjectManager.py,v 1.42 1998/05/22 22:30:42 jim Exp $"""

__version__='$Revision: 1.42 $'[11:-2]

import Persistence, App.Management, Acquisition, App.Undo, Globals
from Globals import HTMLFile, HTMLFile
from Globals import MessageDialog, default__class_init__
from string import find,join,lower
from urllib import quote
from DocumentTemplate import html_quote
from cgi_module_publisher import type_converters
from DateTime import DateTime

class ObjectManager(
    App.Management.Navigation,
    App.Management.Tabs,
    Acquisition.Implicit,
    Persistence.Persistent,
    App.Undo.UndoSupport,
    ):
    """Generic object manager

    This class provides core behavior for collections of heterogeneous objects. 
    """

    meta_type  ='ObjectManager'
    meta_types = dynamic_meta_types = ()
    id       ='default'
    title=''
    icon='p_/folder'
    _objects   =()
    _properties =({'id':'title', 'type': 'string'},)

    manage_main          =HTMLFile('main', globals())
    manage_propertiesForm=HTMLFile('properties', globals())

    manage_options=(
    {'icon':icon,              'label':'Objects',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'OFS/Help_icon.gif', 'label':'Help',
     'action':'manage_help',   'target':'_new'},
    )

    isAnObjectManager=1

    isPrincipiaFolderish=1

    def __class_init__(self):
	try:    mt=list(self.meta_types)
	except: mt=[]
	for b in self.__bases__:
	    try:
		for t in b.meta_types:
		    if t not in mt: mt.append(t)
	    except: pass
	mt.sort()
        self.meta_types=tuple(mt)
	
	default__class_init__(self)

    def all_meta_types(self):
	return self.meta_types+self.dynamic_meta_types

    def _checkId(self,id):

	if not id: raise 'Bad Request', 'No <em>id</em> was specified'

	if quote(id) != id: raise 'Bad Request', (
	    """The id <em>%s<em>  is invalid - it
	       contains characters illegal in URLs.""" % id)

	if id[:1]=='_': raise 'Bad Request', (
	    """The id <em>%s<em>  is invalid - it 
               begins with an underscore character, _.""" % id)

	try: self=self.aq_base
	except: return

	if hasattr(self,id): raise 'Bad Request', (
	    """The id <em>%s<em>  is invalid - it
               is already in use.""" % id)

    def _checkObject(self, object):
	t=object.meta_type
	if callable(t): t=t()
	for d in self.all_meta_types():
 	    if d['name']==t: return
	raise 'Bad Request', 'Object type is not supported'

    def parentObject(self):
	try:
	    if self.aq_parent.isAnObjectManager:
		return (self.aq_parent,)
	except: pass
        return ()

    def _setObject(self,id,object,roles=None,user=None):

	self._checkId(id)
	setattr(self,id,object)
	try:    t=object.meta_type
	except: t=None
	self._objects=self._objects+({'id':id,'meta_type':t},)

    def _delObject(self,id):
        delattr(self,id)
        self._objects=tuple(filter(lambda i,n=id: i['id']!=n, self._objects))

    def objectIds(self, spec=None):
        """Return a list of subobject ids.

	Returns a list of subobject ids of the current object.  If 'spec' is
	specified, returns objects whose meta_type matches 'spec'.
	"""
	if spec is not None:
	    if type(spec)==type('s'):
		spec=[spec]
	    set=[]
	    for ob in self._objects:
	        if ob['meta_type'] in spec:
		    set.append(ob['id'])
	    return set
	return map(lambda i: i['id'], self._objects)

    def objectValues(self, spec=None):
        """Return a list of the actual subobjects.

	Returns a list of actual subobjects of the current object.  If
	'spec' is specified, returns only objects whose meta_type match 'spec'
	"""
	if spec is not None:
	    if type(spec)==type('s'):
		spec=[spec]
	    set=[]
	    for ob in self._objects:
		if ob['meta_type'] in spec:
		    set.append(getattr(self, ob['id']))
	    return set
	return map(lambda i,s=self: getattr(s,i['id']), self._objects)

    def objectItems(self, spec=None):
        """Return a list of (id, subobject) tuples.

	Returns a list of (id, subobject) tuples of the current object.
	If 'spec' is specified, returns only objects whose meta_type match
	'spec'
	"""
	if spec is not None:
	    if type(spec)==type('s'):
		spec=[spec]
	    set=[]
	    for ob in self._objects:
		if ob['meta_type'] in spec:
		    set.append((ob['id'], getattr(self, ob['id'])))
	return map(lambda i,s=self: (i['id'], getattr(s,i['id'])),
		                    self._objects)
    def objectMap(self):
	# Return a tuple of mappings containing subobject meta-data
        return self._objects

    def objectIds_d(self,t=None):
	v=self.objectIds(t)
	try:    n=self._reserved_names
	except: return v
	return filter(lambda x,r=n: x not in r, v)

    def objectValues_d(self,t=None):
	v=self.objectIds(t)
	try:    n=self._reserved_names
	except: return map(lambda i,s=self: getattr(s,i), v)
	return map(lambda i,s=self: getattr(s,i),
	            filter(lambda x,r=n: x not in r, v))

    def objectItems_d(self,t=None):
	v=self.objectItems(t)
	try:    n=self._reserved_names
	except: return v
	return filter(lambda x,r=n: x[0] not in r, v)

    def objectMap_d(self,t=None):
	v=self._objects
	try:    n=self._reserved_names
	except: return v
	return filter(lambda x,r=n: x['id'] not in r, v)

    def superIds(self,t):
        if type(t)==type('s'): t=(t,)
        obj=self
        vals=[]
        x=0
        while x < 100:
	    try:    set=obj._objects
	    except: set=()
	    for i in set:
	        try:
		    if i['meta_type'] in t:
			id=i['id']
			if not id in vals: vals.append(id)
	        except: pass
	    try:    obj=obj.aq_parent
	    except: return vals
	    x=x+1
	return vals

    def superValues(self,t):
        if type(t)==type('s'): t=(t,)
        obj=self
        seen={}
        vals=[]
	have=seen.has_key
        x=0
        while x < 100:
	    try:    set=obj._objects
	    except: set=()
	    for i in set:
	        try:
		    id=i['id']
		    if (not have(id)) and (i['meta_type'] in t):
			vals.append(getattr(obj,id))
			seen[id]=1
	        except: pass
	    try:    obj=obj.aq_parent
	    except: return vals
	    x=x+1
	return vals

    def superItems(self,t):
        if type(t)==type('s'): t=(t,)
        obj=self
        seen={}
        vals=[]
	have=seen.has_key
        x=0
        while x < 100:
	    try:    set=obj._objects
	    except: set=()
	    for i in set:
	        try:
		    id=i['id']
		    if (not have(id)) and (i['meta_type'] in t):
			vals.append((id,getattr(obj,id),))
			seen[id]=1
	        except: pass
	    try:    obj=obj.aq_parent
	    except: return vals
	    x=x+1
	return vals

    def superHasAttr(self,attr):
        obj=self
        seen={}
        vals=[]
	have=seen.has_key
        x=0
        while x < 100:
	    try:    set=obj._objects
	    except: set=()
	    for i in set:
	        try:
		    id=i['id']
		    if not have(id):
			v=getattr(obj,id)
			if hasattr(v,attr):
			    vals.append(v)
			    seen[id]=1
	        except: pass
	    try:    obj=obj.aq_parent
	    except: return vals
	    x=x+1
	return vals

    def manage_addObject(self,type,REQUEST):
	"""Add a subordinate object"""
	for t in self.meta_types:
	    if t['name']==type:
		return getattr(self,t['action'])(
		    self,REQUEST,
		    aclEChecked='', aclAChecked=' CHECKED', aclPChecked=''
		    )
	for t in self.dynamic_meta_types:
	    if t['name']==type:
		return getattr(self,t['action'])(
		    self,REQUEST,
		    aclEChecked='', aclAChecked=' CHECKED', aclPChecked='')
	raise 'BadRequest', 'Unknown object type: %s' % type


    def manage_delObjects(self,ids=[],submit='',clip_id='',
			  clip_data='',REQUEST=None):
	"""Copy/Paste/Delete a subordinate object
	
	Based on the value of 'submit', the objects specified in 'ids' get
	copied, pasted, or deleted.  'Copy' can only work on one object id.
	'Paste' uses the parameters 'clip_id' and 'clip_data' to paste.
	'Delete' removes the objects specified in 'ids'.
	"""
	if submit=='Cut':
	    c=len(ids)
	    if (c <= 0) or (c > 1):
		return MessageDialog(
		       title='Invalid Selection',
		       message='Please select one and only one item to move',
		       action ='./manage_main',)
	    obj=getattr(self, ids[0])
	    err=obj.cutToClipboard(REQUEST)
	    return err or self.manage_main(self, REQUEST, validClipData=1)

	if submit=='Copy':
	    c=len(ids)
	    if (c <= 0) or (c > 1):
		return MessageDialog(
		       title='Invalid Selection',
		       message='Please select one and only one item to copy',
		       action ='./manage_main',)
	    obj=getattr(self, ids[0])
	    err=obj.copyToClipboard(REQUEST)
	    return err or self.manage_main(self, REQUEST, validClipData=1)

	if submit=='Paste':
	    return self.pasteFromClipboard(clip_id,clip_data,REQUEST)


	if submit=='Delete':
	    if not ids:
		return MessageDialog(title='No items specified',
		       message='No items were specified!',
		       action ='./manage_main',)

	    try:    p=self._reserved_names
	    except: p=()
	    for n in ids:
		if n in p:
		    return MessageDialog(title='Not Deletable',
			   message='<EM>%s</EM> cannot be deleted.' % n,
			   action ='./manage_main',)
	    while ids:
		try:    self._delObject(ids[-1])
		except: raise 'BadRequest', ('%s does not exist' % ids[-1])
	        del ids[-1]
	    if REQUEST is not None:
		return self.manage_main(self, REQUEST, update_menu=1)


    def _setProperty(self,id,value,type='string'):
        self._checkId(id)
	self._properties=self._properties+({'id':id,'type':type},)
        setattr(self,id,value)

    def _delProperty(self,id):
        delattr(self,id)
        self._properties=tuple(filter(lambda i, n=id: i['id'] != n,
				     self._properties))
    def propertyIds(self):
        """ Return a list of property ids """
	return map(lambda i: i['id'], self._properties)

    def propertyValues(self):
        """ Return a list of actual property objects """
	return map(lambda i,s=self: getattr(s,i['id']), self._properties)

    def propertyItems(self):
        """ Return a list of (id,property) tuples """
	return map(lambda i,s=self: (i['id'],getattr(s,i['id'])), 
		                    self._properties)
    def propertyMap(self):
        """ Return a tuple of mappings, giving meta-data for properties """
        return self._properties

    def propertyMap_d(self):
	v=self._properties
	try:    n=self._reserved_names
	except: return v
	return filter(lambda x,r=n: x['id'] not in r, v)

    def manage_addProperty(self,id,value,type,REQUEST=None):
	"""Add a new property (www)

	Sets a new property with id, type, and value.
	"""
	try:    value=type_converters[type](value)
	except: pass
	self._setProperty(id,value,type)
	if REQUEST is not None:
	    return self.manage_propertiesForm(self, REQUEST)

    def manage_editProperties(self,REQUEST):
	"""Edit object properties"""
	for p in self._properties:
	    n=p['id']
	    try:    setattr(self,n,REQUEST[n])
	    except: setattr(self,n,'')
	return MessageDialog(
	       title  ='Success!',
	       message='Your changes have been saved',
	       action ='manage_propertiesForm')

    def manage_changeProperties(self, REQUEST=None, **kw):
	"""Change existing object properties.

	Change object properties by passing either a mapping object
	of name:value pairs {'foo':6} or passing name=value parameters
	"""
	if REQUEST is None:
	    props={}
	else:
	    props=REQUEST

	if kw:
	    for name, value in kw.items():
		props[name]=value

	for name, value in props.items():
	    if self.hasProperty(name):
		setattr(self, name, value)
    
	if REQUEST is not None:
	    return MessageDialog(
		title  ='Success!',
		message='Your changes have been saved',
		action ='manage_propertiesForm')

    def hasProperty(self, id):
	"""returns 1 if object has a settable property 'id'"""
	for p in self._properties:
	    if id == p['id']: return 1
	return 0

    def manage_delProperties(self,ids,REQUEST=None):
	"""Delete one or more properties

	Deletes properties specified by 'ids'
	"""
	try:    p=self._reserved_names
	except: p=()
	if ids is None:
	    return MessageDialog(title='No property specified',
		   message='No properties were specified!',
		   action ='./manage_propertiesForm',)
	for n in ids:
	    if n in p:
	        return MessageDialog(
	        title  ='Cannot delete %s' % n,
	        message='The property <I>%s</I> cannot be deleted.' % n,
	        action ='manage_propertiesForm')
	    try:    self._delProperty(n)
	    except: raise 'BadRequest', (
		          'The property <I>%s</I> does not exist' % n)
	if REQUEST is not None:
	    return self.manage_propertiesForm(self, REQUEST)


    def _defaultInput(self,n,t,v):
        return '<INPUT NAME="%s:%s" SIZE="40" VALUE="%s"></TD>' % (n,t,v)

    def _stringInput(self,n,t,v):
        return ('<INPUT NAME="%s:%s" SIZE="40" VALUE="%s"></TD>'
		% (n,t,html_quote(v)))

    def _booleanInput(self,n,t,v):
	if v: v="CHECKED"
	else: v=''
        return ('<INPUT TYPE="CHECKBOX" NAME="%s:%s" SIZE="50" %s></TD>'
		% (n,t,v))

    def _selectInput(self,n,t,v):
        s=['<SELECT NAME="%s:%s">' % (n,t)]
	map(lambda i: s.append('<OPTION>%s' % i), v)
        s.append('</SELECT>')
        return join(s,'\n')

    def _linesInput(self,n,t,v):
	try: v=html_quote(join(v,'\n'))
	except: v=''
        return (
	'<TEXTAREA NAME="%s:lines" ROWS="10" COLS="40">%s</TEXTAREA>'
	% (n,v))

    def _tokensInput(self,n,t,v):
	try: v=html_quote(join(v,' '))
	except: v=''
        return ('<INPUT NAME="%s:%s" SIZE="40" VALUE="%s"></TD>'
		% (n,t,html_quote(v)))

    def _textInput(self,n,t,v):
        return ('<TEXTAREA NAME="%s:text" ROWS="10" COLS="40">%s</TEXTAREA>'
		% (n,html_quote(v)))

    _inputMap={
	'float': 	_defaultInput,
	'int':   	_defaultInput,
	'long':  	_defaultInput,
	'string':	_stringInput,
	'lines': 	_linesInput,
	'text':  	_textInput,
	'date':	 	_defaultInput,
	'tokens':	_tokensInput,	
#	'boolean':	_booleanInput,	
	}

    propertyTypes=map(lambda key: (lower(key), key), _inputMap.keys())
    propertyTypes.sort()
    propertyTypes=map(lambda key:
		      {'id': key[1],
		       'selected': key[1]=='string' and 'SELECTED' or ''},
		      propertyTypes)
		      

    def propertyInputs(self):
	imap=self._inputMap
        r=[]
	for p in self._properties:
	    n=p['id']
	    t=p['type']
	    v=getattr(self,n)
	    r.append({'id': n, 'input': imap[t](None,n,t,v)})
	return r



##############################################################################
#
# $Log: ObjectManager.py,v $
# Revision 1.42  1998/05/22 22:30:42  jim
# Moved some DB-related methods from ObjectManager and SimpleItem and stuffed them
# right into Persistent in Globals.
#
# Changed aq_self to aq_base.
#
# Revision 1.41  1998/04/24 16:11:09  brian
# Added Cut(Move) support for principia objects.
#
# Revision 1.40  1998/04/15 14:58:11  jim
# Don't show confirmation after add or delete.
#
# Revision 1.39  1998/04/09 17:18:41  jim
# Added extra logic to verify session locks, which can become
# stale after a session undo.
#
# Revision 1.38  1998/03/18 20:48:10  jeffrey
# Added some new property management options and Encyclopedia-esque doc
# strings
#
# Revision 1.37  1998/03/18 17:54:29  brian
# Fixed bug that required objects to have a __len__ when a specifier was
# given to objectValues, Ids, and Items.
#
# Revision 1.36  1998/03/09 19:58:20  jim
# changed session marking support
#
# Revision 1.35  1998/02/10 18:38:01  jim
# Removed validation check.
#
# Revision 1.34  1998/01/26 21:01:31  brian
# Added menu update support
#
# Revision 1.33  1998/01/26 16:33:13  brian
# Added confirmation to property editing
#
# Revision 1.31  1998/01/08 17:40:42  jim
# Modified __class_init__ to use default class init defined in Globals.
#
# Revision 1.30  1998/01/02 18:45:06  jim
# Ooops, want implicit acquisition.
#
# Revision 1.29  1998/01/02 17:40:12  jim
# Factored old Management mix-in into Navigation and Tabs.
#
# Revision 1.28  1997/12/31 19:17:18  jim
# Fixed buglet in signature of manage_delObjects.
#
# Revision 1.27  1997/12/19 19:11:17  jim
# updated icon management strategy
#
# Revision 1.26  1997/12/18 21:12:49  jeffrey
# more ImageFile tweaks
#
# Revision 1.25  1997/12/18 16:45:41  jeffrey
# changeover to new ImageFile and HTMLFile handling
#
# Revision 1.24  1997/12/16 20:04:43  jim
# Modified copying code to set validClipData in manage_main so that
# the paste button shows up after copy.
#
# Revision 1.23  1997/12/12 16:14:03  jim
# Added :text for text properties.
#
# Revision 1.22  1997/12/05 17:13:50  brian
# New UI
#
# Revision 1.21  1997/11/26 23:47:00  paul
# if REQUEST is None added
#
# Revision 1.20  1997/11/18 14:10:50  jim
# Fixed a bug in handling 'tokens' properties and got rid of regex
# properties.
#
# Revision 1.19  1997/11/11 21:25:29  brian
# Added copy/paste support, restricted unpickling, fixed DraftFolder bug
#
# Revision 1.18  1997/11/11 18:52:53  jim
# Fixed bug in modified_in_session.
#
# Revision 1.17  1997/11/10 14:54:42  jim
# Added two new methods, bobobase_modification_time, and
# modified_in_session, to support flagging new and session objects.
#
# Revision 1.16  1997/11/06 15:41:48  jim
# Got rid of PARENT_URL in deleteProperties error dialog.
#
# Revision 1.15  1997/11/06 15:39:30  jim
# Modified to pass access radio box settings into add templates.
#
# Revision 1.14  1997/11/05 16:39:10  brian
# Style fix
#
# Revision 1.13  1997/09/25 15:44:18  brian
# *** empty log message ***
#
# Revision 1.12  1997/09/25 15:43:35  brian
# Added document_id, document_title
#
# Revision 1.11  1997/09/25 14:30:39  brian
# Fixed property typing error
#
# Revision 1.10  1997/09/18 22:48:45  brian
# Deletable object filters added
#
# Revision 1.9  1997/09/18 20:03:37  brian
# Added superX type sniffer
#
# Revision 1.8  1997/09/02 18:39:50  jim
# Added check for missing or blank ids.
#
# Revision 1.7  1997/08/18 15:14:54  brian
# Made changes to manage_options to support std icons
#
# Revision 1.6  1997/08/13 19:09:05  jim
# Got rid of ManageHTMLFile
#
# Revision 1.5  1997/08/08 23:03:51  jim
# Improved property handling.
#
# Revision 1.4  1997/08/08 16:54:12  jim
# Changed to allow overriding of acquired attributes.
#
# Revision 1.3  1997/08/06 18:26:14  jim
# Renamed description->title and name->id and other changes
#
# Revision 1.2  1997/07/28 21:36:08  jim
# Got rid of some message dialogs.
#
# Revision 1.1  1997/07/25 20:03:24  jim
# initial
#
# Revision 1.1  1997/07/07 16:02:18  jim
# *** empty log message ***
#
#
