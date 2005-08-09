##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Basic Item class and class manager
"""

import Acquisition, ExtensionClass, Globals, OFS.PropertySheets, OFS.Folder
from AccessControl.Permission import pname
import App.Dialogs, ZClasses, App.Factory, App.ProductRegistry
import ZClassOwner
from AccessControl.PermissionMapping import aqwrap, PermissionMapper

import OFS.content_types
from OFS.DTMLMethod import DTMLMethod
from Products.PythonScripts.PythonScript import PythonScript
from zExceptions import BadRequest

import marshal
from cgi import escape

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
            raise BadRequest, 'The id, %s, is reserved' % escape(id)

        if not allow_dup and self.getClassAttr(id, self) is not self:
            raise BadRequest, (
                'The id %s is invalid - it is already in use.' % escape(id))

        ZClassMethodsSheet.inheritedAttribute('_checkId')(
            self, id, 1)

        return id+' '

    def _setOb(self, id, object):
        self.setClassAttr(id.strip(), MWp(object))

    def _delOb(self, id):
        self.delClassAttr(id.strip())

    def _delObject(self, id, dp=1):
        # Ick!  This is necessary to deal with spaces. Waaa!
        object=self._getOb(id)
        object.manage_beforeDelete(object, self)
        id=id.strip()
        self._objects=tuple(filter(lambda i,n=id:
                                   i['id'].strip() != n,
                                   self._objects))
        self._delOb(id)

    def _getOb(self, id, default=_marker):
        if default is _marker:
            r=self.getClassAttr(id.strip())
        else:
            try: r=self.getClassAttr(id.strip())
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
                self.setClassAttr(id.strip(), mw)

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

    #
    #   FTP support
    #
    def manage_FTPstat(self,REQUEST):
        "Psuedo stat used for FTP listings"
        mode=0040000|0770
        mtime=self.bobobase_modification_time().timeTime()
        owner=group='Zope'
        return marshal.dumps((mode,0,0,1,owner,group,0,mtime,mtime,mtime))

    def PUT_factory( self, name, typ, body ):
        """
            Hook PUT creation to make objects of the right type when
            new item uploaded via FTP/WebDAV.
        """
        if typ is None:
            typ, enc = OFS.content_types.guess_content_type()
        if typ == 'text/x-python':
            return PythonScript( name )
        if typ[ :4 ] == 'text':
            return DTMLMethod( '', __name__=name )
        return None # take the default, then


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
