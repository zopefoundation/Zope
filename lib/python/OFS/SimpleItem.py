#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################## 

'''This module implements a simple item mix-in for objects that have a
very simple (e.g. one-screen) management interface, like documents,
Aqueduct database adapters, etc.

This module can also be used as a simple template for implementing new
item types. 

$Id: SimpleItem.py,v 1.2 1997/10/30 19:51:09 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]


class Item:

    # Name, relative to SOFTWARE_URL of icon used to display item
    # in folder listings.
    icon='App/arrow.jpg'

    # Meta type used for selecting all objects of a given type.
    meta_type='simple item'

    # Default title.  
    title=''

    # Empty manage_options signals that this object has a
    # single-screen management interface.
    manage_options=()

    # Utility that returns the title if it is not blank and the id
    # otherwise.
    def title_or_id(self):
	return self.title or self.id

    # Utility that returns the title if it is not blank and the id
    # otherwise.  If the title is not blank, then the id is included
    # in parens.
    def title_and_id(self):
	t=self.title
	return t and ("%s (%s)" % (t,self.id)) or self.id

    
    # Handy way to talk to ourselves in document templates.
    def this(self):
	return self

    # Interact with tree tag
    def tpURL(self):
	url=self.id
	if hasattr(url,'im_func'): url=url()
	return url

    def tpValues(self): return ()

class Item_w__name__(Item):

    # Utility that returns the title if it is not blank and the id
    # otherwise.
    def title_or_id(self):
	return self.title or self.__name__

    # Utility that returns the title if it is not blank and the id
    # otherwise.  If the title is not blank, then the id is included
    # in parens.
    def title_and_id(self):
	t=self.title
	return t and ("%s (%s)" % (t,self.__name__)) or self.__name__

############################################################################## 
#
# $Log: SimpleItem.py,v $
# Revision 1.2  1997/10/30 19:51:09  jim
# Added methods to support tree browsing.
#
# Revision 1.1  1997/09/10 18:42:36  jim
# Added SimpleItem mix-in and new title/id methods.
#
#
