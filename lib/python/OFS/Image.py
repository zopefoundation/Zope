"""Image object"""

__version__='$Revision: 1.4 $'[11:-2]

from Persistence import Persistent
from Globals import HTMLFile
from AccessControl.Role import RoleManager

class Image(Persistent,RoleManager):
    """Image object"""
    meta_type='Image'
    title    =''
    icon     ='OFS/Image_icon.gif'

    manage_editForm   =HTMLFile('OFS/imageEdit')
    manage=manage_main=manage_editForm

    manage_options=()

    def manage_edit(self,file,title,content_type='',acl_type='A',acl_roles=[]):
	""" """
	try:    headers=file.headers
	except: headers=None

	if headers is None and file:
	    if not content_type: raise 'BadValue', (
		                       'No content type specified')
	    self.content_type=content_type
	    self.data=file
	elif file:
	    data=file.read()
	    self.content_type=headers['content-type']
	    self.data=data
	self.title=title
	self._setRoles(acl_type,acl_roles)

    def _init(self,id,file,content_type=''):
	try:    headers=file.headers
	except: headers=None
	if headers is None:
	    if not content_type: raise 'BadValue', (
		                       'No content type specified')
	    self.content_type=content_type
	    self.data=file
	else:
	    self.content_type=headers['content-type']
	    self.data=file.read()
	self.__name__=id

    def id(self): return self.__name__

    def index_html(self, RESPONSE):
	"""Default document"""
	RESPONSE['content-type']=self.content_type
        return self.data



class ImageHandler:
    """Image object handler mixin"""
    meta_types=({'name':'Image', 'action':'manage_addImageForm'},)

    manage_addImageForm=HTMLFile('OFS/imageAdd')

    def manage_addImage(self,id,file,title,REQUEST,acl_type='A',acl_roles=[]):
	"""Add a new Image object"""
	i=Image()
	i._init(id,file)
	i.title=title
	i._setRoles(acl_type,acl_roles)
	self._setObject(id,i)
	return self.manage_main(self,REQUEST)

    def imageIds(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Image': t.append(i['id'])
	return t

    def imageValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Image': t.append(getattr(self,i['id']))
	return t

    def imageItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Image':
		n=i['id']
		t.append((n,getattr(self,n)))
	return t
