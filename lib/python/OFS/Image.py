"""Image object"""

__version__='$Revision: 1.1 $'[11:-2]


from Globals import HTMLFile


class Image:
    """Image object"""
    meta_type  ='Image'
    description=''
    icon       ='OFS/image.jpg'

    manage_editForm=HTMLFile('OFS/imageEdit')

    def manage_edit(self,file,description,content_type=''):
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
	self.description=description
	

    def _init(self,name,file,content_type=''):
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
	self.__name__=name

    def name(self): return self.__name__

    def index_html(self, RESPONSE):
	"""Default document"""
	RESPONSE['content-type']=self.content_type
        return self.data





class ImageHandler:
    """Image object handler mixin"""
    meta_types=({'name':'Image', 'action':'manage_addImageForm'},)

    manage_addImageForm=HTMLFile('OFS/imageAdd')

    def manage_addImage(self,name,file,description,REQUEST):
	"""Add a new Image object"""
	i=Image()
	i._init(name,file)
	i.description=description
	self._setObject(name,i)
	return self.manage_main(self,REQUEST)

    def imageNames(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Image': t.append(i['name'])
	return t

    def imageValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Image': t.append(getattr(self,i['name']))
	return t

    def imageItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='Image':
		n=i['name']
		t.append((n,getattr(self,n)))
	return t
