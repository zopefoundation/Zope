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
__doc__='''Objects that implement Permission-based roles.


$Id: PermissionRole.py,v 1.1 1998/05/08 14:45:20 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import sys

from ExtensionClass import Base

import string

name_trans=filter(lambda c, an=string.letters+string.digits+'_': c not in an,
		  map(chr,range(256)))
name_trans=string.maketrans(string.join(name_trans,''), '_'*len(name_trans))

class PermissionRole(Base):
    """Implement permission-based roles.

    Under normal circumstances, our __of__ method will be
    called with an unwrapped object.  The result will then be called
    with a wrapped object, if the original object was wrapped.
    To deal with this, we have to create an intermediate object.
    
    """

    def __init__(self, name, default=('Manager',)):
	self.__name__=name
	self._p='_'+string.translate(name,name_trans)+"_Permission"
	self._d=default

    def __of__(self, parent):
	r=imPermissionRole()
	n=r._p=self._p
	if hasattr(parent, n): r._d=getattr(parent,n)
	else: r._d=self._d
	return r

class imPermissionRole(Base):
    """Implement permission-based roles
    """
    
    def __of__(self, parent):
	obj=parent
	n=self._p
	r=None
	while 1:
	    if hasattr(obj,n):
		roles=getattr(obj, n)
                if roles is None: return 'Anonymous',
		if type(roles) is type(()):
		    if r is None: return roles
		    return r+list(roles)
		if r is None: r=list(roles)
		else: r=r+list(roles)
	    if hasattr(obj,'aq_parent'):
		obj=obj.aq_parent
	    else:
		break

	if r is None: r=self._d
	    
	return r
	    
    # The following methods are needed in the unlikely case that an unwrapped
    # object is accessed:
    def __getitem__(self, i): return self._d[i]
    def __len__(self): return len(self._d)


############################################################################## 
# Test functions:
#

def main():
    # The "main" program for this module

    import sys
    sys.path.append('/projects/_/ExtensionClass')

    from Acquisition import Implicit
    class I(Implicit):
	x__roles__=PermissionRole('x')
	y__roles__=PermissionRole('y')
	z__roles__=PermissionRole('z')
	def x(self): pass
	def y(self): pass
	def z(self): pass



    a=I()
    a.b=I()
    a.b.c=I()
    a.q=I()
    a.q._x_Permission=('foo',)
    a._y_Permission=('bar',)
    a._z_Permission=('zee',)
    a.b.c._y_Permission=('Manage',)
    a.b._z_Permission=['also']
    
    print a.x.__roles__, list(a.x.__roles__)
    print a.b.x.__roles__
    print a.b.c.x.__roles__
    print a.q.x.__roles__
    print a.b.q.x.__roles__
    print a.b.c.q.x.__roles__
    print
    
    print a.y.__roles__, list(a.y.__roles__)
    print a.b.y.__roles__
    print a.b.c.y.__roles__
    print a.q.y.__roles__
    print a.b.q.y.__roles__
    print a.b.c.q.y.__roles__
    print
    
    print a.z.__roles__, list(a.z.__roles__)
    print a.b.z.__roles__
    print a.b.c.z.__roles__
    print a.q.z.__roles__
    print a.b.q.z.__roles__
    print a.b.c.q.z.__roles__
    print

if __name__ == "__main__": main()

############################################################################## 
#
# $Log: PermissionRole.py,v $
# Revision 1.1  1998/05/08 14:45:20  jim
# new permission machinery
#
#
