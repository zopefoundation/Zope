
"""Folder object

$Id: Folder.py,v 1.1 1997/07/25 20:03:23 jim Exp $"""

__version__='$Revision: 1.1 $'[11:-2]


from Globals import HTMLFile
from ObjectManager import ObjectManager
from Image import Image, ImageHandler
from Document import Document, DocumentHandler

class FolderHandler:
    """Folder object handler"""

    meta_types=({'name':'Folder', 'action':'manage_addFolderForm'},)

    manage_addFolderForm=HTMLFile('OFS/folderAdd')

    def folderClass(self):
	return Folder
	return self.__class__

    def manage_addFolder(self,name,description,REQUEST):
	"""Add a new Folder object"""
	i=self.folderClass()()
	i.name=name
	i.description=description
	self._setObject(name,i)
	return self.manage_main(self,REQUEST)

    def folderNames(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Folder': t.append(i['name'])
	return t

    def folderValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Folder': t.append(getattr(self,i['name']))
	return t

    def folderItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Folder':
		n=i['name']
		t.append((n,getattr(self,n)))
	return t


class Folder(ObjectManager,DocumentHandler,ImageHandler,FolderHandler):
    """Folder object"""
    meta_type  ='Folder'
    name       ='folder'
    description='Folder object'
    icon       ='OFS/folder.jpg'

    _properties=({'name':'description', 'type': 'string'},)

    index_html=HTMLFile('OFS/folderIndex_html')
    meta_types=(
	DocumentHandler.meta_types+
	ImageHandler.meta_types+
	FolderHandler.meta_types
	)

    manage_options=(
    {'icon':icon, 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/properties.jpg', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'App/help.jpg', 'label':'Help',
     'action':'manage_help',   'target':'_new'},
    )









