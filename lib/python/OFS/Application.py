#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  
#
############################################################################## 
__doc__='''Application support


$Id: Application.py,v 1.4 1997/08/08 15:51:27 jim Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

import Folder, regex, string
import Globals

class Application(Folder.Folder):

    id='Your Place'
    __roles__=None
    title=''
    web__form__method='GET'
    manage_options=Folder.Folder.manage_options+(
	{'icon':'App/arrow.jpg', 'label':'Application Management',
	 'action':'app/manage',   'target':'_top'},
	)
    def folderClass(self): return Folder.Folder

    def __class_init__(self): pass

def open_bobobase():
    # Open the application database
    Bobobase=Globals.Bobobase=Globals.PickleDictionary(Globals.BobobaseName)
    
    if not Bobobase.has_key('products'):
	import initial_products
	initial_products.install(Bobobase)
	get_transaction().commit()
    
    products=Bobobase['products']
    
    install_products(products)

    return Bobobase

def install_products(products):
    # Install a list of products into the basic folder class, so
    # that all folders know about top-level objects, aka products

    meta_types=list(Folder.Folder.dynamic_meta_types)

    for product in products:
	product=__import__(product)
	for meta_type in product.meta_types:
	    meta_types.append(meta_type)
	    name=meta_type['name']

	    if (not meta_type.has_key('prefix') and 
		not regex.match('[^a-zA-Z0-9_]', name)):
	        meta_type['prefix']=string.lower(name)

	    if meta_type.has_key('prefix'):
		prefix=meta_type['prefix']

		def productNames(self, name=name):
		    t=[]
		    for i in self.objectMap():
			if i['meta_type']==name: t.append(i['name'])
		    return t

		setattr(Folder.Folder, "%sNames" % prefix , productNames)

		def productValues(self, name=name):
		    t=[]
		    for i in self.objectMap():
			if i['meta_type']==name:
			    t.append(getattr(self,i['name']))
		    return t

		setattr(Folder.Folder, "%sValues" % prefix , productValues)

		def productItems(self, name=name):
		    t=[]
		    for i in self.objectMap():
			if i['meta_type']=='Image':
			    n=i['name']
			    t.append((n,getattr(self,n)))
		    return t

		setattr(Folder.Folder, "%sItems" % prefix , productItems)

	for name,method in product.methods.items():
	    setattr(Folder.Folder, name, method)

    Folder.Folder.dynamic_meta_types=tuple(meta_types)
    

############################################################################## 
# Test functions:
#

def main():
    # The "main" program for this module
    import sys
    print sys.argv[0]+" is a pure module and doesn't do anything by itself."


if __name__ == "__main__": main()

############################################################################## 
#
# $Log: Application.py,v $
# Revision 1.4  1997/08/08 15:51:27  jim
# Added access control support
#
# Revision 1.3  1997/08/06 18:26:12  jim
# Renamed description->title and name->id and other changes
#
# Revision 1.2  1997/07/28 21:33:08  jim
# Changed top name.
#
# Revision 1.1  1997/07/25 20:03:22  jim
# initial
#
#
