
"""Folder object

$Id: Folder.py,v 1.15 1997/11/07 16:12:29 jim Exp $"""

__version__='$Revision: 1.15 $'[11:-2]


from Globals import HTMLFile
from ObjectManager import ObjectManager
from Image import ImageHandler
from Document import DocumentHandler
from AccessControl.User import UserFolderHandler
from AccessControl.Role import RoleManager
import SimpleItem

class FolderHandler:
    """Folder object handler"""

    # meta_types=({'name':'Folder', 'action':'manage_addFolderForm'},)

    manage_addFolderForm=HTMLFile('OFS/folderAdd')

    def folderClass(self):
	return Folder
	return self.__class__

    def manage_addFolder(self,id,title='',acl_type='A',acl_roles=[],
			 REQUEST=None):
	"""Add a new Folder object"""
	i=self.folderClass()()
	i.id=id
	i.title=title
	i._setRoles(acl_type,acl_roles)
	self._setObject(id,i)
	return self.manage_main(self,REQUEST)

    def folderIds(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Folder': t.append(i['id'])
	return t

    def folderValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Folder': t.append(getattr(self,i['id']))
	return t

    def folderItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Folder':
		n=i['id']
		t.append((n,getattr(self,n)))
	return t

    test_url___allow_groups__=None
    def test_url_(self):
	'''Method for testing server connection information
	when configuring aqueduct clients'''
	return 'PING'


class Folder(ObjectManager,RoleManager,DocumentHandler,
	     ImageHandler,FolderHandler,UserFolderHandler,
	     SimpleItem.Item):
    """Folder object"""
    meta_type='Folder'
    id       ='folder'
    title    ='Folder object'
    icon     ='OFS/Folder_icon.gif'

    _properties=({'id':'title', 'type': 'string'},)

    meta_types=()
    dynamic_meta_types=(
	UserFolderHandler.meta_types_
	)

    manage_options=(
    {'icon':icon, 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'AccessControl/AccessControl_icon.gif', 'label':'Access Control',
     'action':'manage_rolesForm',   'target':'manage_main'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm',   'target':'manage_main'},
#    {'icon':'OFS/Help_icon.gif', 'label':'Help',
#     'action':'manage_help',   'target':'_new'},
    )

    def tpValues(self):
	r=[]
	if hasattr(self.aq_self,'tree_ids'):
	    for id in self.aq_self.tree_ids:
		if hasattr(self, id): r.append(getattr(self, id))
	else:
	    for id in self._objects:
		o=getattr(self, id['id'])
		try:
		    if subclass(o.__class__, Folder): r.append(o)
		except: pass

	return r
		    


def subclass(c,super):
    if c is super: return 1
    try:
	for base in c.__bases__:
	    if subclass(base,super): return 1
    except: pass
    return 0
