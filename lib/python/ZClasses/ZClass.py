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
"""Zope Classes
"""
import Globals, string, OFS.SimpleItem, OFS.PropertySheets, Products
import Method, Basic, Property, AccessControl.Role

from ZPublisher.mapply import mapply
from ExtensionClass import Base
from App.FactoryDispatcher import FactoryDispatcher
from ComputedAttribute import ComputedAttribute
from OFS.misc_ import p_

p_.ZClass_Icon=Globals.ImageFile('class.gif', globals())

class PersistentClass(Base):
    def __class_init__(self): pass

manage_addZClassForm=Globals.HTMLFile(
    'addZClass', globals(), default_class_='OFS.SimpleItem Item')

def manage_addZClass(self, id, title='', baseclasses=[], REQUEST=None):
    """Add a Z Class
    """
    bases=[]
    for b in baseclasses:
        if Products.meta_classes.has_key(b):
            bases.append(Products.meta_classes[b])
        else:
            bases.append(getattr(self, b))

    self._setObject(id, ZClass(id,title,bases))
    if REQUEST is not None: return self.manage_main(self,REQUEST)

def manage_subclassableClassNames(self):
    r={}
    r.update(Products.meta_class_info)

    while 1:
        if not hasattr(self, 'objectItems'): break
        for k, v in self.objectItems():
            if hasattr(v,'_zclass_') and not r.has_key(k):
                r[k]=v.title_and_id()
        if not hasattr(self, 'aq_parent'): break
        self=self.aq_parent
                
    r=r.items()
    r.sort()
    return r

class Template:
    _p_oid=_p_jar=__module__=None
    _p_changed=0
    icon=''

def PersistentClassDict(doc=None, meta_type=None):
        # Build new class dict
        dict={}
        dict.update(Template.__dict__)
        if meta_type is not None:
            dict['meta_type']=dict['__doc__']=meta_type
        if doc is not None:
            dict['__doc__']=doc
        return dict

