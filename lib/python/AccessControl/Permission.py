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
__doc__='''short description


$Id: Permission.py,v 1.3 1998/12/04 20:15:25 jim Exp $'''
__version__='$Revision: 1.3 $'[11:-2]

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
