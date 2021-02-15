##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Object Manager
"""

import html
import os
import re
from io import BytesIO
from logging import getLogger
from operator import itemgetter
from urllib.parse import quote

import zope.sequencesort
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.class_init import InitializeClass
from AccessControl.Permission import getPermissions
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import delete_objects
from AccessControl.Permissions import ftp_access
from AccessControl.Permissions import import_export_objects
from AccessControl.Permissions import view_management_screens
from Acquisition import Implicit
from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_parent
from App.config import getConfiguration
from App.FactoryDispatcher import ProductDispatcher
from App.Management import Navigation
from App.Management import Tabs
from App.special_dtml import DTMLFile
from DateTime import DateTime
from DateTime.interfaces import DateTimeError
from OFS.CopySupport import CopyContainer
from OFS.event import ObjectWillBeAddedEvent
from OFS.event import ObjectWillBeRemovedEvent
from OFS.interfaces import IObjectManager
from OFS.Lockable import LockableItem
from OFS.subscribers import compatibilityCall
from OFS.Traversable import Traversable
from Persistence import Persistent
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from webdav.Collection import Collection
from webdav.NullResource import NullResource
from zExceptions import BadRequest
from zExceptions import ResourceLockedError
from zope.container.contained import notifyContainerModified
from zope.event import notify
from zope.interface import implementer
from zope.interface.interfaces import ComponentLookupError
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectRemovedEvent
from ZPublisher.HTTPResponse import make_content_disposition


# Constants: __replaceable__ flags:
NOT_REPLACEABLE = 0
REPLACEABLE = 1
UNIQUE = 2

LOG = getLogger('ObjectManager')
CONFIG = getConfiguration()

# the name BadRequestException is relied upon by 3rd-party code
BadRequestException = BadRequest

# We want a regex to define the lower ascii control bytes and DEL as bad.
# Additionally we want to exclude angle brackets and ampersand as they mess
# with the url-quoting.
bad_id = re.compile(r'[\x00-\x1F\x7F<>&]').search


def checkValidId(self, id, allow_dup=0):
    # If allow_dup is false, an error will be raised if an object
    # with the given id already exists. If allow_dup is true,
    # only check that the id string contains no illegal chars;
    # check_valid_id() will be called again later with allow_dup
    # set to false before the object is added.
    if not id or not isinstance(id, str):
        if isinstance(id, str):
            id = html.escape(id, True)
        raise BadRequest('Empty or invalid id specified', id)
    if bad_id(id) is not None:
        raise BadRequest(
            'The id "%s" contains characters '
            'illegal in URLs.' % html.escape(id, True))
    if id in ('.', '..'):
        raise BadRequest(
            'The id "%s" is invalid because it is not traversable.' % id)
    if id.startswith('_'):
        raise BadRequest(
            'The id "%s" is invalid because it '
            'begins with an underscore.' % id)
    if id.startswith('aq_'):
        raise BadRequest(
            'The id "%s" is invalid because it begins with "aq_".' % id)
    if id.endswith('__'):
        raise BadRequest(
            'The id "%s" is invalid because it '
            'ends with two underscores.' % id)
    if id.startswith('@@') or id.startswith('++'):
        raise BadRequest(
            'The id "%s" is invalid because it starts with characters '
            'reserved for Zope views lookup.' % id)
    if not allow_dup:
        obj = getattr(self, id, None)
        if obj is not None:
            # An object by the given id exists either in this
            # ObjectManager or in the acquisition path.
            flags = getattr(obj, '__replaceable__', NOT_REPLACEABLE)
            if hasattr(aq_base(self), id):
                # The object is located in this ObjectManager.
                if not flags & REPLACEABLE:
                    raise BadRequest(
                        'The id "%s" is invalid - it is already in use.' % id)
                # else the object is replaceable even if the UNIQUE
                # flag is set.
            elif flags & UNIQUE:
                raise BadRequest('The id "%s" is reserved.' % id)
    if id == 'REQUEST':
        raise BadRequest('REQUEST is a reserved name.')
    if '/' in id:
        raise BadRequest(
            'The id "%s" contains characters illegal in URLs.' % id)


class BeforeDeleteException(Exception):
    pass  # raise to veto deletion


class BreakoutException(Exception):
    pass  # raised to break out of loops


_marker = []


@implementer(IObjectManager)
class ObjectManager(
    CopyContainer,
    Navigation,
    Tabs,
    Implicit,
    Persistent,
    Collection,
    LockableItem,
    Traversable
):
    """Generic object manager

    This class provides core behavior for collections of heterogeneous objects.
    """

    security = ClassSecurityInfo()
    security.declareObjectProtected(access_contents_information)
    security.setPermissionDefault(access_contents_information,
                                  ('Anonymous', 'Manager'))

    meta_type = 'Object Manager'

    meta_types = ()  # Sub-object types that are specific to this object

    _objects = ()

    security.declareProtected(view_management_screens, 'manage_main')  # NOQA: D001,E501
    manage_main = PageTemplateFile('zpt/main', globals())

    manage_index_main = DTMLFile('dtml/index_main', globals())

    manage_options = (
        {
            'label': 'Contents',
            'action': 'manage_main',
        },
    )

    isAnObjectManager = 1
    isPrincipiaFolderish = 1
    has_order_support = 0  # See OrderSupport.py

    # IPossibleSite API
    _components = None

    @security.public
    def getSiteManager(self):
        if self._components is None:
            raise ComponentLookupError('No component registry defined.')
        return self._components

    @security.protected('Manage Site')
    def setSiteManager(self, components):
        self._components = components

    def __class_init__(self):
        try:
            mt = list(self.meta_types)
        except Exception:
            mt = []
        for b in self.__bases__:
            try:
                for t in b.meta_types:
                    if t not in mt:
                        mt.append(t)
            except Exception:
                pass
        self.meta_types = tuple(sorted(mt, key=itemgetter('name')))

        InitializeClass(self)

    def all_meta_types(self, interfaces=None):
        # A list of products registered elsewhere
        import Products
        external_candidates = []

        # Look at all globally visible meta types.
        for entry in getattr(Products, 'meta_types', ()):
            if interfaces is not None or \
               entry.get("visibility", None) == "Global":
                external_candidates.append(entry)

        # Filter the list of external candidates based on the
        # specified interface constraint
        if interfaces is None:
            interface_constrained_meta_types = external_candidates
        else:
            interface_constrained_meta_types = icmt = []
            for entry in external_candidates:
                try:
                    eil = entry.get('interfaces', None)
                    if eil is not None:
                        for ei in eil:
                            for i in interfaces:
                                if ei is i or ei.extends(i):
                                    icmt.append(entry)
                                    raise BreakoutException  # only append 1ce
                except BreakoutException:
                    pass

        # Meta types specified by this instance are not checked against the
        # interface constraint. This is as it always has been, but Im not
        # sure it is correct.
        interface_constrained_meta_types.extend(list(self.meta_types))

        # Filter the list based on each meta-types's container_filter
        meta_types = []
        for entry in interface_constrained_meta_types:
            container_filter = entry.get('container_filter', None)
            if container_filter is None:
                meta_types.append(entry)
            else:
                if container_filter(self):
                    meta_types.append(entry)

        # Synthesize a new key into each item that decides whether to show
        # the modal add dialog in the Zope 4 ZMI
        for mt in meta_types:
            want_modal = getattr(mt.get('instance', None),
                                 'zmi_show_add_dialog', True)
            mt['zmi_show_add_dialog'] = 'modal' if want_modal else ''

        return meta_types

    def _subobject_permissions(self):
        return getPermissions()

    def filtered_meta_types(self, user=None):
        # Return a list of the types for which the user has
        # adequate permission to add that type of object.
        sm = getSecurityManager()
        meta_types = []
        if callable(self.all_meta_types):
            all = self.all_meta_types()
        else:
            all = self.all_meta_types
        for meta_type in all:
            if 'permission' in meta_type:
                if sm.checkPermission(meta_type['permission'], self):
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
            raise AttributeError(id)
        return default

    @security.protected(access_contents_information)
    def hasObject(self, id):
        # Indicate whether the folder has an item by ID.
        #
        # This doesn't try to be more intelligent than _getOb, and doesn't
        # consult _objects (for performance reasons). The common use case
        # is to check that an object does *not* exist.
        if id in ('.', '..') or \
           id.startswith('_') or \
           id.startswith('aq_') or \
           id.endswith('__'):
            return False
        return getattr(aq_base(self), id, None) is not None

    def _setObject(self, id, object, roles=None, user=None, set_owner=1,
                   suppress_events=False):
        """Set an object into this container.

        Also sends IObjectWillBeAddedEvent and IObjectAddedEvent.
        """
        ob = object  # better name, keep original function signature
        v = self._checkId(id)
        if v is not None:
            id = v
        t = getattr(ob, 'meta_type', None)

        # If an object by the given id already exists, remove it.
        for object_info in self._objects:
            if object_info['id'] == id:
                self._delObject(id)
                break

        if not suppress_events:
            notify(ObjectWillBeAddedEvent(ob, self, id))

        self._objects = self._objects + ({'id': id, 'meta_type': t},)
        self._setOb(id, ob)
        ob = self._getOb(id)

        if set_owner:
            # TODO: eventify manage_fixupOwnershipAfterAdd
            # This will be called for a copy/clone, or a normal _setObject.
            ob.manage_fixupOwnershipAfterAdd()

            # Try to give user the local role "Owner", but only if
            # no local roles have been set on the object yet.
            if getattr(ob, '__ac_local_roles__', _marker) is None:
                user = getSecurityManager().getUser()
                if user is not None:
                    userid = user.getId()
                    if userid is not None:
                        ob.manage_setLocalRoles(userid, ['Owner'])

        if not suppress_events:
            notify(ObjectAddedEvent(ob, self, id))
            notifyContainerModified(self)

        compatibilityCall('manage_afterAdd', ob, ob, self)

        return id

    def manage_afterAdd(self, item, container):
        # Don't do recursion anymore, a subscriber does that.
        pass
    manage_afterAdd.__five_method__ = True

    def manage_afterClone(self, item):
        # Don't do recursion anymore, a subscriber does that.
        pass
    manage_afterClone.__five_method__ = True

    def manage_beforeDelete(self, item, container):
        # Don't do recursion anymore, a subscriber does that.
        pass
    manage_beforeDelete.__five_method__ = True

    def _delObject(self, id, dp=1, suppress_events=False):
        """Delete an object from this container.

        Also sends IObjectWillBeRemovedEvent and IObjectRemovedEvent.
        """
        ob = self._getOb(id)

        compatibilityCall('manage_beforeDelete', ob, ob, self)

        if not suppress_events:
            notify(ObjectWillBeRemovedEvent(ob, self, id))

        self._objects = tuple([i for i in self._objects
                               if i['id'] != id])
        self._delOb(id)

        # Indicate to the object that it has been deleted. This is
        # necessary for object DB mount points. Note that we have to
        # tolerate failure here because the object being deleted could
        # be a Broken object, and it is not possible to set attributes
        # on Broken objects.
        try:
            ob._v__object_deleted__ = 1
        except Exception:
            pass

        if not suppress_events:
            notify(ObjectRemovedEvent(ob, self, id))
            notifyContainerModified(self)

    @security.protected(access_contents_information)
    def objectIds(self, spec=None):
        # Returns a list of subobject ids of the current object.
        # If 'spec' is specified, returns objects whose meta_type
        # matches 'spec'.
        if spec is not None:
            if isinstance(spec, str):
                spec = [spec]
            set = []
            for ob in self._objects:
                if ob['meta_type'] in spec:
                    set.append(ob['id'])
            return set
        return [o['id'] for o in self._objects]

    @security.protected(access_contents_information)
    def objectValues(self, spec=None):
        # Returns a list of actual subobjects of the current object.
        # If 'spec' is specified, returns only objects whose meta_type
        # match 'spec'.
        return [self._getOb(id) for id in self.objectIds(spec)]

    @security.protected(access_contents_information)
    def objectItems(self, spec=None):
        # Returns a list of (id, subobject) tuples of the current object.
        # If 'spec' is specified, returns only objects whose meta_type match
        # 'spec'
        return [(id, self._getOb(id)) for id in self.objectIds(spec)]

    def objectMap(self):
        # Return a tuple of mappings containing subobject meta-data
        return tuple(d.copy() for d in self._objects)

    @security.protected(access_contents_information)
    def objectIds_d(self, t=None):
        if hasattr(self, '_reserved_names'):
            n = self._reserved_names
        else:
            n = ()
        if not n:
            return self.objectIds(t)
        r = []
        for id in self.objectIds(t):
            if id not in n:
                r.append(id)
        return r

    @security.protected(access_contents_information)
    def objectValues_d(self, t=None):
        return list(map(self._getOb, self.objectIds_d(t)))

    @security.protected(access_contents_information)
    def objectItems_d(self, t=None):
        r = []
        for id in self.objectIds_d(t):
            r.append((id, self._getOb(id)))
        return r

    @security.protected(access_contents_information)
    def objectMap_d(self, t=None):
        if hasattr(self, '_reserved_names'):
            n = self._reserved_names
        else:
            n = ()
        if not n:
            return self._objects
        r = []
        for d in self._objects:
            if d['id'] not in n:
                r.append(d.copy())
        return r

    @security.protected(access_contents_information)
    def superValues(self, t):
        # Return all of the objects of a given type located in
        # this object and containing objects.
        if isinstance(t, str):
            t = (t,)
        obj = self
        seen = {}
        vals = []
        relativePhysicalPath = ()
        x = 0
        while x < 100:
            if not hasattr(obj, '_getOb'):
                break
            get = obj._getOb
            if hasattr(obj, '_objects'):
                for i in obj._objects:
                    try:
                        id = i['id']
                        physicalPath = relativePhysicalPath + (id,)
                        if physicalPath not in seen and i['meta_type'] in t:
                            vals.append(get(id))
                            seen[physicalPath] = 1
                    except Exception:
                        pass

            if hasattr(obj, '__parent__'):
                obj = aq_parent(obj)
                relativePhysicalPath = ('..',) + relativePhysicalPath
            else:
                return vals
            x = x + 1
        return vals

    manage_addProduct = ProductDispatcher()

    @security.protected(delete_objects)
    def manage_delObjects(self, ids=[], REQUEST=None):
        """Delete a subordinate object

        The objects specified in 'ids' get deleted.
        """
        if isinstance(ids, str):
            ids = [ids]
        if not ids:
            raise BadRequest('No items specified')
        try:
            p = self._reserved_names
        except Exception:
            p = ()
        for n in ids:
            if n in p:
                raise BadRequest('Not Deletable')
        while ids:
            id = ids[-1]
            v = self._getOb(id, self)

            try:
                if v.wl_isLocked():
                    raise ResourceLockedError(
                        'Object "%s" is locked.' % v.getId())
            except AttributeError:
                pass

            if v is self:
                raise BadRequest('%s does not exist' %
                                 html.escape(ids[-1], True))
            self._delObject(id)
            del ids[-1]
        if REQUEST is not None:
            return self.manage_main(self, REQUEST)

    @security.protected(access_contents_information)
    def tpValues(self):
        # Return a list of subobjects, used by tree tag.
        r = []
        if hasattr(aq_base(self), 'tree_ids'):
            tree_ids = self.tree_ids
            try:
                tree_ids = list(tree_ids)
            except TypeError:
                pass
            if hasattr(tree_ids, 'sort'):
                tree_ids.sort()
            for id in tree_ids:
                if hasattr(self, id):
                    r.append(self._getOb(id))
        else:
            obj_ids = self.objectIds()
            obj_ids.sort()
            for id in obj_ids:
                o = self._getOb(id)
                if hasattr(aq_base(o), 'isPrincipiaFolderish') and \
                   o.isPrincipiaFolderish:
                    r.append(o)
        return r

    @security.protected(import_export_objects)
    def manage_exportObject(
        self,
        id='',
        download=None,
        RESPONSE=None,
        REQUEST=None
    ):
        """Exports an object to a file and returns that file."""
        if not id:
            # can't use getId() here (breaks on "old" exported objects)
            id = self.id
            if getattr(id, '__func__', None) is not None:
                id = id()
            ob = self
        else:
            ob = self._getOb(id)

        suffix = 'zexp'

        if download:
            with BytesIO() as f:
                ob._p_jar.exportFile(ob._p_oid, f)
                result = f.getvalue()

            if RESPONSE is not None:
                RESPONSE.setHeader('Content-type', 'application/data')
                RESPONSE.setHeader(
                    'Content-Disposition',
                    make_content_disposition('inline', f'{id}.{suffix}')
                )
            return result

        f = os.path.join(CONFIG.clienthome, f'{id}.{suffix}')
        with open(f, 'w+b') as fd:
            ob._p_jar.exportFile(ob._p_oid, fd)

        if REQUEST is not None:
            return self.manage_main(
                self, REQUEST,
                manage_tabs_message=f'"{id}" successfully exported to "{f}"',
                title='Object exported'
            )

    security.declareProtected(import_export_objects, 'manage_importExportForm')  # NOQA: D001,E501
    manage_importExportForm = DTMLFile('dtml/importExport', globals())

    @security.protected(import_export_objects)
    def manage_importObject(self, file, REQUEST=None, set_owner=1,
                            suppress_events=False):
        """Import an object from a file"""
        dirname, file = os.path.split(file)
        if dirname:
            raise BadRequest('Invalid file name %s' % html.escape(file, True))

        for impath in self._getImportPaths():
            filepath = os.path.join(impath, 'import', file)
            if os.path.exists(filepath):
                break
        else:
            raise BadRequest(
                'File does not exist: %s' %
                html.escape(
                    file, True))

        imported = self._importObjectFromFile(
            filepath, verify=bool(REQUEST), set_owner=set_owner,
            suppress_events=suppress_events)
        getId = getattr(aq_base(imported), "getId", None)  # aq wrapped
        id = imported.getId() if getId is not None else imported.id
        if getattr(id, '__func__', None) is not None:
            id = id()

        if REQUEST is not None:
            return self.manage_main(
                self,
                REQUEST,
                manage_tabs_message='"%s" successfully imported' % id,
                title='Object imported',
                update_menu=1
            )

    def _importObjectFromFile(self, filepath, verify=1, set_owner=1,
                              suppress_events=False):
        # locate a valid connection
        connection = self._p_jar
        obj = self

        while connection is None:
            obj = aq_parent(obj)
            connection = obj._p_jar
        ob = connection.importFile(filepath)
        if verify:
            self._verifyObjectPaste(ob, validate_src=0)
        getId = getattr(ob, "getId", None)  # not acquisition wrapped
        id = getId() if getId is not None else ob.id
        if getattr(id, '__func__', None) is not None:
            id = id()
        self._setObject(id, ob, set_owner=set_owner,
                        suppress_events=suppress_events)

        # try to make ownership implicit if possible in the context
        # that the object was imported into.
        ob = self._getOb(id)
        ob.manage_changeOwnershipType(explicit=0)
        return ob

    def _getImportPaths(self):
        paths = []
        if CONFIG.instancehome not in paths:
            paths.append(CONFIG.instancehome)
        if CONFIG.clienthome not in paths:
            paths.append(CONFIG.clienthome)
        return paths

    def list_imports(self):
        listing = []
        for impath in self._getImportPaths():
            directory = os.path.join(impath, 'import')
            if not os.path.isdir(directory):
                continue
            listing += [f for f in os.listdir(directory)
                        if f.endswith('.zexp') or f.endswith('.xml')]
        listing.sort()
        return listing

    @security.protected(ftp_access)
    def manage_hasId(self, REQUEST):
        """Check if the folder has an object with REQUEST['id']."""
        # When this method will be removed, please also remove
        # `ftp_access` both from `AppendixA`from the Zope Developers
        # Book and from `AccessControl.Permissions`
        import warnings
        warnings.warn(
            "`ObjectManager.manage_hasId` is deprecated "
            "and will be removed in future.",
            DeprecationWarning)
        if not REQUEST['id'] in self.objectIds():
            raise KeyError(REQUEST['id'])

    def __delitem__(self, name):
        return self.manage_delObjects(ids=[name])

    def __getitem__(self, key):
        if key in self:
            return self._getOb(key, None)

        request = getattr(self, 'REQUEST', None)
        if not (isinstance(request, str) or request is None):
            method = request.get('REQUEST_METHOD', 'GET')
            if request.maybe_webdav_client and method not in ('GET', 'POST'):
                return NullResource(self, key, request).__of__(self)

        raise KeyError(key)

    def __setitem__(self, key, value):
        return self._setObject(key, value)

    def __contains__(self, name):
        for ob in self._objects:
            if name == ob['id']:
                return True

        return False

    def __iter__(self):
        return iter(self.objectIds())

    def __len__(self):
        return len(self.objectIds())

    def __bool__(self):
        return True

    @security.protected(access_contents_information)
    def get(self, key, default=None):
        if key in self:
            return self._getOb(key, default)
        return default

    @security.protected(access_contents_information)
    def keys(self):
        return self.objectIds()

    @security.protected(access_contents_information)
    def items(self):
        return self.objectItems()

    @security.protected(access_contents_information)
    def values(self):
        return self.objectValues()

    @security.protected(access_contents_information)
    def compute_size(self, ob):
        if hasattr(aq_base(ob), 'get_size'):
            ob_size = ob.get_size()
            if ob_size < 1024:
                return '1 KiB'
            elif ob_size > 1048576:
                return "{:0.02f} MiB".format(ob_size / 1048576.0)
            else:
                return "{:0.0f} KiB".format(ob_size / 1024.0)

    @security.protected(access_contents_information)
    def last_modified(self, ob):
        try:
            return DateTime(ob._p_mtime).strftime("%Y-%m-%d %H:%M")
        except (DateTimeError, AttributeError):
            return ''

    @security.protected(view_management_screens)
    def manage_get_sortedObjects(self, sortkey, revkey):
        '''
        Return dictionaries used for the management page, sorted by sortkey
        (which is 'id' or an attribute of the objects). The direction is
        determined by rkey, which can be 'asc' for ascending or 'desc' for
        descending.
        It returns a list of dictionaries, with keys 'id' and 'obj', where 'id'
        is the ID of the object as known by the parent and 'obj' is the child
        object.
        '''
        if sortkey not in ['position', 'title', 'meta_type', 'get_size',
                           '_p_mtime']:
            sortkey = 'id'

        items = []
        for id, obj in self.objectItems():
            item = {'id': id, 'quoted_id': quote(id), 'obj': obj}
            if sortkey not in ['id', 'position'] and hasattr(obj, sortkey):
                # add the attribute by which we need to sort
                item[sortkey] = getattr(obj, sortkey)
            items.append(item)

        if sortkey == 'position':
            # native ordering of Ordered Folders
            if revkey == 'desc':
                return list(reversed(items))
            else:
                return items

        if sortkey in ['id', 'title', 'meta_type']:
            sort_func = 'strcoll'
        else:
            sort_func = 'cmp'

        sorted_items = zope.sequencesort.sort(
            items,
            ((sortkey, sort_func, revkey), ),
            mapping=1
        )

        # remove the additional attribute
        return [
            {
                'id': item['id'],
                'quoted_id': item['quoted_id'],
                'obj': item['obj'],
            }
            for item in sorted_items
        ]

    @security.protected(view_management_screens)
    def getBookmarkableURLs(self):
        """ Helper method to expose a configuration flag """
        return getattr(CONFIG, 'zmi_bookmarkable_urls', True)

# Don't InitializeClass, there is a specific __class_init__ on ObjectManager
# InitializeClass(ObjectManager)


def findChildren(obj, dirname=''):
    """ recursive walk through the object hierarchy to
    find all children of an object (ajung)
    """

    lst = []
    for name, child in obj.objectItems():
        if hasattr(aq_base(child), 'isPrincipiaFolderish') and \
           child.isPrincipiaFolderish:
            lst.extend(findChildren(child, dirname + obj.getId() + '/'))
        else:
            lst.append((dirname + obj.getId() + "/" + name, child))

    return lst


class IFAwareObjectManager:

    def all_meta_types(self, interfaces=None):

        if interfaces is None:
            if hasattr(self, '_product_interfaces'):
                interfaces = self._product_interfaces
            elif hasattr(self, 'aq_acquire'):
                try:
                    interfaces = aq_acquire(self, '_product_interfaces')
                except Exception:
                    pass

        return ObjectManager.all_meta_types(self, interfaces)