_marker=[]
class ZClass(OFS.SimpleItem.SimpleItem):
    """Zope Class
    """
    meta_type="Z Class"
    icon="p_/ZClass_Icon"
    instance__meta_type='instance'
    instance__icon=''
    __propsets__=()
    isPrincipiaFolderish=1
 
    __ac_permissions__=(
	('View management screens', ('manage_tabs', 'manage_workspace')),
	('Change permissions',      ('manage_access',)                 ),
	('View',                    ('', '__call__', 'index_html')     ),
	)

    def __init__(self, id, title, bases):
        """Build a Zope class

        A Zope class is *really* a meta-class that manages an
        actual extension class that is instantiated to create instances.
        """
        self.id=id
        self.title=title
        
        # Set up base classes for new class, the meta class prop
        # sheet and the class(/instance) prop sheet.
        args=[PersistentClass]
        zsheets_classes=[PersistentClass]
        csheets_classes=[PersistentClass]
        zbases=[ZStandardSheets]
        for z in bases:
            args.append(z._zclass_)
            zbases.append(z)
            try: zsheets_classes.append(z.propertysheets.__class__)
            except AttributeError: pass
            try: csheets_classes.append(z._zclass_.propertysheets.__class__)
            except AttributeError: pass

        args.append(OFS.SimpleItem.SimpleItem)
        zsheets_classes.append(ZClassSheets)
        csheets_classes.append(Property.ZInstanceSheets)

        # Create the meta-class property sheet
        if len(zsheets_classes) > 2:
            zsheets_class=type(PersistentClass)(
                id+'_ZPropertySheetsClass',
                tuple(zsheets_classes)+(Globals.Persistent,),
                PersistentClassDict(id+'_ZPropertySheetsClass'))
        else: zsheets_class=zsheets_classes[1]
        self.propertysheets=sheets=zsheets_class()

        # Create the class
        self._zclass_=c=type(PersistentClass)(
            id, tuple(args),
            PersistentClassDict(title or id))
        c.__ac_permissions__=()
        
        # Create the class(/instance) prop sheet *class*
        csheets_class=type(PersistentClass)(
            id+'_PropertySheetsClass',
            tuple(csheets_classes),
            PersistentClassDict(id+' Property Sheets'))        

        # Record the class property sheet class in the meta-class so
        # that we can manage it:
        self._zclass_propertysheets_class=csheets_class
        
        # Finally create the new classes propertysheets by instantiating the
        # propertysheets class.
        c.propertysheets=csheets_class()

        # Save base meta-classes:
        self._zbases=zbases

    def manage_options(self):
        r=[]
        d={}
        have=d.has_key
        for z in self._zbases:
            for o in z.manage_options:                
                label=o['label']
                if have(label): continue
                d[label]=1
                r.append(o)
        return r

    manage_options=ComputedAttribute(manage_options)

    def index_html(self, id, REQUEST, RESPONSE=None):
        """
        Create Z instance. If called with a RESPONSE,
        the RESPONSE will be redirected to the management
        screen of the new instance's parent Folder. Otherwise,
        the instance will be returned.
        """
        i=mapply(self._zclass_, (), REQUEST)
        if not hasattr(i, 'id') or not i.id: i.id=id

        folder=durl=None
        if hasattr(self, 'Destination'):
            d=self.Destination
            if d.im_self.__class__ is FactoryDispatcher:
                folder=d()
        if folder is None: folder=self.aq_parent
        if not hasattr(folder,'_setObject'):
            folder=folder.aq_parent

        folder._setObject(id, i)

        if RESPONSE is not None:
            try: durl=self.DestinationURL()
            except: durl=REQUEST['URL3']
            RESPONSE.redirect(durl+'/manage_workspace')
        else:
            return getattr(folder, id)
        

    __call__=index_html

    def zclass_candidate_view_actions(self):
        r={}

        zclass=self._zclass_
        # Step one, look at all of the methods.
        # We can cheat (hee hee) and and look in the _zclass_
        # dict for wrapped objects.
        for id in Method.findMethodIds(zclass):
            r[id]=1

        # OK, now lets check out the inherited views:
        findActions(zclass, r)

        # OK, now add our property sheets.
        for id in self.propertysheets.common.objectIds():
            r['propertysheets/%s/manage' % id]=1

        r=r.keys()
        r.sort()
        return r

    def getClassAttr(self, name, default=_marker, inherit=0):
        if default is _marker:
            if inherit: return getattr(self._zclass_, name)
            else: return self._zclass_.__dict__[name]
        try:
            if inherit: return getattr(self._zclass_, name)
            else: return self._zclass_.__dict__[name]
        except: return default

    def setClassAttr(self, name, value):
        c=self._zclass_
        setattr(c, name, value)
        if not c._p_changed:
            get_transaction().register(c)
            c._p_changed=1

    def delClassAttr(self, name):
        c=self._zclass_
        delattr(c, name)
        if not c._p_changed:
            get_transaction().register(c)
            c._p_changed=1

    def classDefinedPermissions(self):
        c=self._zclass_
        r=[]
        a=r.append
        for p in c.__ac_permissions__: a(p[0])
        r.sort()
        return r

    def classInheritedPermissions(self):
        c=self._zclass_
        d={}
        for p in c.__ac_permissions__: d[p[0]]=None
        r=[]
        a=r.append
        for p in AccessControl.Role.gather_permissions(c, [], d): a(p[0])
        r.sort()
        return r

    def classDefinedAndInheritedPermissions(self):
        return (self.classDefinedPermissions()+
                self.classInheritedPermissions())

    def ziconImage(self, REQUEST, RESPONSE):
        "Display a class icon"
        return self._zclass_.ziconImage.index_html(REQUEST, RESPONSE)

    def tpValues(self):
        return self.propertysheets.common, self.propertysheets.methods
            
class ZClassSheets(OFS.PropertySheets.PropertySheets):
    "Manage a collection of property sheets that provide ZClass management"

    #isPrincipiaFolderish=1
    #def tpValues(self): return self.methods, self.common
    #def tpURL(self): return 'propertysheets'
    #def manage_workspace(self, URL1):
    #    "Emulate standard interface for use with navigation"
    #    raise 'Redirect', URL1+'/manage'

    views       = Basic.ZClassViewsSheet('views')
    basic       = Basic.ZClassBasicSheet('basic')
    permissions = Basic.ZClassPermissionsSheet('permissions')

    def __init__(self):
        self.methods=Method.ZClassMethodsSheet('methods')
        self.common=Property.ZInstanceSheetsSheet('common')


class ZStandardSheets:

    manage_options=(
        {'label': 'Basic', 'action' :'propertysheets/basic/manage'},
        {'label': 'Methods', 'action' :'propertysheets/methods/manage'},
        {'label': 'Views', 'action' :'propertysheets/views/manage'},
        {'label': 'Property Sheets', 'action' :'propertysheets/common/manage'},
        {'label': 'Permissions',
         'action' :'propertysheets/permissions/manage'},
        {'label': 'Security', 'action' :'manage_access'},        
        )

def findActions(klass, found):
    for b in klass.__bases__:
        try:
            for d in b.manage_options:
                found[d['action']]=1
            findActions(b, found)
        except: pass
