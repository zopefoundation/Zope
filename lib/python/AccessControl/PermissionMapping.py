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
"""Permission Mapping

Sometimes, we need an object's permissions to be remapped to other permissions
when the object is used in specual ways.  This is rather hard, since we
need the object's ordinary permissions intact so we can manage it.
"""

import ExtensionClass, Acquisition
from Permission import pname
from Owned import UnownableOwner

class RoleManager:

        
    def manage_getPermissionMapping(self):
        """Return the permission mapping for the object

        This is a list of dictionaries with:

          permission_name -- The name of the native object permission

          class_permission -- The class permission the permission is
             mapped to.
        """
        wrapper=getattr(self, '_permissionMapper', None)
        if wrapper is None: wrapper=PM()

        perms={}
        for p in self.possible_permissions():
            perms[pname(p)]=p
        
        r=[]
        a=r.append
        for ac_perms in self.ac_inherited_permissions(1):
            p=perms.get(getPermissionMapping(ac_perms[0], wrapper), '')
            a({'permission_name': ac_perms[0], 'class_permission': p})
        return r

    def manage_setPermissionMapping(self,
                                    permission_names=[],
                                    class_permissions=[], REQUEST=None):
        """Change the permission mapping
        """
        wrapper=getattr(self, '_permissionMapper', None)
        if wrapper is None: wrapper=PM()

        perms=self.possible_permissions()
        for i in range(len(permission_names)):
            name=permission_names[i]
            p=class_permissions[i]
            if p and (p not in perms):
                __traceback_info__=perms, p, i
                raise 'Permission mapping error', (
                    """Attempted to map a permission to a permission, %s,
                    that is not valid. This should never happen. (Waaa).
                    """ % p)
            

            setPermissionMapping(name, wrapper, p)

        self._permissionMapper=wrapper

        if REQUEST is not None:
            return self.manage_access(
                self, REQUEST, 
                manage_tabs_message='The permission mapping has been updated')

    def _isBeingUsedAsAMethod(self, REQUEST =None, wannaBe=0):
        try:
            if hasattr(self, 'aq_self'):
                r=self.aq_acquire('_isBeingUsedAsAMethod_')
            else:
                r=self._isBeingUsedAsAMethod_
        except: r=0

        if REQUEST is not None:
            if not r != (not wannaBe): REQUEST.response.notFoundError()

        return r

    def _isBeingAccessedAsZClassDefinedInstanceMethod(self):
        p=getattr(self,'aq_parent',None)
        if p is None: return 0          # Not wrapped
        base=getattr(p, 'aq_base', None)
        return type(base) is PermissionMapper  
              
                                        
 
def getPermissionMapping(name, obj, st=type('')):
    obj=getattr(obj, 'aq_base', obj)
    name=pname(name)
    r=getattr(obj, name, '')
    if type(r) is not st: r=''
    return r

def setPermissionMapping(name, obj, v):
    name=pname(name)
    if v: setattr(obj, name, pname(v))
    elif obj.__dict__.has_key(name): delattr(obj, name)

class PM(ExtensionClass.Base):
    _owner=UnownableOwner

    _View_Permission='_View_Permission'
    _is_wrapperish = 1
        
    def __getattr__(self, name):
        # We want to make sure that any non-explicitly set methods are
        # private!
        if name[:1]=='_' and name[-11:]=="_Permission": return ''
        raise AttributeError, name
        
PermissionMapper=PM

def aqwrap(object, wrapper, parent):
    r=Rewrapper()
    r._ugh=wrapper, object, parent
    return r

class Rewrapper(ExtensionClass.Base):
    def __of__(self, parent):
        w, m, p = self._ugh
        return m.__of__(
            Acquisition.ImplicitAcquisitionWrapper(
                w, parent))

    def __getattr__(self, name):
        w, m, parent = self._ugh
        self=m.__of__(
            Acquisition.ImplicitAcquisitionWrapper(
                w, parent))
        return getattr(self, name)

    def __call__(self, *args, **kw):
        w, m, parent = self._ugh
        self=m.__of__(
            Acquisition.ImplicitAcquisitionWrapper(
                w, parent))
        return apply(self, args, kw)
