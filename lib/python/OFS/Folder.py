
"""Folder object

$Id: Folder.py,v 1.51 1998/08/14 16:46:35 brian Exp $"""

__version__='$Revision: 1.51 $'[11:-2]


from Globals import HTMLFile
from ObjectManager import ObjectManager
from CopySupport import CopyContainer
from Image import Image, File
from Document import DocumentHandler
from AccessControl.Role import RoleManager
import SimpleItem
from string import rfind, lower
from content_types import content_type, find_binary, text_type
import Globals

manage_addFolderForm=HTMLFile('folderAdd', globals())

def manage_addFolder(self,id,title='',createPublic=0,createUserF=0,
			 REQUEST=None):
    """Add a new Folder object with id *id*.

    If the 'createPublic' and 'createUserF' parameters are set to any true
    value, an 'index_html' and a 'UserFolder' objects are created respectively
    in the new folder.
    """
    i=self.folderClass()()
    i.id=id
    i.title=title
    self._setObject(id,i)
    if createUserF:  i.manage_addUserFolder()
    if createPublic: i.manage_addDocument(id='index_html',title='')
    if REQUEST is not None: return self.manage_main(self,REQUEST,update_menu=1)

class Folder(ObjectManager,RoleManager,DocumentHandler,
	     SimpleItem.Item,CopyContainer):
    """
    The basic container object in Principia.  Folders can hold almost all
    other Principia objects.
    """
    meta_type='Folder'
    id       ='folder'
    title    ='Folder object'
    icon     ='p_/folder'

    _properties=({'id':'title', 'type': 'string'},)

    meta_types=()
    dynamic_meta_types=(
	# UserFolderHandler.meta_types_
	)

    manage_options=(
    {'label':'Contents', 'action':'manage_main',
     'target':'manage_main'},
    {'label':'Properties', 'action':'manage_propertiesForm',
     'target':'manage_main'},
    {'label':'Security', 'action':'manage_access',
     'target':'manage_main'},
    {'label':'Undo', 'action':'manage_UndoForm',
     'target':'manage_main'},
    {'label':'Find', 'action':'manage_findFrame',
     'target':'manage_main'},
    )

    __ac_permissions__=(
	('View', ()),
	('View management screens',
	 ('manage','manage_menu','manage_main','manage_copyright',
	  'manage_tabs','manage_propertiesForm','manage_UndoForm',
          'manage_cutObjects', 'manage_copyObjects', 'manage_pasteObjects',
          'manage_renameForm', 'manage_renameObject',
          'manage_findFrame', 'manage_findForm', 'manage_findAdv',
          'manage_findResult', 'manage_findOpt')),
	('Access contents information',
	 ('objectIds', 'objectValues', 'objectItems','hasProperty',
	  'propertyIds', 'propertyValues','propertyItems',''),
	 ('Anonymous', 'Manager'),
	 ),
	('Undo changes',       ('manage_undo_transactions',)),
	('Change permissions',
         ('manage_access','manage_changePermissions', 'manage_role',
          'manage_permission', 'manage_defined_roles',
          'manage_acquiredForm','manage_acquiredPermissions',
          'manage_permissionForm','manage_roleForm'
          )),
	('Delete objects',     ('manage_delObjects','manage_cutObject')),
	('Manage properties',
         ('manage_addProperty', 'manage_editProperties',
          'manage_delProperties', 'manage_changeProperties',)),
    )

    manage_addObject__roles__=None

    def tpValues(self):
	r=[]
	if hasattr(self.aq_base,'tree_ids'):
	    for id in self.aq_base.tree_ids:
		if hasattr(self, id): r.append(getattr(self, id))
	else:
	    for id in self._objects:
		o=getattr(self, id['id'])
		try:
		    if o.isPrincipiaFolderish: r.append(o)
#		    if subclass(o.__class__, Folder): r.append(o)
		except: pass

	return r

    def __getitem__(self, key):
	# Hm, getattr didn't work, maybe this is a put:
	if key[:19]=='manage_draftFolder-':
	    id=key[19:]
	    if hasattr(self, id): return getattr(self, id).manage_supervisor()
	    raise KeyError, key
	try:
	    if self.REQUEST['REQUEST_METHOD']=='PUT': return PUTer(self,key)
	except: pass
	raise KeyError, key

    def folderClass(self):
	return Folder
	return self.__class__

    test_url___allow_groups__=None
    def test_url_(self):
	"""Test connection"""
	return 'PING'


    # The Following methods are short-term measures to get Paul off my back;)
    def manage_exportHack(self, id=None):
	" "
	if id is None: o=self
	else: o=getattr(self.o)
	f=Globals.data_dir+'/export.bbe'
	o._p_jar.export_file(o,f)
	return f

    def manage_importHack(self, REQUEST=None):
	" "
	f=Globals.data_dir+'/export.bbe'
	o=self._p_jar.import_file(f)
        id=o.id
        if hasattr(id,'im_func'): id=id()
	self._setObject(id,o)
        return 'OK, I imported %s' % id

class PUTer:
    """ """
    def __init__(self, parent, key):
	self._parent=parent
	self._key=key
	self.__roles__=parent.PUT__roles__

    def PUT(self, REQUEST, BODY):
	""" """
	name=self._key
	try: type=REQUEST['CONTENT_TYPE']
	except KeyError: type=''
	if not type:
	    dot=rfind(name, '.')
	    suf=dot > 0 and lower(name[dot+1:]) or ''
	    if suf:
		try: type=content_type[suf]
		except KeyError:
		    if find_binary(BODY) >= 0: type='application/x-%s' % suf
		    else: type=text_type(BODY)
	    else:
		if find_binary(BODY) >= 0:
		    raise 'Bad Request', 'Could not determine file type'
		else: type=text_type(BODY)
	    __traceback_info__=suf, dot, name, type
	if lower(type)=='text/html':
	    return self._parent.manage_addDocument(name,'',BODY,
						   REQUEST=REQUEST)
	if lower(type)[:6]=='image/':
	    self._parent._setObject(name, Image(name, '', BODY, type))
	else:
	    self._parent._setObject(name, File(name, '', BODY, type))
	return 'OK'

    def __str__(self): return self._key






def subclass(c,super):
    if c is super: return 1
    try:
	for base in c.__bases__:
	    if subclass(base,super): return 1
    except: pass
    return 0


