##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__doc__='''Objects that implement Permission-based roles.


$Id: PermissionRole.py,v 1.9 2000/12/05 18:49:42 shane Exp $'''
__version__='$Revision: 1.9 $'[11:-2]

import sys

from ExtensionClass import Base

import string

name_trans=filter(lambda c, an=string.letters+string.digits+'_': c not in an,
                  map(chr,range(256)))
name_trans=string.maketrans(string.join(name_trans,''), '_'*len(name_trans))

def rolesForPermissionOn(perm, object, default=('Manager',)):
    """Return the roles that have the given permission on the given object
    """
    im=imPermissionRole()
    im._p='_'+string.translate(perm, name_trans)+"_Permission"
    im._d=default
    return im.__of__(object)
    

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

    def __of__(self, parent, None=None, getattr=getattr):
        r=imPermissionRole()
        r._p=self._p
        r._pa=parent
        r._d=self._d
        p=getattr(parent, 'aq_inner', None)
        if p is not None:
            return r.__of__(p)
        else:
            return r


# This is used when a permission maps explicitly to no permission.
_what_not_even_god_should_do=[]

class imPermissionRole(Base):
    """Implement permission-based roles
    """
    
    def __of__(self, parent,tt=type(()),st=type(''),getattr=getattr,None=None):
        obj=parent
        n=self._p
        r=None
        while 1:
            if hasattr(obj,n):
                roles=getattr(obj, n)
                
                if roles is None: return 'Anonymous',
                
                t=type(roles)

                if t is tt:
                    # If we get a tuple, then we don't acquire
                    if r is None: return roles
                    return r+list(roles)

                if t is st:
                    # We found roles set to a name.  Start over
                    # with the new permission name.  If the permission
                    # name is '', then treat as private!
                    if roles:
                        if roles != n:
                            n=roles
                        # If we find a name that is the same as the
                        # current name, we just ignore it.
                        roles=None
                    else:
                        return _what_not_even_god_should_do

                elif roles:
                    if r is None: r=list(roles)
                    else: r=r+list(roles)

            obj=getattr(obj, 'aq_inner', None)
            if obj is None: break
            obj=obj.aq_parent

        if r is None: r=self._d
            
        return r
            
    # The following methods are needed in the unlikely case that an unwrapped
    # object is accessed:
    def __getitem__(self, i):
        try:
            v=self._v
        except: 
            v=self._v=self.__of__(self._pa)
            del self._pa
            
        return v[i]
        
    def __len__(self):
        try:
            v=self._v
        except: 
            v=self._v=self.__of__(self._pa)
            del self._pa

        return len(v)

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
