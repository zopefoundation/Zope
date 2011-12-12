##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""BTreeFolder2

$Id: BTreeFolder2.py,v 1.27 2004/03/17 22:49:25 urbanape Exp $
"""

from cgi import escape
from logging import getLogger
from random import randint
import sys
from urllib import quote

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import view_management_screens
from Acquisition import aq_base
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from BTrees.Length import Length
from BTrees.OIBTree import OIBTree
from BTrees.OIBTree import union
from BTrees.OOBTree import OOBTree
from OFS.event import ObjectWillBeAddedEvent
from OFS.event import ObjectWillBeRemovedEvent
from OFS.Folder import Folder
from OFS.ObjectManager import BadRequestException
from OFS.ObjectManager import BeforeDeleteException
from OFS.subscribers import compatibilityCall
from Persistence import Persistent
from Products.ZCatalog.Lazy import LazyMap
from ZODB.POSException import ConflictError
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectRemovedEvent
from zope.container.contained import notifyContainerModified


LOG = getLogger('BTreeFolder2')

manage_addBTreeFolderForm = DTMLFile('folderAdd', globals())

def manage_addBTreeFolder(dispatcher, id, title='', REQUEST=None):
    """Adds a new BTreeFolder object with id *id*.
    """
    id = str(id)
    ob = BTreeFolder2(id)
    ob.title = str(title)
    dispatcher._setObject(id, ob)
    ob = dispatcher._getOb(id)
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST, update_menu=1)


listtext0 = '''<select name="ids:list" multiple="multiple" size="%s">
'''
listtext1 = '''<option value="%s">%s</option>
'''
listtext2 = '''</select>
'''


_marker = []  # Create a new marker object.

MAX_UNIQUEID_ATTEMPTS = 1000

class ExhaustedUniqueIdsError (Exception):
    pass


class BTreeFolder2Base (Persistent):
    """Base for BTree-based folders.
    """

    security = ClassSecurityInfo()

    manage_options=(
        ({'label':'Contents', 'action':'manage_main',},
         ) + Folder.manage_options[1:]
        )

    security.declareProtected(view_management_screens,
                              'manage_main')
    manage_main = DTMLFile('contents', globals())

    _tree = None      # OOBTree: { id -> object }
    _count = None     # A BTrees.Length
    _v_nextid = 0     # The integer component of the next generated ID
    _mt_index = None  # OOBTree: { meta_type -> OIBTree: { id -> 1 } }
    title = ''


    def __init__(self, id=None):
        if id is not None:
            self.id = id
        self._initBTrees()

    def _initBTrees(self):
        self._tree = OOBTree()
        self._count = Length()
        self._mt_index = OOBTree()


    def _populateFromFolder(self, source):
        """Fill this folder with the contents of another folder.
        """
        for name in source.objectIds():
            value = source._getOb(name, None)
            if value is not None:
                self._setOb(name, aq_base(value))


    security.declareProtected(view_management_screens, 'manage_fixCount')
    def manage_fixCount(self):
        """Calls self._fixCount() and reports the result as text.
        """
        old, new = self._fixCount()
        path = '/'.join(self.getPhysicalPath())
        if old == new:
            return "No count mismatch detected in BTreeFolder2 at %s." % path
        else:
            return ("Fixed count mismatch in BTreeFolder2 at %s. "
                    "Count was %d; corrected to %d" % (path, old, new))


    def _fixCount(self):
        """Checks if the value of self._count disagrees with
        len(self.objectIds()). If so, corrects self._count. Returns the
        old and new count values. If old==new, no correction was
        performed.
        """
        old = self._count()
        new = len(self.objectIds())
        if old != new:
            self._count.set(new)
        return old, new


    security.declareProtected(view_management_screens, 'manage_cleanup')
    def manage_cleanup(self):
        """Calls self._cleanup() and reports the result as text.
        """
        v = self._cleanup()
        path = '/'.join(self.getPhysicalPath())
        if v:
            return "No damage detected in BTreeFolder2 at %s." % path
        else:
            return ("Fixed BTreeFolder2 at %s.  "
                    "See the log for more details." % path)


    def _cleanup(self):
        """Cleans up errors in the BTrees.

        Certain ZODB bugs have caused BTrees to become slightly insane.
        Fortunately, there is a way to clean up damaged BTrees that
        always seems to work: make a new BTree containing the items()
        of the old one.

        Returns 1 if no damage was detected, or 0 if damage was
        detected and fixed.
        """
        from BTrees.check import check
        path = '/'.join(self.getPhysicalPath())
        try:
            check(self._tree)
            for key in self._tree.keys():
                if not self._tree.has_key(key):
                    raise AssertionError(
                        "Missing value for key: %s" % repr(key))
            check(self._mt_index)
            for key, value in self._mt_index.items():
                if (not self._mt_index.has_key(key)
                    or self._mt_index[key] is not value):
                    raise AssertionError(
                        "Missing or incorrect meta_type index: %s"
                        % repr(key))
                check(value)
                for k in value.keys():
                    if not value.has_key(k):
                        raise AssertionError(
                            "Missing values for meta_type index: %s"
                            % repr(key))
            return 1
        except AssertionError:
            LOG.warn('Detected damage to %s. Fixing now.' % path,
                     exc_info=sys.exc_info())
            try:
                self._tree = OOBTree(self._tree)
                mt_index = OOBTree()
                for key, value in self._mt_index.items():
                    mt_index[key] = OIBTree(value)
                self._mt_index = mt_index
            except:
                LOG.error('Failed to fix %s.' % path,
                    exc_info=sys.exc_info())
                raise
            else:
                LOG.info('Fixed %s.' % path)
            return 0


    def _getOb(self, id, default=_marker):
        """Return the named object from the folder.
        """
        tree = self._tree
        if default is _marker:
            ob = tree[id]
            return ob.__of__(self)
        else:
            ob = tree.get(id, _marker)
            if ob is _marker:
                return default
            else:
                return ob.__of__(self)


    def _setOb(self, id, object):
        """Store the named object in the folder.
        """
        tree = self._tree
        if tree.has_key(id):
            raise KeyError('There is already an item named "%s".' % id)
        tree[id] = object
        self._count.change(1)
        # Update the meta type index.
        mti = self._mt_index
        meta_type = getattr(object, 'meta_type', None)
        if meta_type is not None:
            ids = mti.get(meta_type, None)
            if ids is None:
                ids = OIBTree()
                mti[meta_type] = ids
            ids[id] = 1


    def _delOb(self, id):
        """Remove the named object from the folder.
        """
        tree = self._tree
        meta_type = getattr(tree[id], 'meta_type', None)
        del tree[id]
        self._count.change(-1)
        # Update the meta type index.
        if meta_type is not None:
            mti = self._mt_index
            ids = mti.get(meta_type, None)
            if ids is not None and ids.has_key(id):
                del ids[id]
                if not ids:
                    # Removed the last object of this meta_type.
                    # Prune the index.
                    del mti[meta_type]


    security.declareProtected(view_management_screens, 'getBatchObjectListing')
    def getBatchObjectListing(self, REQUEST=None):
        """Return a structure for a page template to show the list of objects.
        """
        if REQUEST is None:
            REQUEST = {}
        pref_rows = int(REQUEST.get('dtpref_rows', 20))
        b_start = int(REQUEST.get('b_start', 1))
        b_count = int(REQUEST.get('b_count', 1000))
        b_end = b_start + b_count - 1
        url = self.absolute_url() + '/manage_main'
        idlist = self.objectIds()  # Pre-sorted.
        count = self.objectCount()

        if b_end < count:
            next_url = url + '?b_start=%d' % (b_start + b_count)
        else:
            b_end = count
            next_url = ''

        if b_start > 1:
            prev_url = url + '?b_start=%d' % max(b_start - b_count, 1)
        else:
            prev_url = ''

        formatted = []
        formatted.append(listtext0 % pref_rows)
        for i in range(b_start - 1, b_end):
            optID = escape(idlist[i])
            formatted.append(listtext1 % (escape(optID, quote=1), optID))
        formatted.append(listtext2)
        return {'b_start': b_start, 'b_end': b_end,
                'prev_batch_url': prev_url,
                'next_batch_url': next_url,
                'formatted_list': ''.join(formatted)}


    security.declareProtected(view_management_screens,
                              'manage_object_workspace')
    def manage_object_workspace(self, ids=(), REQUEST=None):
        '''Redirects to the workspace of the first object in
        the list.'''
        if ids and REQUEST is not None:
            REQUEST.RESPONSE.redirect(
                '%s/%s/manage_workspace' % (
                self.absolute_url(), quote(ids[0])))
        else:
            return self.manage_main(self, REQUEST)


    security.declareProtected(access_contents_information,
                              'tpValues')
    def tpValues(self):
        """Ensures the items don't show up in the left pane.
        """
        return ()


    security.declareProtected(access_contents_information,
                              'objectCount')
    def objectCount(self):
        """Returns the number of items in the folder."""
        return self._count()


    security.declareProtected(access_contents_information, 'has_key')
    def has_key(self, id):
        """Indicates whether the folder has an item by ID.
        """
        return self._tree.has_key(id)


    security.declareProtected(access_contents_information,
                              'objectIds')
    def objectIds(self, spec=None):
        # Returns a list of subobject ids of the current object.
        # If 'spec' is specified, returns objects whose meta_type
        # matches 'spec'.

        mti = self._mt_index
        if spec is None:
            spec = mti.keys() #all meta types

        if isinstance(spec, str):
            spec = [spec]
        set = None
        for meta_type in spec:
            ids = mti.get(meta_type, None)
            if ids is not None:
                set = union(set, ids)
        if set is None:
            return ()
        else:
            return set.keys()


    security.declareProtected(access_contents_information,
                              'objectValues')
    def objectValues(self, spec=None):
        # Returns a list of actual subobjects of the current object.
        # If 'spec' is specified, returns only objects whose meta_type
        # match 'spec'.
        return LazyMap(self._getOb, self.objectIds(spec))


    security.declareProtected(access_contents_information,
                              'objectItems')
    def objectItems(self, spec=None):
        # Returns a list of (id, subobject) tuples of the current object.
        # If 'spec' is specified, returns only objects whose meta_type match
        # 'spec'
        return LazyMap(lambda id, _getOb=self._getOb: (id, _getOb(id)),
                       self.objectIds(spec))


    security.declareProtected(access_contents_information,
                              'objectMap')
    def objectMap(self):
        # Returns a tuple of mappings containing subobject meta-data.
        return LazyMap(lambda (k, v):
                       {'id': k, 'meta_type': getattr(v, 'meta_type', None)},
                       self._tree.items(), self._count())

    # superValues() looks for the _objects attribute, but the implementation
    # would be inefficient, so superValues() support is disabled.
    _objects = ()


    security.declareProtected(access_contents_information,
                              'objectIds_d')
    def objectIds_d(self, t=None):
        ids = self.objectIds(t)
        res = {}
        for id in ids:
            res[id] = 1
        return res


    security.declareProtected(access_contents_information,
                              'objectMap_d')
    def objectMap_d(self, t=None):
        return self.objectMap()


    def _checkId(self, id, allow_dup=0):
        if not allow_dup and self.has_key(id):
            raise BadRequestException, ('The id "%s" is invalid--'
                                        'it is already in use.' % id)


    def _setObject(self, id, object, roles=None, user=None, set_owner=1,
                   suppress_events=False):
        ob = object # better name, keep original function signature
        v = self._checkId(id)
        if v is not None:
            id = v

        # If an object by the given id already exists, remove it.
        if self.has_key(id):
            self._delObject(id)

        if not suppress_events:
            notify(ObjectWillBeAddedEvent(ob, self, id))

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


    def _delObject(self, id, dp=1, suppress_events=False):
        ob = self._getOb(id)

        compatibilityCall('manage_beforeDelete', ob, ob, self)

        if not suppress_events:
            notify(ObjectWillBeRemovedEvent(ob, self, id))

        self._delOb(id)

        if not suppress_events:
            notify(ObjectRemovedEvent(ob, self, id))
            notifyContainerModified(self)


    # Aliases for mapping-like access.
    __len__ = objectCount
    security.declareProtected(access_contents_information, 'keys')
    keys = objectIds
    security.declareProtected(access_contents_information, 'values')
    values = objectValues
    security.declareProtected(access_contents_information, 'items')
    items = objectItems

    # backward compatibility
    security.declareProtected(access_contents_information, 'hasObject')
    hasObject = has_key

    security.declareProtected(access_contents_information, 'get')
    def get(self, name, default=None):
        return self._getOb(name, default)


    # Utility for generating unique IDs.

    security.declareProtected(access_contents_information, 'generateId')
    def generateId(self, prefix='item', suffix='', rand_ceiling=999999999):
        """Returns an ID not used yet by this folder.

        The ID is unlikely to collide with other threads and clients.
        The IDs are sequential to optimize access to objects
        that are likely to have some relation.
        """
        tree = self._tree
        n = self._v_nextid
        attempt = 0
        while 1:
            if n % 4000 != 0 and n <= rand_ceiling:
                id = '%s%d%s' % (prefix, n, suffix)
                if not tree.has_key(id):
                    break
            n = randint(1, rand_ceiling)
            attempt = attempt + 1
            if attempt > MAX_UNIQUEID_ATTEMPTS:
                # Prevent denial of service
                raise ExhaustedUniqueIdsError
        self._v_nextid = n + 1
        return id

    def __getattr__(self, name):
        # Boo hoo hoo!  Zope 2 prefers implicit acquisition over traversal
        # to subitems, and __bobo_traverse__ hooks don't work with
        # restrictedTraverse() unless __getattr__() is also present.
        # Oh well.
        res = self._tree.get(name)
        if res is None:
            raise AttributeError, name
        return res


InitializeClass(BTreeFolder2Base)


class BTreeFolder2 (BTreeFolder2Base, Folder):
    """BTreeFolder2 based on OFS.Folder.
    """
    meta_type = 'BTreeFolder2'

    def _checkId(self, id, allow_dup=0):
        Folder._checkId(self, id, allow_dup)
        BTreeFolder2Base._checkId(self, id, allow_dup)
    

InitializeClass(BTreeFolder2)

