"""Image object that is stored in a file"""

__version__='$Revision: 1.5 $'[11:-2]

from string import rfind
from Globals import package_home
from DateTime import DateTime
import Acquisition

class ImageFile(Acquisition.Explicit):
    """Image object stored in an external file"""

    def __init__(self,path,_prefix=None):
	if _prefix is None: _prefix=SOFTWARE_HOME+'/lib/python'
	elif type(_prefix) is not type(''): _prefix=package_home(_prefix)
	path='%s/%s' % (_prefix, path)

	self.path=path
	self.content_type='image/%s' % path[rfind(path,'.')+1:]
	self.__name__=path[rfind(path,'/')+1:]


    def index_html(self, RESPONSE):
	"""Default document"""
	RESPONSE['content-type']=self.content_type
	f=open(self.path,'rb')
	data=f.read()
	f.close()
        return data

    HEAD__roles__=None
    def HEAD(self, REQUEST, RESPONSE):
	""" """
	RESPONSE['content-type'] =self.content_type
	return ''

    def __len__(self):
	# This is bogus and needed because of the way Python tests truth.
	return 1 

    def __str__(self):
	return '<IMG SRC="%s" ALT="%s">' % (self.__name__, self.title_or_id()) 







