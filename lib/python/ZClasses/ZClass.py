##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Zope Classes
"""
import Globals,  OFS.SimpleItem, OFS.PropertySheets, Products
from Globals import InitializeClass
import Method, Basic, Property, AccessControl.Role, re
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import create_class_instances

from ZPublisher.mapply import mapply
from ExtensionClass import Base
from Acquisition import aq_base
from App.FactoryDispatcher import FactoryDispatcher
from ComputedAttribute import ComputedAttribute
from Products.PythonScripts.PythonScript import PythonScript
from zExceptions import BadRequest, Redirect
import webdav.Collection
import ZClasses._pmc

import transaction

import marshal

if not hasattr(Products, 'meta_types'):
    Products.meta_types=()

if not hasattr(Products, 'meta_classes'):
    Products.meta_classes={}
    Products.meta_class_info={}

def createZClassForBase( base_class, pack, nice_name=None, meta_type=None ):
    """
      * Create a ZClass for 'base_class' in 'pack' (before a ProductContext
        is available).  'pack' may be either the module which is to
        contain the ZClass or its 'globals()'.  If 'nice_name' is
        passed, use it as the name for the created class, and create
        the "ugly" '_ZClass_for_...' name as an alias;  otherwise,
        just use the "ugly" name.

      * Register the ZClass under its meta_type in the Products registries.
    """
    d                 = {}
    zname             = '_ZClass_for_' + base_class.__name__

    if nice_name is None:
        nice_name = zname

    exec 'class %s: pass' % nice_name in d

    Z                 = d[nice_name]
    Z.propertysheets  = OFS.PropertySheets.PropertySheets()
    Z._zclass_        = base_class
    Z.manage_options  = ()

    try:
        Z.__module__  = pack.__name__
        setattr( pack, nice_name, Z )
        setattr( pack, zname, Z )
    except AttributeError: # we might be passed 'globals()'
        Z.__module__      = pack[ '__name__' ]
        pack[ nice_name ] = Z
        pack[ zname ]     = Z

    if meta_type is None:
        if hasattr(base_class, 'meta_type'): meta_type=base_class.meta_type
        else:                                meta_type=base_class.__name__

    base_module = base_class.__module__
    base_name   = base_class.__name__

    key         = "%s/%s" % (base_module, base_name)

    if base_module[:9] == 'Products.':
        base_module = base_module.split('.' )[1]
    else:
        base_module = base_module.split('.' )[0]

    info="%s: %s" % ( base_module, base_name )

    Products.meta_class_info[key] = info # meta_type
    Products.meta_classes[key]    = Z

    return Z

from OFS.misc_ import p_

p_.ZClass_Icon=Globals.ImageFile('class.gif', globals())

class PersistentClass(Base, webdav.Collection.Collection ):

    __metaclass__ = ZClasses._pmc.ZClassPersistentMetaClass

    # We need this class to be treated as a normal global class, even
    # though it is an instance of ZClassPersistentMetaClass.
    # Subclasses should be stored in the database.  See
    # _pmc._p_DataDescr.__get__.
    
    __global_persistent_class_not_stored_in_DB__ = True
    
    def __class_init__(self):
        pass

manage_addZClassForm=Globals.DTMLFile(
    'dtml/addZClass', globals(),
    default_class_='OFS.SimpleItem Item',
    CreateAFactory=1,
    zope_object=1)


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

bad_id=re.compile('[^a-zA-Z0-9_]').search

def manage_addZClass(self, id, title='', baseclasses=[],
                     meta_type='', CreateAFactory=0, REQUEST=None,
                     zope_object=0):
    """Add a Z Class
    """
    
    if bad_id(id) is not None:
        raise BadRequest, (
            'The id %s is invalid as a class name.' % id)
    if not meta_type: meta_type=id

    r={}
    for data in self.aq_acquire('_getProductRegistryData')('zclasses'):
        r['%(product)s/%(id)s' % data]=data['meta_class']

    bases=[]
    for b in baseclasses:
        if Products.meta_classes.has_key(b):
            bases.append(Products.meta_classes[b])
        elif r.has_key(b):
            bases.append(r[b])
        else:
            raise ValueError, 'Invalid class: %s' % b

    Z=ZClass(id, title, bases, zope_object=zope_object)
    Z._zclass_.meta_type=meta_type
    self._setObject(id, Z)

    if CreateAFactory and meta_type:
        self.manage_addDTMLMethod(
            id+'_addForm',
            id+' constructor input form',
            addFormDefault % {'id': id, 'meta_type': meta_type},
            )
        constScript = PythonScript(id+'_add')
        constScript.write(addDefault % {'id': id, 'title':id+' constructor'})
        self._setObject(constScript.getId(), constScript)
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
class ZClass( Base
            , webdav.Collection.Collection
            , OFS.SimpleItem.SimpleItem
            ):
    """Zope Class
    """
    meta_type="Z Class"
    icon="p_/ZClass_Icon"
    instance__meta_type='instance'
    instance__icon=''
    __propsets__=()
    isPrincipiaFolderish=1

    security = ClassSecurityInfo()
    security.declareObjectProtected(create_class_instances)

    def __init__(self, id, title, bases, zope_object=1):
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

        if zope_object:
            base_classes.append(OFS.SimpleItem.SimpleItem)

        zsheets_base_classes.append(ZClassSheets)
        isheets_base_classes.append(Property.ZInstanceSheets)

        # Create the meta-class property sheet
        sheet_id = id+'_ZPropertySheetsClass'
        zsheets_class=type(PersistentClass)(
            sheet_id,
            tuple(zsheets_base_classes)+(Globals.Persistent,),
            PersistentClassDict(sheet_id, sheet_id))
        self.propertysheets=sheets=zsheets_class()

        # Create the class
        self._zclass_=c=type(PersistentClass)(
            id, tuple(base_classes),
            PersistentClassDict(title or id))
        c.__ac_permissions__=()

        # Copy manage options
        if zope_object:
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
    cb_isMoveable=cb_isCopyable

    def _setBasesHoldOnToYourButts(self, bases):
        # Eeeek
        copy=self.__class__(self.id, self.title, bases,
                            hasattr(self._zclass_, '_p_deactivate')
                            )

        copy._zclass_.__dict__.update(self._zclass_.__dict__)
        transaction.get().register(copy._zclass_)
        self._p_jar.exchange(self._zclass_, copy._zclass_)
        self._zclass_=copy._zclass_

        copy._zclass_propertysheets_class.__dict__.update(
            self._zclass_propertysheets_class.__dict__)
        transaction.get().register(copy._zclass_propertysheets_class)
        self._p_jar.exchange(self._zclass_propertysheets_class,
                             copy._zclass_propertysheets_class)
        self._zclass_propertysheets_class=copy._zclass_propertysheets_class

        if hasattr(self.propertysheets.__class__, '_p_oid'):
            copy.propertysheets.__class__.__dict__.update(
                self.propertysheets.__class__.__dict__)
            transaction.get().register(copy.propertysheets.__class__)
            self._p_jar.exchange(self.propertysheets.__class__,
                                 copy.propertysheets.__class__)

        self._zbases=copy._zbases

    def _new_class_id(self):
        import md5, base64, time

        id=md5.new()
        id.update(self.absolute_url())
        id.update(str(time.time()))
        id=id.digest()
        id=base64.encodestring(id).strip()

        return '*'+id

    security.declarePrivate('changeClassId')
    def changeClassId(self, newid=None):
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
            raise ValueError, 'Duplicate Class Ids'

        globals[class_id]=z

        product=self.aq_inner.aq_parent.zclass_product_name()

        # Register self as a ZClass:
        self.aq_acquire('_manage_add_product_data')(
            'zclasses',
            product=product,
            id=self.id,
            meta_type=z.meta_type or '',
            meta_class=aq_base(self),
            )

    def _unregister(self):

        # Unregister the global id of the managed class:
        class_id=self._zclass_.__module__
        if not class_id: return
        globals=self._p_jar.root()['ZGlobals']
        if globals.has_key(class_id):
            del globals[class_id]

        product=self.aq_inner.aq_parent.zclass_product_name()

        # Unregister self as a ZClass:
        self.aq_acquire('_manage_remove_product_data')(
            'zclasses',
            product=product,
            id=self.id,
            )

    def zclass_product_name(self):
        product=self.aq_inner.aq_parent.zclass_product_name()
        return "%s/%s" % (product, self.id)

    def manage_afterClone(self, item):
        self.setClassAttr('__module__', None)
        self.propertysheets.methods.manage_afterClone(item)

    def manage_afterAdd(self, item, container):
        if not self._zclass_.__module__:
            self.setClassAttr('__module__', self._new_class_id())
        self._register()
        self.propertysheets.methods.manage_afterAdd(item, container)

    def manage_beforeDelete(self, item, container):
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

    security.declareProtected(create_class_instances, 'createInObjectManager')
    def createInObjectManager(self, id, REQUEST, RESPONSE=None):
        """
        Create Z instance. If called with a RESPONSE,
        the RESPONSE will be redirected to the management
        screen of the new instance's parent Folder. Otherwise,
        the instance will be returned.
        """
        i = self.fromRequest(id, REQUEST)
        folder=durl=None
        if hasattr(self, 'Destination'):
            d=self.Destination
            if d.im_self.__class__ is FactoryDispatcher:
                folder=d()
        if folder is None: folder=self.aq_parent
        if not hasattr(folder,'_setObject'):
            folder=folder.aq_parent

        # An object is not guarenteed to have the id we passed in.
        id = i.getId()
        folder._setObject(id, i)

        if RESPONSE is not None:
            try: durl=self.DestinationURL()
            except: durl=REQUEST['URL3']
            RESPONSE.redirect(durl+'/manage_workspace')
        else:
            return folder._getOb(id)

    security.declareProtected(create_class_instances, 'index_html')
    index_html=createInObjectManager

    def fromRequest(self, id=None, REQUEST={}):
        if self._zclass_.__init__ is object.__init__:
            # there is no user defined __init__, avoid calling
            # mapply then, as it would fail while trying
            # to figure out the function properties
            i = self._zclass_()
        else:
            i = mapply(self._zclass_, (), REQUEST)
        if id is not None:
            try:
                i._setId(id)
            except AttributeError:
                i.id = id
        return i

    security.declareProtected(create_class_instances, '__call__')
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

    security.declarePrivate('getClassAttr')
    def getClassAttr(self, name, default=_marker, inherit=0):
        if default is _marker:
            if inherit: return getattr(self._zclass_, name)
            else: return self._zclass_.__dict__[name]
        try:
            if inherit: return getattr(self._zclass_, name)
            else: return self._zclass_.__dict__[name]
        except: return default

    security.declarePrivate('setClassAttr')
    def setClassAttr(self, name, value):
        c=self._zclass_
        setattr(c, name, value)
        if (not c._p_changed) and (c._p_jar is not None):
            transaction.get().register(c)
            c._p_changed=1

    security.declarePrivate('delClassAttr')
    def delClassAttr(self, name):
        c=self._zclass_
        delattr(c, name)
        if (not c._p_changed) and (c._p_jar is not None):
            transaction.get().register(c)
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

    security.declarePublic('ziconImage')
    def ziconImage(self, REQUEST, RESPONSE):
        "Display a class icon"
        return self._zclass_.ziconImage.index_html(REQUEST, RESPONSE)

    def tpValues(self):
        return self.propertysheets.common, self.propertysheets.methods

    def ZClassBaseClassNames(self):
        r=[]
        for c in self._zbases:
            if hasattr(c, 'id'): r.append(c.id)
            elif hasattr(c, '__name__'): r.append(c.__name__)

        return r

    def _getZClass(self): return self

    #
    #   FTP support
    #
    def manage_FTPlist(self,REQUEST):
        "Directory listing for FTP"
        out=()
        files=self.__dict__.items()
        if not (hasattr(self,'isTopLevelPrincipiaApplicationObject') and
                self.isTopLevelPrincipiaApplicationObject):
            files.insert(0,('..',self.aq_parent))
        for k,v in files:
            try:    stat=marshal.loads(v.manage_FTPstat(REQUEST))
            except:
                stat=None
            if stat is not None:
                out=out+((k,stat),)
        return marshal.dumps(out)

    def manage_FTPstat(self,REQUEST):
        "Psuedo stat used for FTP listings"
        mode=0040000|0770
        mtime=self.bobobase_modification_time().timeTime()
        owner=group='Zope'
        return marshal.dumps((mode,0,0,1,owner,group,0,mtime,mtime,mtime))

    #
    #   WebDAV support
    #
    isAnObjectManager=1
    def objectValues( self, filter=None ):
        """
        """
        values = [ self.propertysheets ]
        if filter is not None:
            if type( filter ) == type( '' ):
                filter = [ filter ]
            for value in values:
                if not self.propertysheets.meta_type in filter:
                    values.remove( value )
        return values

InitializeClass(ZClass)


class ZClassSheets(OFS.PropertySheets.PropertySheets):
    "Manage a collection of property sheets that provide ZClass management"

    #isPrincipiaFolderish=1
    #def tpValues(self): return self.methods, self.common
    #def tpURL(self): return 'propertysheets'
    def manage_workspace(self, URL2):
        "Emulate standard interface for use with navigation"
        raise Redirect, URL2+'/manage_workspace'

    views       = Basic.ZClassViewsSheet('views')
    basic       = Basic.ZClassBasicSheet('basic')
    permissions = Basic.ZClassPermissionsSheet('permissions')

    def __init__(self):
        self.methods=Method.ZClassMethodsSheet('methods')
        self.common=Property.ZInstanceSheetsSheet('common')

    #
    #   FTP support
    #
    def manage_FTPlist(self,REQUEST):
        "Directory listing for FTP"
        out=()
        files=self.__dict__.items()
        if not (hasattr(self,'isTopLevelPrincipiaApplicationObject') and
                self.isTopLevelPrincipiaApplicationObject):
            files.insert(0,('..',self.aq_parent))
        for k,v in files:
            try:    stat=marshal.loads(v.manage_FTPstat(REQUEST))
            except:
                stat=None
            if stat is not None:
                out=out+((k,stat),)
        return marshal.dumps(out)

    def manage_FTPstat(self,REQUEST):
        "Psuedo stat used for FTP listings"
        mode=0040000|0770
        mtime=self.bobobase_modification_time().timeTime()
        owner=group='Zope'
        return marshal.dumps((mode,0,0,1,owner,group,0,mtime,mtime,mtime))

    #
    #   WebDAV support
    #
    isAnObjectManager=1

    def objectValues( self, filter=None ):
        return [ self.methods, self.common ]


class ZObject:

    manage_options=(
        {'label': 'Methods', 'action' :'propertysheets/methods/manage',
         'help':('OFSP','ZClass_Methods.stx')},
        {'label': 'Basic', 'action' :'propertysheets/basic/manage',
         'help':('OFSP','ZClass_Basic.stx')},
        {'label': 'Views', 'action' :'propertysheets/views/manage',
         'help':('OFSP','ZClass_Views.stx')},
        {'label': 'Property Sheets', 'action' :'propertysheets/common/manage',
         'help':('OFSP','ZClass_Property-Sheets.stx')},
        {'label': 'Permissions',
         'action' :'propertysheets/permissions/manage',
         'help':('OFSP','ZClass_Permissions.stx')},
        {'label': 'Define Permissions', 'action' :'manage_access',
         'help':('OFSP','Security_Define-Permissions.stx')},
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

addDefault="""## Script (Python) "%(id)s_add"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=redirect=1
##title=%(title)s
##
# Add a new instance of the ZClass
request = context.REQUEST
instance = container.%(id)s.createInObjectManager(request['id'], request)

# *****************************************************************
# Perform any initialization of the new instance here.
# For example, to update a property sheet named "Basic" from the
# form values, uncomment the following line of code:
# instance.propertysheets.Basic.manage_editProperties(request)
# *****************************************************************

if redirect:
    # redirect to the management view of the instance's container
    request.RESPONSE.redirect(instance.aq_parent.absolute_url() + '/manage_main')
else:
    # If we aren't supposed to redirect (ie, we are called from a script)
    # then just return the ZClass instance to the caller
    return instance
"""
