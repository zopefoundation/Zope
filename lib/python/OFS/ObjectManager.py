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
"""Object Manager

$Id$
"""

import sys, fnmatch, copy, os, re
import marshal
from cgi import escape
from cStringIO import StringIO
from types import StringType, UnicodeType

import App.Management, Acquisition, Globals, Products
import App.FactoryDispatcher, Products
from Globals import DTMLFile, Persistent
from Globals import MessageDialog, default__class_init__
from Globals import REPLACEABLE, NOT_REPLACEABLE, UNIQUE
from webdav.NullResource import NullResource
from webdav.Collection import Collection
from Acquisition import aq_base
from webdav.Lockable import ResourceLockedError
from ZODB.POSException import ConflictError
import App.Common
from App.config import getConfiguration
from AccessControl import getSecurityManager
from AccessControl.ZopeSecurityPolicy import getRoles
from zLOG import LOG, ERROR
from zExceptions import BadRequest

from OFS.Traversable import Traversable
import CopySupport

# the name BadRequestException is relied upon by 3rd-party code
BadRequestException = BadRequest

import XMLExportImport
customImporters={
    XMLExportImport.magic: XMLExportImport.importXML,
    }

bad_id=re.compile(r'[^a-zA-Z0-9-_~,.$\(\)# @]').search

def checkValidId(self, id, allow_dup=0):
    # If allow_dup is false, an error will be raised if an object
    # with the given id already exists. If allow_dup is true,
    # only check that the id string contains no illegal chars;
    # check_valid_id() will be called again later with allow_dup
    # set to false before the object is added.

    if not id or not isinstance(id, StringType):
        if isinstance(id, UnicodeType): id = escape(id)
        raise BadRequest, ('Empty or invalid id specified', id)
    if bad_id(id) is not None:
        raise BadRequest, (
            'The id "%s" contains characters illegal in URLs.' % escape(id))
    if id in ('.', '..'): raise BadRequest, (
        'The id "%s" is invalid because it is not traversable.' % id)
    if id.startswith('_'): raise BadRequest, (
        'The id "%s" is invalid because it begins with an underscore.' % id)
    if id.startswith('aq_'): raise BadRequest, (
        'The id "%s" is invalid because it begins with "aq_".' % id)
    if id.endswith('__'): raise BadRequest, (
        'The id "%s" is invalid because it ends with two underscores.' % id)
    if not allow_dup:
        obj = getattr(self, id, None)
        if obj is not None:
            # An object by the given id exists either in this
            # ObjectManager or in the acquisition path.
            flags = getattr(obj, '__replaceable__', NOT_REPLACEABLE)
            if hasattr(aq_base(self), id):
                # The object is located in this ObjectManager.
                if not flags & REPLACEABLE:
                    raise BadRequest, (
                        'The id "%s" is invalid - it is already in use.' % id)
                # else the object is replaceable even if the UNIQUE
                # flag is set.
            elif flags & UNIQUE:
                raise BadRequest, ('The id "%s" is reserved.' % id)
    if id == 'REQUEST':
        raise BadRequest, 'REQUEST is a reserved name.'
    if '/' in id:
        raise BadRequest, (
            'The id "%s" contains characters illegal in URLs.' % id)


class BeforeDeleteException(Exception):

    pass # raise to veto deletion


class BreakoutException(Exception):

    pass  # raised to break out of loops


_marker=[]


