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
    'addZClass', globals(), default_class_='OFS.SimpleItem Item',
    CreateAFactory=1)


def find_class(ob, name):
    # Walk up the aq hierarchy, looking for a ZClass
    # with the given name.
    while 1:
        if hasattr(ob, name):
            return getattr(ob, name)
        elif hasattr(ob, '_getOb'):
            try:    return ob._getOb(name)
            except: pass
        if hasattr(ob, 'aq_parent'):
            ob=ob.aq_parent
            continue
        raise AttributeError, name

def dbVersionEquals(ver):
    # A helper function to isolate db version checking.
    return hasattr(Globals, 'DatabaseVersion') and \
       Globals.DatabaseVersion == ver


def manage_addZClass(self, id, title='', baseclasses=[],
                     meta_type='', CreateAFactory=0, REQUEST=None):
    """Add a Z Class
    """
    bases=[]
    for b in baseclasses:
        if Products.meta_classes.has_key(b):
            bases.append(Products.meta_classes[b])
        else:
            base=find_class(self, b)
            bases.append(base)


    Z=ZClass(id,title,bases)
    if meta_type: Z._zclass_.meta_type=meta_type
    self._setObject(id, Z)

    if CreateAFactory and meta_type:
        self.manage_addDTMLMethod(
            id+'_addForm', 
            id+' constructor input form', 
            addFormDefault % {'id': id, 'meta_type': meta_type},
            )
        self.manage_addDTMLMethod(
            id+'_add',
            id+' constructor',
            addDefault % {'id': id},
            )
        self.manage_addPermission(
            id+'_add_permission',
            id+' constructor permission',
            'Add %ss' % meta_type 
            )
        self.manage_addPrincipiaFactory(
            id+'_factory',
            id+' factory',
            meta_type,
            id+'_addForm',
            'Add %ss' % meta_type 
            )

        Z=self._getOb(id)
        Z.propertysheets.permissions.manage_edit(
            selected=['Add %ss' % id])
        Z.manage_setPermissionMapping(
            permission_names=['Create class instances'],
            class_permissions=['Add %ss' % meta_type]
        ) 
    if REQUEST is not None:
        return self.manage_main(self,REQUEST, update_menu=1)

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
	('Create class instances',
         ('', '__call__', 'index_html', 'createInObjectManager')),
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
        base_classes=[PersistentClass]
        zsheets_base_classes=[PersistentClass]
        isheets_base_classes=[PersistentClass]
        zbases=[ZStandardSheets]
        for z in bases:
            base_classes.append(z._zclass_)
            zbases.append(z)
            try: zsheets_base_classes.append(z.propertysheets.__class__)
            except AttributeError: pass
            try:
                psc=z._zclass_.propertysheets.__class__
                if getattr(psc,
                           '_implements_the_notional'
                           '_subclassable_propertysheet'
                           '_class_interface',
                           0):
                    isheets_base_classes.append(psc)
            except AttributeError: pass

        base_classes.append(OFS.SimpleItem.SimpleItem)
        zsheets_base_classes.append(ZClassSheets)
        isheets_base_classes.append(Property.ZInstanceSheets)

        # Create the meta-class property sheet
        zsheets_class=type(PersistentClass)(
            id+'_ZPropertySheetsClass',
            tuple(zsheets_base_classes)+(Globals.Persistent,),
            PersistentClassDict(id+'_ZPropertySheetsClass'))
        self.propertysheets=sheets=zsheets_class()

        # Create the class
        self._zclass_=c=type(PersistentClass)(
            id, tuple(base_classes),
            PersistentClassDict(title or id))
        c.__ac_permissions__=()

        options=[]
        for option in c.manage_options:
            copy={}
            copy.update(option)
            options.append(copy)
        c.manage_options=tuple(options)
        
        # Create the class(/instance) prop sheet *class*
        isheets_class=type(PersistentClass)(
            id+'_PropertySheetsClass',
            tuple(isheets_base_classes),
            PersistentClassDict(id+' Property Sheets'))        

        # Record the class property sheet class in the meta-class so
        # that we can manage it:
        self._zclass_propertysheets_class=isheets_class
        
        # Finally create the new classes propertysheets by instantiating the
        # propertysheets class.
        c.propertysheets=isheets_class()

        # Save base meta-classes:
        self._zbases=zbases

    def cb_isCopyable(self):
        pass # for now, we don't allow ZClasses to be copied.
    cb_isMovable=cb_isCopyable

    def _setBasesHoldOnToYourButts(self, bases):
        # Eeeek
        copy=self.__class__(self.id, self.title, bases)

        copy._zclass_.__dict__.update(
            self._zclass_.__dict__)
        get_transaction().register(
            copy._zclass_)
        self._p_jar.exchange(self._zclass_, copy._zclass_)
        self._zclass_=copy._zclass_

        copy._zclass_propertysheets_class.__dict__.update(
            self._zclass_propertysheets_class.__dict__)
        get_transaction().register(
            copy._zclass_propertysheets_class)
        self._p_jar.exchange(self._zclass_propertysheets_class,
                             copy._zclass_propertysheets_class)
        self._zclass_propertysheets_class=copy._zclass_propertysheets_class

        if hasattr(self.propertysheets.__class__, '_p_oid'):
            copy.propertysheets.__class__.__dict__.update(
                self.propertysheets.__class__.__dict__)
            get_transaction().register(
                copy.propertysheets.__class__)
            self._p_jar.exchange(self.propertysheets.__class__,
                                 copy.propertysheets.__class__)

        self._zbases=copy._zbases

    def _new_class_id(self):
        import md5, base64, time

        id=md5.new()
        id.update(self.absolute_url())
        id.update(str(time.time()))
        id=id.digest()
        id=string.strip(base64.encodestring(id))

        return '*'+id

    def changeClassId(self, newid=None):
        if not dbVersionEquals('3'):
            return
        if newid is None: newid=self._new_class_id()
        self._unregister()
        if newid:
            if not newid[:1] == '*': newid='*'+newid
            self.setClassAttr('__module__', newid)
            self._register()

    def _waaa_getJar(self):
        # Waaa, we need our jar to register, but we may not have one yet when
        # we need to register, so we'll walk our acquisition tree looking
        # for one.
        jar=None
        while 1:
            if hasattr(self, '_p_jar'):
                jar=self._p_jar
            if jar is not None:
                return jar
            if not hasattr(self, 'aq_parent'):
                return jar
            self=self.aq_parent


    def _register(self):

        # Register the global id of the managed class:
        z=self._zclass_
        class_id=z.__module__
        if not class_id: return

        jar=self._waaa_getJar()
        globals=jar.root()['ZGlobals']
        if globals.has_key(class_id):
            raise 'Duplicate Class Ids'

        globals[class_id]=z

        # Register self as a ZClass:
        self.aq_acquire('_manage_add_product_data')(
            'zclasses',
            product=self.aq_inner.aq_parent.id,
            id=self.id,
            meta_type=z.meta_type or '',
            meta_class=self,
            )

    def _unregister(self):

        # Unregister the global id of the managed class:
        class_id=self._zclass_.__module__
        if not class_id: return
        globals=self._p_jar.root()['ZGlobals']
        if globals.has_key(class_id):
            del globals[class_id]

        # Unregister self as a ZClass:
        self.aq_acquire('_manage_remove_product_data')(
            'zclasses',
            product=self.aq_inner.aq_parent.id,
            id=self.id,
            )

    def manage_afterClone(self, item):
        self.setClassAttr('__module__', None)
        self.propertysheets.methods.manage_afterClone(item)
        
    def manage_afterAdd(self, item, container):
        if not dbVersionEquals('3'):
            return
        if not self._zclass_.__module__:
            self.setClassAttr('__module__', self._new_class_id())
        self._register()
        self.propertysheets.methods.manage_afterAdd(item, container)

    def manage_beforeDelete(self, item, container):
        if not dbVersionEquals('3'):
            return
        self._unregister()
        self.propertysheets.methods.manage_beforeDelete(item, container)

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

    def createInObjectManager(self, id, REQUEST, RESPONSE=None):
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
        
    index_html=createInObjectManager

    def fromRequest(self, id=None, REQUEST={}):
        i=mapply(self._zclass_, (), REQUEST)
        if id is not None and (not hasattr(i, 'id') or not i.id): i.id=id

        return i
        
    def __call__(self, *args, **kw):
        return apply(self._zclass_, args, kw)

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

    ziconImage__roles__=None

    def tpValues(self):
        return self.propertysheets.common, self.propertysheets.methods

    def ZClassBaseClassNames(self):
        r=[]
        for c in self._zbases:
            if hasattr(c, 'id'): r.append(c.id)
            elif hasattr(c, '__name__'): r.append(c.__name__)

        return r

    def _getZClass(self): return self
            
