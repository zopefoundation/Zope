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
"""Basic Item class and class manager
"""

import Acquisition, ExtensionClass, Globals, OFS.PropertySheets, OFS.Folder
from AccessControl.Permission import pname
from string import strip
import App.Dialogs, ZClasses, App.Factory, App.Product, App.ProductRegistry
import ZClassOwner
from AccessControl.PermissionMapping import aqwrap, PermissionMapper

_marker=[]
class ZClassMethodsSheet(
    OFS.PropertySheets.PropertySheet,
    OFS.PropertySheets.View,
    OFS.Folder.Folder,
    App.ProductRegistry.ProductRegistryMixin,
    ZClassOwner.ZClassOwner):
    "Manage instance methods"
    id='contents'
    icon='p_/Methods_icon'

    def tpURL(self): return 'propertysheets/methods'

    ######################################################################
    # Hijinks to let us create factories and classes within classes.

    #meta_types=App.Product.Product.meta_types
    
    meta_types=(
        {'name': 'Z Class',
         'action':'manage_addZClassForm'},
        {'name': App.Factory.Factory.meta_type,
         'action': 'manage_addPrincipiaFactoryForm'
         },
        {'name': 'Property Sheet Interface',
         'action': 'manage_addPropertyInterfaceForm'
         },
        )
    
    def manage_addPrincipiaFactory(
        self, id, title, object_type, initial, permission=None, REQUEST=None):
        ' '
        i=App.Factory.Factory(id, title, object_type, initial, permission)
        self._setObject(id,i)
        factory = self._getOb(id)
        factory.initializePermission()
        if REQUEST is not None:
            return self.manage_main(self,REQUEST,update_menu=1)


    def _getProductRegistryMetaTypes(self):
        return self.getClassAttr('_zclass_method_meta_types',())
    
    def _setProductRegistryMetaTypes(self, v):
        return self.setClassAttr('_zclass_method_meta_types', v)

    def _constructor_prefix_string(self, pid): return ''

    ######################################################################

    manage_addPropertyInterfaceForm=Globals.HTMLFile(
        'dtml/addPropertyInterface',
        globals())


    # This is to trigger alternate access management for methods:
    _isBeingUsedAsAMethod_=1
    def _isBeingUsedAsAMethod(self, REQUEST =None, wannaBe=0):
        if REQUEST is not None and wannaBe: REQUEST.response.notFoundError()
        return 0

    def permissionMappingPossibleValues(self):
        return self.classDefinedAndInheritedPermissions()

    def meta_type(self):
        return self.aq_inner.aq_parent.aq_parent.meta_type

    def manage(self, REQUEST):
        " "
        return self.manage_main(self, REQUEST)

    def manage_addDTMLMethod(self, id, title='', file='',
                             REQUEST=None, submit=None):
        "Add a DTML Method using a management template"
        if not file: file=default_dm_html
        return ZClassMethodsSheet.inheritedAttribute('manage_addDTMLMethod')(
            self, id, title, file, REQUEST, submit)



    def _checkId(self, id, allow_dup=0,
                 _reserved=('propertysheets','manage_workspace')):
        if id in _reserved:
            raise 'Bad Request', 'The id, %s, is reseverd' % id

        if not allow_dup and self.getClassAttr(id, self) is not self:
            raise 'Bad Request', (
                'The id %s is invalid - it is already in use.' % id)

        ZClassMethodsSheet.inheritedAttribute('_checkId')(
            self, id, 1)

        return id+' '

    def _setOb(self, id, object):
        self.setClassAttr(strip(id), MWp(object))

    def _delOb(self, id):
        self.delClassAttr(strip(id))

    def _delObject(self, id, dp=1):
        # Ick!  This is necessary to deal with spaces. Waaa!
        object=self._getOb(id)
        object.manage_beforeDelete(object, self)
        id=strip(id)
        self._objects=tuple(filter(lambda i,n=id:
                                   strip(i['id']) != n,
                                   self._objects))
        self._delOb(id)

    def _getOb(self, id, default=_marker):
        if default is _marker:
            r=self.getClassAttr(strip(id))
        else:
            try: r=self.getClassAttr(strip(id))
            except: return default

        if hasattr(r, methodattr):
            m=r.__dict__[methodattr]
            if r.__class__ is W:
                # Ugh, we need to convert an old wrapper to a new one
                wrapper=getattr(m, '_permissionMapper', None)
                if wrapper is None: wrapper=PermissionMapper()

                for k, v in r.__dict__.items():
                    if k[:1]=='_' and k[-11:]=='_Permission':
                        setattr(wrapper, k, v)

                m._permissionMapper=wrapper

                mw=MWp(m)
                self.setClassAttr(strip(id), mw)

            r=m

        return getattr(r, 'aq_base', r).__of__(self)

    def __bobo_traverse__(self, request, name):
        if hasattr(self, 'aq_base'):
            b=self.aq_base
            if hasattr(b,name): return getattr(self, name)
        
        try: return self[name]
        except: return getattr(self, name) 

    def possible_permissions(self):
        return self.classDefinedAndInheritedPermissions()

default_dm_html='''<html>
<head><title><dtml-var document_title></title></head>
<body bgcolor="#FFFFFF" LINK="#000099" VLINK="#555555">
<dtml-var manage_tabs>

<P>This is the <dtml-var document_id> Document in
the <dtml-var title_and_id> Folder.</P>

</body></html>
'''

methodattr='_ZClassMethodPermissionMapperMethod_'

class MW(ExtensionClass.Base):

    def __init__(self, meth): self.__dict__[methodattr]=meth
            
    def __of__(self, parent):
        m=getattr(self, methodattr)
        m=self.__dict__[methodattr]
        wrapper=getattr(m, '_permissionMapper', None)
        if wrapper is None: wrapper=PermissionMapper()
        if hasattr(m,'__of__'): return aqwrap(m, wrapper, parent)
        return m

class MWp(Globals.Persistent):

    def __init__(self, meth): self.__dict__[methodattr]=meth
    __setstate__=__init__

    def __getstate__(self):
        getattr(self, methodattr)
        return self.__dict__[methodattr]
                
    def __of__(self, parent):
        m=getattr(self, methodattr)
        m=self.__dict__[methodattr]
        wrapper=getattr(m, '_permissionMapper', None)
        if wrapper is None: wrapper=PermissionMapper()
        if hasattr(m,'__of__'): return aqwrap(m, wrapper, parent)
        return m

    

# Backward compat. Waaaaa
class W(Globals.Persistent, MW):

    _View_Permission='_View_Permission'
        
    def __getattr__(self, name):
        # We want to make sure that any non-explicitly set methods are
        # private!
        try:
            # Oh this sucks
            return W.inheritedAttribute('__getattr__')(self, name)
        except: pass
            
        if name[:1]=='_' and name[-11:]=="_Permission": return ''
        raise AttributeError, name
            
    def __of__(self, parent):
        m=getattr(self, methodattr)
        m=self.__dict__[methodattr]
        if hasattr(m,'__of__'): return aqwrap(m, self, parent)
        return m
    

def findMethodIds(klass, methodTypes=(MWp, MW, W)):
    r=[]
    for k, v in klass.__dict__.items():
        if type(v) in methodTypes: r.append(k)

    return r
