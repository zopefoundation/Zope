
__doc__="""Object Manager

$Id: ObjectManager.py,v 1.1 1997/07/25 20:03:24 jim Exp $"""

__version__='$Revision: 1.1 $'[11:-2]


from SingleThreadedTransaction import Persistent
from Globals import ManageHTMLFile,PublicHTMLFile
from Globals import MessageDialog
from App.Management import Management
from Acquisition import Acquirer
from string import find,joinfields
from urllib import quote

class ObjectManager(Acquirer,Management,Persistent):
    """Generic object manager

    This class provides core behavior for collections of heterogeneous objects. 
    """

    meta_type  ='ObjectManager'
    meta_types = dynamic_meta_types = ()
    name       ='default'
    description=''
    icon       ='dir.jpg'
    _objects   =()
    _properties =({'name':'description', 'type': 'string'},)

    manage_main          =ManageHTMLFile('OFS/main')
    manage_propertiesForm=ManageHTMLFile('OFS/properties')

    manage_options=(
    {'icon':'OFS/templates.jpg', 'label':'Objects',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/properties.jpg', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'APP/help.jpg', 'label':'Help',
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

    def _checkName(self,name):
	if quote(name) != name: raise 'Bad Request', (
	    """The name <em>%s<em>  is invalid - it
	       contains characters illegal in URLs.""" % name)

	if name[:1]=='_': raise 'Bad Request', (
	    """The name <em>%s<em>  is invalid - it 
               begins with an underscore character, _.""" % name)

	if hasattr(self,name): raise 'Bad Request', (
	    """The name <em>%s<em>  is invalid - it
               is already in use.""" % name)

    def parentObject(self):
	try:
	    if self.aq_parent.isAnObjectManager:
		return (self.aq_parent,)
	except: pass
        return ()
        #try:    return (self.aq_parent,)
	#except: return ()

    def _setObject(self,name,object):
	self._checkName(name)
	setattr(self,name,object)
	try:    t=object.meta_type
	except: t=None
	self._objects=self._objects+({'name':name,'meta_type':t},)

    def _delObject(self,name):
        delattr(self,name)
        self._objects=tuple(filter(lambda i,n=name: i['name'] != n, 
				                    self._objects))

    def objectNames(self):
        # Return a list of subobject names
	return map(lambda i: i['name'], self._objects)

    def objectValues(self):
        # Return a list of the actual subobjects
	return map(lambda i,s=self: getattr(s,i['name']), self._objects)

    def objectItems(self):
        # Return a list of (name, subobject) tuples
	return map(lambda i,s=self: (i['name'], getattr(s,i['name'])),
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

    def manage_delObjects(self,names,REQUEST):
	"""Delete a subordinate object"""
	while names:
	    try:    self._delObject(names[-1])
	    except: raise 'BadRequest', ('%s does not exist' % names[-1])
	    del names[-1]
	return MessageDialog(
	       title  ='Items Removed',
	       message='The items were removed successfully',
	       action =REQUEST['PARENT_URL']+'/manage_main',
	       target ='manage_main')

    def _setProperty(self,name,value,type='string'):
        self._checkName(name)
	self._properties=self._properties+({'name':name,'type':type},)
        setattr(self,name,value)

    def _delProperty(self,name):
        delattr(self,name)
        self._properties=tuple(filter(lambda i, n=name: i['name'] != n,
				     self._properties))

    def propertyNames(self):
        # Return a list of property names
	return map(lambda i: i['name'], self._properties)

    def propertyValues(self):
        # Return a list of actual property objects
	return map(lambda i,s=self: getattr(s,i['name']), self._properties)

    def propertyItems(self):
        # Return a list of (name,property) tuples
	return map(lambda i,s=self: (i['name'],getattr(s,i['name'])), 
		                    self._properties)
    def propertyMap(self):
        # Return a tuple of mappings, giving meta-data for properties
        return self._properties

    def manage_addProperty(self,name,value,type,REQUEST):
	"""Add a new property (www)"""
	self._setProperty(name,value,type)
	return MessageDialog(
	       title='Property Added',
	       message='The property was added successfully',
	       action=REQUEST['PARENT_URL']+'/manage_propertiesForm',
	       target='manage_main')

    def manage_editProperties(self,REQUEST):
	"""Edit object properties"""
	for p in self._properties:
	    n=p['name']
	    try:    setattr(self,n,REQUEST[n])
	    except: pass
	return MessageDialog(
	       title  ='Properties changed',
	       message='Properties were changed successfully',
	       action =REQUEST['PARENT_URL']+'/manage_propertiesForm',
	       target ='manage_main')

    def manage_delProperties(self,names,REQUEST):
	"""Delete one or more properties"""
	try:    p=map(lambda d: d['name'], self.__class__._properties)
	except: p=[]
	for n in names:
	    if n in p:
	        return MessageDialog(
	        title  ='Cannot delete %s' % n,
	        message='The property <I>%s</I> cannot be deleted.' % n,
	        action =REQUEST['PARENT_URL']+'/manage_propertiesForm',
	        target ='manage_main')

	    try:    self._delProperty(n)
	    except: raise 'BadRequest', (
		          'The property <I>%s</I> does not exist' % n)

	return MessageDialog(
	       title  ='Properties Removed',
	       message='The properties were removed successfully',
	       action =REQUEST['PARENT_URL']+'/manage_propertiesForm',
	       target ='manage_main')

    def _defaultInput(self,n,t,v):
        return '<INPUT NAME="%s:%s" SIZE="50" VALUE="%s"></TD>' % (n,t,v)

    def _selectInput(self,n,t,v):
        s=['<SELECT NAME="%s:%s">' % (n,t)]
	map(lambda i: s.append('<OPTION>%s' % i), v)
        s.append('</SELECT>')
        return joinfields(s,'\n')

    def _linesInput(self,n,t,v):
        return (
	'<TEXTAREA NAME="%s:lines" ROWS="10" COLS="50">%s</TEXTAREA>' % (n,v))

    def _textInput(self,n,t,v):
        return '<TEXTAREA NAME="%s" ROWS="10" COLS="50">%s</TEXTAREA>' % (n,v)

    _inputMap={'float': _defaultInput,
	       'int':   _defaultInput,
	       'long':  _defaultInput,
	       'string':_defaultInput,
               'lines': _linesInput,
	       'text':  _textInput,
               }

    propertyTypes=_inputMap.keys()

    def propertyInputs(self):
	imap=self._inputMap
        r=[]
	for p in self._properties:
	    n=p['name']
	    t=p['type']
	    v=getattr(self,n)
	    r.append({'name': n, 'input': imap[t](None,n,t,v)})
	return r

##############################################################################
#
# $Log: ObjectManager.py,v $
# Revision 1.1  1997/07/25 20:03:24  jim
# initial
#
# Revision 1.1  1997/07/07 16:02:18  jim
# *** empty log message ***
#
#
