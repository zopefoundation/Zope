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
__doc__='''short description


$Id: Permission.py,v 1.7 2000/07/26 18:18:34 jim Exp $'''
__version__='$Revision: 1.7 $'[11:-2]

import string, Products, Globals

ListType=type([])

name_trans=filter(lambda c, an=string.letters+string.digits+'_': c not in an,
                  map(chr,range(256)))
name_trans=string.maketrans(string.join(name_trans,''), '_'*len(name_trans))

def pname(name, translate=string.translate, name_trans=name_trans):
    return '_'+translate(name,name_trans)+"_Permission"

_marker=[]
class Permission:
    # A Permission maps a named logical permission to a set
    # of attribute names. Attribute names which appear in a
    # permission may not appear in any other permission defined
    # by the object.

    def __init__(self,name,data,obj,default=None):
        self.name=name
        self._p='_'+string.translate(name,name_trans)+"_Permission"
        self.data=data
        if hasattr(obj, 'aq_base'): obj=obj.aq_base
        self.obj=obj
        self.default=default

    def getRoles(self, default=_marker):
        # Return the list of role names which have been given
        # this permission for the object in question. To do
        # this, we try to get __roles__ from all of the object
        # attributes that this permission represents.
        obj=self.obj
        name=self._p
        if hasattr(obj, name): return getattr(obj, name)
        roles=default
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
        if roles is _marker: return ['Manager']
                                
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


_registeredPermissions={}
_registerdPermission=_registeredPermissions.has_key

def registerPermissions(permissions, defaultDefault=('Manager',)):
    """Register an __ac_permissions__ sequence.
    """
    for setting in permissions:
        if _registerdPermission(setting[0]): continue
        if len(setting)==2:
            perm, methods = setting
            default = defaultDefault
        else:
            perm, methods, default = setting
        _registeredPermissions[perm]=1
        Products.__ac_permissions__=(
            Products.__ac_permissions__+((perm,(),default),))
        mangled=pname(perm) # get mangled permission name
        if not hasattr(Globals.ApplicationDefaultPermissions, mangled):
            setattr(Globals.ApplicationDefaultPermissions,
                    mangled, default)
