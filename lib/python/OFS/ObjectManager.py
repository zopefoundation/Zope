
__doc__="""Object Manager

$Id: ObjectManager.py,v 1.8 1997/09/02 18:39:50 jim Exp $"""

__version__='$Revision: 1.8 $'[11:-2]


from SingleThreadedTransaction import Persistent
from Globals import HTMLFile, HTMLFile
from Globals import MessageDialog
from App.Management import Management
from Acquisition import Acquirer
from string import find,join,lower
from urllib import quote
from DocumentTemplate import html_quote

class ObjectManager(Acquirer,Management,Persistent):
    """Generic object manager

    This class provides core behavior for collections of heterogeneous objects. 
    """

    meta_type  ='ObjectManager'
    meta_types = dynamic_meta_types = ()
    id       ='default'
    title=''
    icon       ='OFS/Folder_icon.gif'
    _objects   =()
    _properties =({'id':'title', 'type': 'string'},)

    manage_main          =HTMLFile('OFS/main')
    manage_propertiesForm=HTMLFile('OFS/properties')

    manage_options=(
    {'icon':icon,              'label':'Objects',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'OFS/Help_icon.gif', 'label':'Help',
     'action':'manage_help',   'target':'_new'},
    )

    isAnObjectManager=1

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

	try: self=self.aq_self
	except: return

	if hasattr(self,id): raise 'Bad Request', (
	    """The id <em>%s<em>  is invalid - it
               is already in use.""" % id)

    def parentObject(self):
	try:
	    if self.aq_parent.isAnObjectManager:
		return (self.aq_parent,)
	except: pass
        return ()
        #try:    return (self.aq_parent,)
	#except: return ()

    def _setObject(self,id,object):
	self._checkId(id)
	setattr(self,id,object)
	try:    t=object.meta_type
	except: t=None
	self._objects=self._objects+({'id':id,'meta_type':t},)

    def _delObject(self,id):
        delattr(self,id)
        self._objects=tuple(filter(lambda i,n=id: i['id'] != n, 
				                    self._objects))

    def objectIds(self):
        # Return a list of subobject ids
	return map(lambda i: i['id'], self._objects)

    def objectValues(self):
        # Return a list of the actual subobjects
	return map(lambda i,s=self: getattr(s,i['id']), self._objects)

    def objectItems(self):
        # Return a list of (id, subobject) tuples
	return map(lambda i,s=self: (i['id'], getattr(s,i['id'])),
		                    self._objects)
    def objectMap(self):
	# Return a tuple of mappings containing subobject meta-data
        return self._objects

    def manage_addObject(self,type,REQUEST):
	"""Add a subordinate object"""
	for t in self.meta_types:
	    if t['name']==type:
		return getattr(self,t['action'])(self,REQUEST)
	for t in self.dynamic_meta_types:
	    if t['name']==type:
		return getattr(self,t['action'])(self,REQUEST)
	raise 'BadRequest', 'Unknown object type: %s' % type

    def manage_delObjects(self,ids,REQUEST):
	"""Delete a subordinate object"""
	while ids:
	    try:    self._delObject(ids[-1])
	    except: raise 'BadRequest', ('%s does not exist' % ids[-1])
	    del ids[-1]
	return self.manage_main(self, REQUEST)

    def _setProperty(self,id,value,type='string'):
        self._checkId(id)
	self._properties=self._properties+({'id':id,'type':type},)
        setattr(self,id,value)

    def _delProperty(self,id):
        delattr(self,id)
        self._properties=tuple(filter(lambda i, n=id: i['id'] != n,
				     self._properties))

    def propertyIds(self):
        # Return a list of property ids
	return map(lambda i: i['id'], self._properties)

    def propertyValues(self):
        # Return a list of actual property objects
	return map(lambda i,s=self: getattr(s,i['id']), self._properties)

    def propertyItems(self):
        # Return a list of (id,property) tuples
	return map(lambda i,s=self: (i['id'],getattr(s,i['id'])), 
		                    self._properties)
    def propertyMap(self):
        # Return a tuple of mappings, giving meta-data for properties
        return self._properties

    def manage_addProperty(self,id,value,type,REQUEST):
	"""Add a new property (www)"""
	self._setProperty(id,value,type)
	return self.manage_propertiesForm(self,REQUEST)

    def manage_editProperties(self,REQUEST):
	"""Edit object properties"""
	for p in self._properties:
	    n=p['id']
	    try:    setattr(self,n,REQUEST[n])
	    except: setattr(self,n,'')
	return self.manage_propertiesForm(self,REQUEST)

    def manage_delProperties(self,ids,REQUEST):
	"""Delete one or more properties"""
	try:    p=map(lambda d: d['id'], self.__class__._properties)
	except: p=[]
	for n in ids:
	    if n in p:
	        return MessageDialog(
	        title  ='Cannot delete %s' % n,
	        message='The property <I>%s</I> cannot be deleted.' % n,
	        action =REQUEST['PARENT_URL']+'/manage_propertiesForm',
	        target ='manage_main')

	    try:    self._delProperty(n)
	    except: raise 'BadRequest', (
		          'The property <I>%s</I> does not exist' % n)

	return self.manage_propertiesForm(self,REQUEST)

    def _defaultInput(self,n,t,v):
        return '<INPUT NAME="%s:%s" SIZE="50" VALUE="%s"></TD>' % (n,t,v)

    def _stringInput(self,n,t,v):
        return ('<INPUT NAME="%s:%s" SIZE="50" VALUE="%s"></TD>'
		% (n,t,html_quote(v)))

    def _booleanInput(self,n,t,v):
	if v: v="CHECKET"
	else: v=''
        return ('<INPUT TYPE= "CHECKBOX" NAME="%s:%s" SIZE="50" %s></TD>'
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
	'<TEXTAREA NAME="%s:lines" ROWS="10" COLS="50">%s</TEXTAREA>'
	% (n,v))

    def _textInput(self,n,t,v):
        return ('<TEXTAREA NAME="%s" ROWS="10" COLS="50">%s</TEXTAREA>'
		% (n,html_quote(v)))

    _inputMap={
	'float': 	_defaultInput,
	'int':   	_defaultInput,
	'long':  	_defaultInput,
	'string':	_stringInput,
	'lines': 	_linesInput,
	'text':  	_textInput,
	'date':	 	_defaultInput,
	'regex':	_stringInput,
	'Regex':	_stringInput,
	'regexs':	_stringInput,
	'Regexs':	_stringInput,
	'tokens':	_stringInput,	
	'boolean':	_booleanInput,	
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
