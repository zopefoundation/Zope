#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1998 Digital Creations, Inc., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''short description


$Id: Permission.py,v 1.2 1998/05/11 14:58:28 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

from Globals import HTMLFile, MessageDialog
from string import join, strip, split, find
from Acquisition import Implicit
import Globals, string

ListType=type([])


name_trans=filter(lambda c, an=string.letters+string.digits+'_': c not in an,
		  map(chr,range(256)))
name_trans=string.maketrans(string.join(name_trans,''), '_'*len(name_trans))


class Permission:
    # A Permission maps a named logical permission to a set
    # of attribute names. Attribute names which appear in a
    # permission may not appear in any other permission defined
    # by the object.

    def __init__(self,name,data,obj):
	self.name=name
	self._p='_'+string.translate(name,name_trans)+"_Permission"
	self.data=data
	if hasattr(obj, 'aq_base'): obj=obj.aq_base
	self.obj=obj

    def getRoles(self):
	# Return the list of role names which have been given
	# this permission for the object in question. To do
	# this, we try to get __roles__ from all of the object
	# attributes that this permission represents.
	obj=self.obj
	name=self._p
	if hasattr(obj, name): return getattr(obj, name)
	roles=[]
	for name in self.data:
	    if name:
		if hasattr(obj, name):
		    attr=getattr(obj, name)
		    if hasattr(attr,'im_self'):
			attr=attr.im_self
			if hasattr(attr, '__dict__'):
			    attr=attr.__dict__
			    name=name+'__roles__'
			    if attr.has_key(name):
				roles=attr[name]
				break
	    elif hasattr(obj, '__dict__'):
		attr=obj.__dict__
		if attr.has_key('__roles__'):
		    roles=attr['__roles__']
		    break

	if roles:
	    try:
		if 'Shared' not in roles: return tuple(roles)
		roles=list(roles)
		roles.remove('Shared')
		return roles
	    except: return []

	if roles is None: return ['Manager','Anonymous']
				
	return roles

    def setRoles(self, roles):
	obj=self.obj

	if type(roles) is ListType and not roles:
	    if hasattr(obj, self._p): delattr(obj, self._p)
	else:
	    setattr(obj, self._p, roles)
	
	for name in self.data:
	    if name=='': attr=obj
	    else: attr=getattr(obj, name)
	    try: del attr.__roles__
	    except: pass
	    try: delattr(obj,name+'__roles__')
	    except: pass

    def setRole(self, role, present):
	roles=self.getRoles()
	if role in roles:
	    if present: return
	    if type(roles) is ListType: roles.remove(role)
	    else:
		roles=list(roles)
		roles.remove(role)
		roles=tuple(roles)
	elif not present: return
	else:
	    if type(roles) is ListType: roles.append(role)
	    else: roles=roles+(role,)
	self.setRoles(roles)
		
    def __len__(self): return 1
    def __str__(self): return self.name


############################################################################## 
#
# $Log: Permission.py,v $
# Revision 1.2  1998/05/11 14:58:28  jim
# Added some machinery to fix bugs in reseting old permission settings.
#
# Revision 1.1  1998/05/08 14:45:20  jim
# new permission machinery
#
#
