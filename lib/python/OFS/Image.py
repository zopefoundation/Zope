"""Image object"""

__version__='$Revision: 1.20 $'[11:-2]

from Persistence import Persistent
from Globals import HTMLFile
from Globals import MessageDialog
from AccessControl.Role import RoleManager
import SimpleItem
import Acquisition

class File(Persistent,RoleManager,SimpleItem.Item_w__name__,
	   Acquisition.Implicit):
    """Image object"""
    meta_type='File'
    icon='p_/file'

    manage_editForm   =HTMLFile('imageEdit', globals(), Kind='File', kind='file')
    manage_uploadForm =HTMLFile('imageUpload', globals(), Kind='File', kind='file')
    manage=manage_main=manage_editForm

    manage_options=({'icon':'', 'label':'Edit',
		     'action':'manage_main', 'target':'manage_main',
	            },
		    {'icon':'', 'label':'Upload',
		     'action':'manage_uploadForm', 'target':'manage_main',
		    },
		    {'icon':'', 'label':'View',
		     'action':'index_html', 'target':'manage_main',
		    },
		    {'icon':'', 'label':'Security',
		     'action':'manage_access', 'target':'manage_main',
		    },
		    {'icon':'', 'label':'Undo',
		     'action':'manage_UndoForm', 'target':'manage_main',
		    },
		   )

    __ac_permissions__=(
    ('View management screens', ['manage','manage_tabs','manage_uploadForm']),
    ('Change permissions', ['manage_access']),
    ('Change/upload data', ['manage_edit','manage_upload','PUT']),
    ('View', ['index_html',]),
    )
   
    __ac_types__=(('Full Access', map(lambda x: x[0], __ac_permissions__)),
		  ('View Access', ['View',]),
		 )

    def manage_edit(self,title,content_type,REQUEST=None):
	""" """
	self.title=title
	self.content_type=content_type
	if REQUEST: return self.manage_editedDialog(REQUEST)

    def manage_upload(self,file='', REQUEST=None):
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

    def __str__(self): return self.data

    def __len__(self):
	# This is bogus and needed because of the way Python tests truth.
	return 1 

    def PUT(self, BODY, REQUEST):
	'handle PUT requests'
	self.data=BODY
	try:
	    type=REQUEST['CONTENT_TYPE']
	    if type: self.content_type=type
	except KeyError: pass


class Image(File):

    meta_type='Image'
    icon='p_/image'

    manage_editForm   =HTMLFile('imageEdit', globals(), Kind='Image', kind='image')
    manage_uploadForm =HTMLFile('imageUpload', globals(), Kind='Image', kind='image')
    manage=manage_main=manage_editForm

    def __str__(self):
	return '<IMG SRC="%s" ALT="%s">' % (self.__name__, self.title_or_id()) 


class ImageHandler:
    """Image object handler mixin"""
    #meta_types=({'name':'Image', 'action':'manage_addImageForm'},)

    manage_addFileForm=HTMLFile('imageAdd', globals(),  Kind='File', kind='file')
    manage_addImageForm=HTMLFile('imageAdd', globals(), Kind='Image', kind='image')

    def manage_addImage(self,id,file,title='',REQUEST=None):
	"""Add a new Image object"""
	i=Image()
	i._init(id,file)
	i.title=title
	self._setObject(id,i)
	return self.manage_main(self,REQUEST)

    def manage_addFile(self,id,file,title='',REQUEST=None):
	"""Add a new Image object"""
	i=File()
	i._init(id,file)
	i.title=title
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

    def fileIds(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='File': t.append(i['id'])
	return t

    def fileValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='File': t.append(getattr(self,i['id']))
	return t

    def fileItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='File':
		n=i['id']
		t.append((n,getattr(self,n)))
	return t