class ZClassSheets(OFS.PropertySheets.PropertySheets):
    "Manage a collection of property sheets that provide ZClass management"

    #isPrincipiaFolderish=1
    #def tpValues(self): return self.methods, self.common
    #def tpURL(self): return 'propertysheets'
    def manage_workspace(self, URL2):
        "Emulate standard interface for use with navigation"
        raise 'Redirect', URL2+'/manage_workspace'

    views       = Basic.ZClassViewsSheet('views')
    basic       = Basic.ZClassBasicSheet('basic')
    permissions = Basic.ZClassPermissionsSheet('permissions')

    def __init__(self):
        self.methods=Method.ZClassMethodsSheet('methods')
        self.common=Property.ZInstanceSheetsSheet('common')


class ZObject:

    manage_options=(
        {'label': 'Methods', 'action' :'propertysheets/methods/manage'},
        {'label': 'Basic', 'action' :'propertysheets/basic/manage'},
        {'label': 'Views', 'action' :'propertysheets/views/manage'},
        {'label': 'Property Sheets', 'action' :'propertysheets/common/manage'},
        {'label': 'Permissions',
         'action' :'propertysheets/permissions/manage'},
        {'label': 'Security', 'action' :'manage_access'},        
        )
    
ZStandardSheets=ZObject

