"""Image object"""

__version__='$Revision: 1.29 $'[11:-2]

import Globals
from Globals import HTMLFile, MessageDialog
from AccessControl.Role import RoleManager
from SimpleItem import Item_w__name__
from Persistence import Persistent
from Acquisition import Implicit



class Pdata(Persistent, Implicit):
    # Wrapper for possibly large data
    def __init__(self, data):
	self.data=data

    def __str__(self):
	return self.data

    def __len__(self):
	return len(self.data)





class File(Persistent,Implicit,RoleManager,Item_w__name__):
    """ """
    meta_type='File'
    icon='p_/file'

    manage_editForm  =HTMLFile('imageEdit',globals(),Kind='File',kind='file')
    manage_uploadForm=HTMLFile('imageUpload',globals(),Kind='File',kind='file')
    manage=manage_main=manage_editForm

    manage_options=({'label':'Edit', 'action':'manage_main',
		     'target':'manage_main',
	            },
		    {'label':'Upload', 'action':'manage_uploadForm',
		     'target':'manage_main',
		    },
		    {'label':'View', 'action':'index_html',
		     'target':'manage_main',
		    },
		    {'label':'Security', 'action':'manage_access',
		     'target':'manage_main',
		    },
		   )

    __ac_permissions__=(
    ('View management screens', ['manage','manage_tabs','manage_uploadForm']),
    ('Change permissions', ['manage_access']),
    ('Change/upload data', ['manage_edit','manage_upload','PUT']),
    ('View', ['index_html',]),
    ('Shared permission', ['',]),
    )
   

    def __init__(self,id,title,file,content_type='application/octet-stream'):
	try:    headers=file.headers
	except: headers=None
	if headers is None:
	    if not content_type:
		raise 'BadValue', 'No content type specified'
	    self.content_type=content_type
	    self.data=Pdata(file)
	else:
	    if headers.has_key('content-type'):
		self.content_type=headers['content-type']
	    else:
		if not content_type:
		    raise 'BadValue', 'No content type specified'
		self.content_type=content_type
	    self.data=Pdata(file.read())
	self.__name__=id
	self.title=title
	self.size=len(self.data)

    def id(self): return self.__name__

    def index_html(self, RESPONSE):
	""" """
	RESPONSE['content-type']=self.content_type
        return self.data

    def manage_edit(self,title,content_type,REQUEST=None):
	""" """
	self.title=title
	self.content_type=content_type
	if REQUEST: return MessageDialog(
		    title  ='Success!',
		    message='Your changes have been saved',
		    action ='manage_main')

    def manage_upload(self,file='',REQUEST=None):
	""" """
	self.content_type=file.headers['content-type']
	data=file.read()
	self.data=Pdata(data)
	self.size=len(data)
	if REQUEST: return MessageDialog(
		    title  ='Success!',
		    message='Your changes have been saved',
		    action ='manage_main')

    PUT__roles__=['Manager']
    def PUT(self, BODY, REQUEST):
	'handle PUT requests'
	self.data=Pdata(BODY)
	self.size=len(BODY)
	try:
	    type=REQUEST['CONTENT_TYPE']
	    if type: self.content_type=type
	except KeyError: pass

    def size(self):    return len(self.data)
    def __str__(self): return str(self.data)
    def __len__(self): return 1




class Image(File):
    meta_type='Image'
    icon     ='p_/image'

    manage_editForm  =HTMLFile('imageEdit',globals(),Kind='Image',kind='image')
    manage_uploadForm=HTMLFile('imageUpload',globals(),Kind='Image',kind='image')
    manage=manage_main=manage_editForm

    PUT__roles__=['Manager']

    def __str__(self):
	return '<IMG SRC="%s" ALT="%s">' % (self.__name__, self.title_or_id()) 


class ImageHandler:
    """ """
    manage_addFileForm=HTMLFile('imageAdd', globals(),Kind='File',kind='file')
    manage_addImageForm=HTMLFile('imageAdd',globals(),Kind='Image',kind='image')

    def manage_addImage(self,id,file,title='',REQUEST=None):
	""" """
	self._setObject(id, Image(id,title,file))
	return self.manage_main(self,REQUEST)

    def manage_addFile(self,id,file,title='',REQUEST=None):
	""" """
	self._setObject(id, File(id,title,file))
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


Globals.default__class_init__(ImageHandler)