class ObjectManager(
    CopySupport.CopyContainer,
    App.Management.Navigation,
    App.Management.Tabs,
    Acquisition.Implicit,
    Persistent,
    Collection,
    Traversable,
    ):

    """Generic object manager

    This class provides core behavior for collections of heterogeneous objects.
    """

    __ac_permissions__=(
        ('View management screens', ('manage_main',)),
        ('Access contents information',
         ('objectIds', 'objectValues', 'objectItems',''),
         ('Anonymous', 'Manager'),
         ),
        ('Delete objects',     ('manage_delObjects',)),
        ('FTP access',         ('manage_FTPstat','manage_FTPlist')),
        ('Import/Export objects',
         ('manage_importObject','manage_importExportForm',
          'manage_exportObject')
         ),
    )


    meta_type = 'Object Manager'

    meta_types=() # Sub-object types that are specific to this object

    _objects = ()

    manage_main=DTMLFile('dtml/main', globals())
    manage_index_main=DTMLFile('dtml/index_main', globals())

    manage_options=(
        {'label':'Contents', 'action':'manage_main',
         'help':('OFSP','ObjectManager_Contents.stx')},
        )

    isAnObjectManager=1

    isPrincipiaFolderish=1

    has_order_support = 0 # See OrderSupport.py

    def __class_init__(self):
        try:    mt=list(self.meta_types)
        except: mt=[]
        for b in self.__bases__:
            try:
                for t in b.meta_types:
                    if t not in mt: mt.append(t)
            except: pass
        mt.sort()
        self.meta_types=tuple(mt)

        default__class_init__(self)

    def all_meta_types(self, interfaces=None):
        # A list of products registered elsewhere
        external_candidates = []

        # Look at _product_meta_types, if there is one
        _pmt=()
        if hasattr(self, '_product_meta_types'): _pmt=self._product_meta_types
        elif hasattr(self, 'aq_acquire'):
            try: _pmt=self.aq_acquire('_product_meta_types')
            except:  pass
        external_candidates.extend(list(_pmt))

        # Look at all globally visible meta types.
        for entry in Products.meta_types:
            if ( (interfaces is not None) or (entry.get("visibility", None)=="Global") ):
                external_candidates.append(entry)

        # Filter the list of external candidates based on the
        # specified interface constraint
        if interfaces is None:
            interface_constrained_meta_types = external_candidates
        else:
            interface_constrained_meta_types = []
            for entry in external_candidates:
                try:
                    eil = entry.get('interfaces',None)
                    if eil is not None:
                        for ei in eil:
                            for i in interfaces:
                                if ei is i or ei.extends(i):
                                    interface_constrained_meta_types.append(entry)
                                    raise BreakoutException # only append 1ce
                except BreakoutException:
                    pass

        # Meta types specified by this instance are not checked against the
        # interface constraint. This is as it always has been, but Im not
        # sure it is correct.
        interface_constrained_meta_types.extend(list(self.meta_types))

        # Filter the list based on each meta-types's container_filter
        meta_types = []
        for entry in interface_constrained_meta_types:
            container_filter = entry.get('container_filter',None)
            if container_filter is None:
                meta_types.append(entry)
            else:
                if container_filter(self):
                    meta_types.append(entry)

        return meta_types

    def _subobject_permissions(self):
        return (Products.__ac_permissions__+
                self.aq_acquire('_getProductRegistryData')('ac_permissions')
                )

    def filtered_meta_types(self, user=None):
        # Return a list of the types for which the user has
        # adequate permission to add that type of object.
        user=getSecurityManager().getUser()
        meta_types=[]
        if callable(self.all_meta_types):
            all=self.all_meta_types()
        else:
            all=self.all_meta_types
        for meta_type in all:
            if meta_type.has_key('permission'):
                if user.has_permission(meta_type['permission'],self):
                    meta_types.append(meta_type)
            else:
                meta_types.append(meta_type)
        return meta_types

    _checkId = checkValidId

    def _setOb(self, id, object):
        setattr(self, id, object)

    def _delOb(self, id):
        delattr(self, id)

    def _getOb(self, id, default=_marker):
        # FIXME: what we really need to do here is ensure that only
        # sub-items are returned. That could have a measurable hit
        # on performance as things are currently implemented, so for
        # the moment we just make sure not to expose private attrs.
        if id[:1] != '_' and hasattr(aq_base(self), id):
            return getattr(self, id)
        if default is _marker:
            raise AttributeError, id
        return default

    def hasObject(self, id):
        """Indicate whether the folder has an item by ID.

        This doesn't try to be more intelligent than _getOb, and doesn't
        consult _objects (for performance reasons). The common use case
        is to check that an object does *not* exist.
        """
        if (id in ('.', '..') or
            id.startswith('_') or
            id.startswith('aq_') or
            id.endswith('__')):
            return False
        return getattr(aq_base(self), id, None) is not None

    def _setObject(self, id, object, roles=None, user=None, set_owner=1):
        v=self._checkId(id)
        if v is not None: id=v
        try:    t=object.meta_type
        except: t=None

        # If an object by the given id already exists, remove it.
        for object_info in self._objects:
            if object_info['id'] == id:
                self._delObject(id)
                break

        self._objects=self._objects+({'id':id,'meta_type':t},)
        self._setOb(id,object)
        object=self._getOb(id)

        if set_owner:
            object.manage_fixupOwnershipAfterAdd()

            # Try to give user the local role "Owner", but only if
            # no local roles have been set on the object yet.
            if hasattr(object, '__ac_local_roles__'):
                if object.__ac_local_roles__ is None:
                    user=getSecurityManager().getUser()
                    if user is not None:
                        userid=user.getId()
                        if userid is not None:
                            object.manage_setLocalRoles(userid, ['Owner'])

        object.manage_afterAdd(object, self)
        return id

    def manage_afterAdd(self, item, container):
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            if hasattr(aq_base(object), 'manage_afterAdd'):
                object.manage_afterAdd(item, container)
            if s is None: object._p_deactivate()

    def manage_afterClone(self, item):
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            if hasattr(aq_base(object), 'manage_afterClone'):
                object.manage_afterClone(item)
            if s is None: object._p_deactivate()

    def manage_beforeDelete(self, item, container):
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            try:
                if hasattr(aq_base(object), 'manage_beforeDelete'):
                    object.manage_beforeDelete(item, container)
            except BeforeDeleteException, ob:
                raise
            except ConflictError:
                raise
            except:
                LOG('Zope',ERROR,'manage_beforeDelete() threw',
                    error=sys.exc_info())
                # In debug mode when non-Manager, let exceptions propagate.
                if getConfiguration().debug_mode:
                    if not getSecurityManager().getUser().has_role('Manager'):
                        raise
            if s is None: object._p_deactivate()

    def _delObject(self, id, dp=1):
        object=self._getOb(id)
        try:
            object.manage_beforeDelete(object, self)
        except BeforeDeleteException, ob:
            raise
        except ConflictError:
            raise
        except:
            LOG('Zope', ERROR, '_delObject() threw',
                error=sys.exc_info())
            # In debug mode when non-Manager, let exceptions propagate.
            if getConfiguration().debug_mode:
                if not getSecurityManager().getUser().has_role('Manager'):
                    raise
        self._objects=tuple(filter(lambda i,n=id: i['id']!=n, self._objects))
        self._delOb(id)

        # Indicate to the object that it has been deleted. This is
        # necessary for object DB mount points. Note that we have to
        # tolerate failure here because the object being deleted could
        # be a Broken object, and it is not possible to set attributes
        # on Broken objects.
        try:    object._v__object_deleted__ = 1
        except: pass

    def objectIds(self, spec=None):
        # Returns a list of subobject ids of the current object.
        # If 'spec' is specified, returns objects whose meta_type
        # matches 'spec'.
        if spec is not None:
            if type(spec)==type('s'):
                spec=[spec]
            set=[]
            for ob in self._objects:
                if ob['meta_type'] in spec:
                    set.append(ob['id'])
            return set
        return [ o['id']  for o in self._objects ]

    def objectValues(self, spec=None):
        # Returns a list of actual subobjects of the current object.
        # If 'spec' is specified, returns only objects whose meta_type
        # match 'spec'.
        return [ self._getOb(id) for id in self.objectIds(spec) ]

    def objectItems(self, spec=None):
        # Returns a list of (id, subobject) tuples of the current object.
        # If 'spec' is specified, returns only objects whose meta_type match
        # 'spec'
        return [ (id, self._getOb(id)) for id in self.objectIds(spec) ]

    def objectMap(self):
        # Return a tuple of mappings containing subobject meta-data
        return tuple(map(lambda dict: dict.copy(), self._objects))

    def objectIds_d(self, t=None):
        if hasattr(self, '_reserved_names'): n=self._reserved_names
        else: n=()
        if not n: return self.objectIds(t)
        r=[]
        a=r.append
        for id in self.objectIds(t):
            if id not in n: a(id)
        return r

    def objectValues_d(self, t=None):
        return map(self._getOb, self.objectIds_d(t))

    def objectItems_d(self, t=None):
        r=[]
        a=r.append
        g=self._getOb
        for id in self.objectIds_d(t): a((id, g(id)))
        return r

    def objectMap_d(self, t=None):
        if hasattr(self, '_reserved_names'): n=self._reserved_names
        else: n=()
        if not n: return self._objects
        r=[]
        a=r.append
        for d in self._objects:
            if d['id'] not in n: a(d.copy())
        return r

    def superValues(self, t):
        # Return all of the objects of a given type located in
        # this object and containing objects.
        if type(t)==type('s'): t=(t,)
        obj=self
        seen={}
        vals=[]
        relativePhysicalPath = ()
        have=seen.has_key
        x=0
        while x < 100:
            if not hasattr(obj,'_getOb'): break
            get=obj._getOb
            if hasattr(obj,'_objects'):
                for i in obj._objects:
                    try:
                        id=i['id']
                        physicalPath = relativePhysicalPath + (id,)
                        if (not have(physicalPath)) and (i['meta_type'] in t):
                            vals.append(get(id))
                            seen[physicalPath]=1
                    except: pass

            if hasattr(obj,'aq_parent'):
                obj=obj.aq_parent
                relativePhysicalPath = ('..',) + relativePhysicalPath
            else:
                return vals
            x=x+1
        return vals


    manage_addProduct=App.FactoryDispatcher.ProductDispatcher()

    def manage_delObjects(self, ids=[], REQUEST=None):
        """Delete a subordinate object

        The objects specified in 'ids' get deleted.
        """
        if type(ids) is type(''): ids=[ids]
        if not ids:
            return MessageDialog(title='No items specified',
                   message='No items were specified!',
                   action ='./manage_main',)
        try:    p=self._reserved_names
        except: p=()
        for n in ids:
            if n in p:
                return MessageDialog(title='Not Deletable',
                       message='<EM>%s</EM> cannot be deleted.' % escape(n),
                       action ='./manage_main',)
        while ids:
            id=ids[-1]
            v=self._getOb(id, self)

            if v.wl_isLocked():
                raise ResourceLockedError, (
                    'Object "%s" is locked via WebDAV' % v.getId())

            if v is self:
                raise BadRequest, '%s does not exist' % escape(ids[-1])
            self._delObject(id)
            del ids[-1]
        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1)


    def tpValues(self):
        # Return a list of subobjects, used by tree tag.
        r=[]
        if hasattr(aq_base(self), 'tree_ids'):
            tree_ids=self.tree_ids
            try:   tree_ids=list(tree_ids)
            except TypeError:
                pass
            if hasattr(tree_ids, 'sort'):
                tree_ids.sort()
            for id in tree_ids:
                if hasattr(self, id):
                    r.append(self._getOb(id))
        else:
            obj_ids=self.objectIds()
            obj_ids.sort()
            for id in obj_ids:
                o=self._getOb(id)
                if hasattr(aq_base(o), 'isPrincipiaFolderish') and \
                   o.isPrincipiaFolderish:
                    r.append(o)
        return r

    def manage_exportObject(self, id='', download=None, toxml=None,
                            RESPONSE=None,REQUEST=None):
        """Exports an object to a file and returns that file."""
        if not id:
            # can't use getId() here (breaks on "old" exported objects)
            id=self.id
            if hasattr(id, 'im_func'): id=id()
            ob=self
        else: ob=self._getOb(id)

        suffix=toxml and 'xml' or 'zexp'

        if download:
            f=StringIO()
            if toxml: XMLExportImport.exportXML(ob._p_jar, ob._p_oid, f)
            else:     ob._p_jar.exportFile(ob._p_oid, f)
            if RESPONSE is not None:
                RESPONSE.setHeader('Content-type','application/data')
                RESPONSE.setHeader('Content-Disposition',
                                   'inline;filename=%s.%s' % (id, suffix))
            return f.getvalue()

        cfg = getConfiguration()
        f = os.path.join(cfg.clienthome, '%s.%s' % (id, suffix))
        if toxml:
            XMLExportImport.exportXML(ob._p_jar, ob._p_oid, f)
        else:
            ob._p_jar.exportFile(ob._p_oid, f)

        if REQUEST is not None:
            return self.manage_main(self, REQUEST,
                manage_tabs_message=
                '<em>%s</em> successfully exported to <em>%s</em>' % (id,f),
                title = 'Object exported')


    manage_importExportForm=DTMLFile('dtml/importExport',globals())

    def manage_importObject(self, file, REQUEST=None, set_owner=1):
        """Import an object from a file"""
        dirname, file=os.path.split(file)
        if dirname:
            raise BadRequest, 'Invalid file name %s' % escape(file)

        cfg = getConfiguration()
        for impath in (cfg.instancehome, cfg.zopehome):
            filepath = os.path.join(impath, 'import', file)
            if os.path.exists(filepath):
                break
        else:
            raise BadRequest, 'File does not exist: %s' % escape(file)

        self._importObjectFromFile(filepath, verify=not not REQUEST,
                                   set_owner=set_owner)

        if REQUEST is not None:
            return self.manage_main(
                self, REQUEST,
                manage_tabs_message='<em>%s</em> successfully imported' % id,
                title='Object imported',
                update_menu=1)

    def _importObjectFromFile(self, filepath, verify=1, set_owner=1):
        # locate a valid connection
        connection=self._p_jar
        obj=self

        while connection is None:
            obj=obj.aq_parent
            connection=obj._p_jar
        ob=connection.importFile(
            filepath, customImporters=customImporters)
        if verify: self._verifyObjectPaste(ob, validate_src=0)
        id=ob.id
        if hasattr(id, 'im_func'): id=id()
        self._setObject(id, ob, set_owner=set_owner)

        # try to make ownership implicit if possible in the context
        # that the object was imported into.
        ob=self._getOb(id)
        ob.manage_changeOwnershipType(explicit=0)

    def list_imports(self):
        listing = []
        cfg = getConfiguration()
        paths = [cfg.zopehome]
        if not cfg.instancehome in paths:
            paths.append(cfg.instancehome)
        for impath in paths:
            directory = os.path.join(impath, 'import')
            listing += [f for f in os.listdir(directory) 
                        if f.endswith('.zexp') or f.endswith('.xml')]
        return listing

    # FTP support methods

    def manage_FTPlist(self, REQUEST):
        """Directory listing for FTP.
        """
        out=()

        # check to see if we are being acquiring or not
        ob=self
        while 1:
            if App.Common.is_acquired(ob):
                raise ValueError('FTP List not supported on acquired objects')
            if not hasattr(ob,'aq_parent'):
                break
            ob=ob.aq_parent

        files = list(self.objectItems())

        # recursive ride through all subfolders (ls -R) (ajung)

        if REQUEST.environ.get('FTP_RECURSIVE',0) == 1:

            all_files = copy.copy(files)
            for f in files:
                if hasattr(aq_base(f[1]), 'isPrincipiaFolderish') and f[1].isPrincipiaFolderish:
                    all_files.extend(findChildren(f[1]))
            files = all_files

        # Perform globbing on list of files (ajung)

        globbing = REQUEST.environ.get('GLOBBING','')
        if globbing :
            files = filter(lambda x,g=globbing: fnmatch.fnmatch(x[0],g), files)

        files.sort()

        if not (hasattr(self,'isTopLevelPrincipiaApplicationObject') and
                self.isTopLevelPrincipiaApplicationObject):
            files.insert(0,('..',self.aq_parent))
        files.insert(0, ('.', self))
        for k,v in files:
            # Note that we have to tolerate failure here, because
            # Broken objects won't stat correctly. If an object fails
            # to be able to stat itself, we will ignore it, but log
            # the error.
            try:
                stat=marshal.loads(v.manage_FTPstat(REQUEST))
            except:
                LOG("FTP", ERROR, "Failed to stat file '%s'" % k,
                    error=sys.exc_info())
                stat=None
            if stat is not None:
                out=out+((k,stat),)
        return marshal.dumps(out)

    def manage_hasId(self, REQUEST):
        """ check if the folder has an object with REQUEST['id'] """

        if not REQUEST['id'] in self.objectIds():
            raise KeyError(REQUEST['id'])

    def manage_FTPstat(self,REQUEST):
        """Psuedo stat, used by FTP for directory listings.
        """
        mode=0040000
        from AccessControl.User import nobody
        # check to see if we are acquiring our objectValues or not
        if not (len(REQUEST.PARENTS) > 1 and
                self.objectValues() == REQUEST.PARENTS[1].objectValues()):
            try:
                if getSecurityManager().validate(
                    None, self, 'manage_FTPlist', self.manage_FTPlist
                    ):
                    mode=mode | 0770
            except: pass

            if nobody.allowed(
                self,
                getRoles(self, 'manage_FTPlist', self.manage_FTPlist, ())):
                mode=mode | 0007
        mtime=self.bobobase_modification_time().timeTime()
        # get owner and group
        owner=group='Zope'
        for user, roles in self.get_local_roles():
            if 'Owner' in roles:
                owner=user
                break
        return marshal.dumps((mode,0,0,1,owner,group,0,mtime,mtime,mtime))

    def __getitem__(self, key):
        v=self._getOb(key, None)
        if v is not None: return v
        if hasattr(self, 'REQUEST'):
            request=self.REQUEST
            method=request.get('REQUEST_METHOD', 'GET')
            if request.maybe_webdav_client and not method in ('GET', 'POST'):
                return NullResource(self, key, request).__of__(self)
        raise KeyError, key


def findChildren(obj,dirname=''):
    """ recursive walk through the object hierarchy to
    find all children of an object (ajung)
    """

    lst = []
    for name, child in obj.objectItems():
        if hasattr(aq_base(child), 'isPrincipiaFolderish') and child.isPrincipiaFolderish:
            lst.extend(findChildren(child, dirname + obj.id + '/'))
        else:
            lst.append((dirname + obj.id + "/" + name, child))

    return lst


class IFAwareObjectManager:

    def all_meta_types(self, interfaces=None):

        if interfaces is None:
            if hasattr(self, '_product_interfaces'):
                interfaces=self._product_interfaces
            elif hasattr(self, 'aq_acquire'):
                try: interfaces=self.aq_acquire('_product_interfaces')
                except: pass    # Bleah generic pass is bad

        return ObjectManager.all_meta_types(self, interfaces)

Globals.default__class_init__(ObjectManager)
