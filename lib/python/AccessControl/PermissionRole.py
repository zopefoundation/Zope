##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
__doc__='''Objects that implement Permission-based roles.


$Id: PermissionRole.py,v 1.2 1998/12/04 20:15:25 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

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
