"""Image object"""

__version__='$Revision: 1.11 $'[11:-2]

from Persistence import Persistent
from Globals import HTMLFile
from Globals import MessageDialog
from AccessControl.Role import RoleManager
import SimpleItem
import Acquisition

class Image(Persistent,RoleManager,SimpleItem.Item_w__name__,
	    Acquisition.Implicit):
    """Image object"""
    meta_type='Image'
    icon     ='OFS/Image_icon.gif'

    manage_editForm   =HTMLFile('OFS/imageEdit')
    manage=manage_main=manage_editForm

    def manage_edit(self,title,content_type,
		    acl_type='A',acl_roles=[], REQUEST=None):
	""" """
	self.title=title
	self.content_type=content_type
	self.title=title
	self._setRoles(acl_type,acl_roles)
	if REQUEST: return self.manage_editedDialog(REQUEST)

    def manage_editData(self,file='', REQUEST=None):
	"""Change image data"""
	headers=file.headers
	data=file.read()
	content_type=headers['content-type']
	self.data=data
	self.content_type=content_type
	if REQUEST: return self.manage_editedDialog(REQUEST)

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

    def __str__(self):
	return '<IMG SRC="%s" ALT="%s">' % (self.__name__, self.title_or_id()) 

    def __len__(self):
	# This is bogus and needed because of the way Python tests truth.
	return 1 

    PUT__roles__='manage',
    def PUT(self, BODY, REQUEST):
	'handle PUT requests'
	self.data=BODY
	try:
	    type=REQUEST['CONTENT_TYPE']
	    if type: self.content_type=type
	except KeyError: pass


class ImageHandler:
    """Image object handler mixin"""
    #meta_types=({'name':'Image', 'action':'manage_addImageForm'},)

    manage_addImageForm=HTMLFile('OFS/imageAdd')

    def manage_addImage(self,id,file,title='',acl_type='A',acl_roles=[],
			REQUEST=None):
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