def findActions(klass, found):
    for b in klass.__bases__:
        try:
            for d in b.manage_options:
                found[d['action']]=1
            findActions(b, found)
        except: pass

addFormDefault="""<HTML> 
<HEAD><TITLE>Add %(meta_type)s</TITLE></HEAD> 
<BODY BGCOLOR="#FFFFFF" LINK="#000099" VLINK="#555555"> 
<H2>Add %(meta_type)s</H2> 
<form action="%(id)s_add"><table> 
<tr><th>Id</th> 
    <td><input type=text name=id></td> 
</tr> 
<tr><td></td><td><input type=submit value=" Add "></td></tr> 
</table></form> 
</body></html> 
"""

addDefault="""<HTML>
<HEAD><TITLE>Add %(id)s</TITLE></HEAD>
<BODY BGCOLOR="#FFFFFF" LINK="#000099" VLINK="#555555">

<dtml-comment> We add the new object by calling the class in
                a with tag.  Not only does this get the thing
                added, it adds the new thing's attributes to
                the DTML name space, so we can call methods
                to initialize the object.
</dtml-comment>

<dtml-with "%(id)s.createInObjectManager(REQUEST['id'], REQUEST)">

  <dtml-comment>

     You can ad code that modifies the new instance here.

     For example, if you have a property sheet that you want to update
     from form values, you can call it here:

       <dtml-call "propertysheets.Basic.manage_editProperties(
                  REQUEST)">

  </dtml-comment>

</dtml-with>

<dtml-comment> Now we need to return something.  We do this via
                a redirect so that the URL is correct.

                Unfortunately, the way we do this depends on
                whether we live in a product or in a class.
                If we live in a product, we need to use DestinationURL
                to decide where to go. If we live in a class,
                DestinationURL won't be available, so we use URL2.
</dtml-comment>
<dtml-if DestinationURL>

 <dtml-call "RESPONSE.redirect(
       DestinationURL+'/manage_workspace')">

<dtml-else>

    <dtml-call "RESPONSE.redirect(
           URL2+'/manage_workspace')">
</dtml-if>
</body></html>
"""
