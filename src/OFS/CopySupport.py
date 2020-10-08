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
"""Copy interface
"""

import base64
import logging
import re
import tempfile
import warnings
from json import dumps
from json import loads
from zlib import compress
from zlib import decompressobj

import transaction
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import copy_or_move
from AccessControl.Permissions import delete_objects
from AccessControl.Permissions import view_management_screens
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from OFS.event import ObjectClonedEvent
from OFS.event import ObjectWillBeMovedEvent
from OFS.interfaces import ICopyContainer
from OFS.interfaces import ICopySource
from OFS.Moniker import Moniker
from OFS.Moniker import loadMoniker
from OFS.subscribers import compatibilityCall
from zExceptions import BadRequest
from zExceptions import ResourceLockedError
from zExceptions import Unauthorized
from ZODB.POSException import ConflictError
from zope.container.contained import notifyContainerModified
from zope.event import notify
from zope.interface import implementer
from zope.lifecycleevent import ObjectCopiedEvent
from zope.lifecycleevent import ObjectMovedEvent


class CopyError(Exception):
    pass


copy_re = re.compile('^copy([0-9]*)_of_(.*)')
logger = logging.getLogger('OFS')
_marker = []


@implementer(ICopyContainer)
class CopyContainer(Base):

    """Interface for containerish objects which allow cut/copy/paste"""

    security = ClassSecurityInfo()

    # The following three methods should be overridden to store sub-objects
    # as non-attributes.
    def _setOb(self, id, object):
        setattr(self, id, object)

    def _delOb(self, id):
        delattr(self, id)

    def _getOb(self, id, default=_marker):
        if hasattr(aq_base(self), id):
            return getattr(self, id)
        if default is _marker:
            raise AttributeError(id)
        return default

    def manage_CopyContainerFirstItem(self, REQUEST):
        return self._getOb(REQUEST['ids'][0])

    def manage_CopyContainerAllItems(self, REQUEST):
        return [self._getOb(i) for i in REQUEST['ids']]

    @security.protected(delete_objects)
    def manage_cutObjects(self, ids=None, REQUEST=None):
        """Put a reference to the objects named in ids in the clip board"""
        if ids is None and REQUEST is not None:
            raise BadRequest('No items specified')
        elif ids is None:
            raise ValueError('ids must be specified')

        if isinstance(ids, str):
            ids = [ids]
        oblist = []
        for id in ids:
            ob = self._getOb(id)

            if ob.wl_isLocked():
                raise ResourceLockedError('Object "%s" is locked' % ob.getId())

            if not ob.cb_isMoveable():
                raise CopyError('Not Supported')
            m = Moniker(ob)
            oblist.append(m.dump())
        cp = (1, oblist)
        cp = _cb_encode(cp)
        if REQUEST is not None:
            resp = REQUEST['RESPONSE']
            resp.setCookie('__cp', cp, path='%s' % cookie_path(REQUEST))
            REQUEST['__cp'] = cp
            return self.manage_main(self, REQUEST)
        return cp

    @security.protected(view_management_screens)
    def manage_copyObjects(self, ids=None, REQUEST=None, RESPONSE=None):
        """Put a reference to the objects named in ids in the clip board"""
        if ids is None and REQUEST is not None:
            raise BadRequest('No items specified')
        elif ids is None:
            raise ValueError('ids must be specified')

        if isinstance(ids, str):
            ids = [ids]
        oblist = []
        for id in ids:
            ob = self._getOb(id)
            if not ob.cb_isCopyable():
                raise CopyError('Not Supported')
            m = Moniker(ob)
            oblist.append(m.dump())
        cp = (0, oblist)
        cp = _cb_encode(cp)
        if REQUEST is not None:
            resp = REQUEST['RESPONSE']
            resp.setCookie('__cp', cp, path='%s' % cookie_path(REQUEST))
            REQUEST['__cp'] = cp
            return self.manage_main(self, REQUEST)
        return cp

    def _get_id(self, id):
        # Allow containers to override the generation of
        # object copy id by attempting to call its _get_id
        # method, if it exists.
        match = copy_re.match(id)
        if match:
            n = int(match.group(1) or '1')
            orig_id = match.group(2)
        else:
            n = 0
            orig_id = id
        while 1:
            if self._getOb(id, None) is None:
                return id
            id = 'copy{}_of_{}'.format(n and n + 1 or '', orig_id)
            n = n + 1

    def _pasteObjects(self, cp, cb_maxsize=0):
        """Paste previously copied objects into the current object.

        ``cp`` is the list of objects for paste as encoded by ``_cb_encode``.
        If calling _pasteObjects from python code, pass the result of a
        previous call to manage_cutObjects or manage_copyObjects as the first
        argument.

        ``cb_maxsize`` is the maximum size of the JSON representation of the
        object list. Set it to a non-zero value to prevent DoS attacks with
        huge object lists or zlib bombs.

        This method sends IObjectCopiedEvent and IObjectClonedEvent
        or IObjectWillBeMovedEvent and IObjectMovedEvent.

        Returns tuple of (operator, list of {'id': orig_id, 'new_id': new_id}).
        Where `operator` is 0 for a copy operation and 1 for a move operation.
        """
        if cp is None:
            raise CopyError('No clipboard data found.')

        try:
            op, mdatas = _cb_decode(cp, cb_maxsize)
        except Exception as e:
            raise CopyError('Clipboard Error') from e

        oblist = []
        app = self.getPhysicalRoot()
        for mdata in mdatas:
            m = loadMoniker(mdata)
            try:
                ob = m.bind(app)
            except ConflictError:
                raise
            except Exception:
                raise CopyError('Item Not Found')
            self._verifyObjectPaste(ob, validate_src=op + 1)
            oblist.append(ob)

        result = []
        if op == 0:
            # Copy operation
            for ob in oblist:
                orig_id = ob.getId()
                if not ob.cb_isCopyable():
                    raise CopyError('Not Supported')

                try:
                    ob._notifyOfCopyTo(self, op=0)
                except ConflictError:
                    raise
                except Exception:
                    raise CopyError('Copy Error')

                id = self._get_id(orig_id)
                result.append({'id': orig_id, 'new_id': id})

                orig_ob = ob
                ob = ob._getCopy(self)
                ob._setId(id)
                notify(ObjectCopiedEvent(ob, orig_ob))

                self._setObject(id, ob)
                ob = self._getOb(id)
                ob.wl_clearLocks()

                ob._postCopy(self, op=0)

                compatibilityCall('manage_afterClone', ob, ob)

                notify(ObjectClonedEvent(ob))

        elif op == 1:
            # Move operation
            for ob in oblist:
                orig_id = ob.getId()
                if not ob.cb_isMoveable():
                    raise CopyError('Not Supported')

                try:
                    ob._notifyOfCopyTo(self, op=1)
                except ConflictError:
                    raise
                except Exception:
                    raise CopyError('Move Error')

                if not sanity_check(self, ob):
                    raise CopyError("This object cannot be pasted into itself")

                orig_container = aq_parent(aq_inner(ob))
                if aq_base(orig_container) is aq_base(self):
                    id = orig_id
                else:
                    id = self._get_id(orig_id)
                result.append({'id': orig_id, 'new_id': id})

                notify(ObjectWillBeMovedEvent(ob, orig_container, orig_id,
                                              self, id))

                # try to make ownership explicit so that it gets carried
                # along to the new location if needed.
                ob.manage_changeOwnershipType(explicit=1)

                try:
                    orig_container._delObject(orig_id, suppress_events=True)
                except TypeError:
                    orig_container._delObject(orig_id)
                    warnings.warn(
                        "%s._delObject without suppress_events is discouraged."
                        % orig_container.__class__.__name__,
                        DeprecationWarning)
                ob = aq_base(ob)
                ob._setId(id)

                try:
                    self._setObject(id, ob, set_owner=0, suppress_events=True)
                except TypeError:
                    self._setObject(id, ob, set_owner=0)
                    warnings.warn(
                        "%s._setObject without suppress_events is discouraged."
                        % self.__class__.__name__, DeprecationWarning)
                ob = self._getOb(id)

                notify(ObjectMovedEvent(ob, orig_container, orig_id, self, id))
                notifyContainerModified(orig_container)
                if aq_base(orig_container) is not aq_base(self):
                    notifyContainerModified(self)

                ob._postCopy(self, op=1)
                # try to make ownership implicit if possible
                ob.manage_changeOwnershipType(explicit=0)

        return op, result

    @security.protected(view_management_screens)
    def manage_pasteObjects(self, cb_copy_data=None, REQUEST=None):
        """Paste previously copied objects into the current object.

        If calling manage_pasteObjects from python code, pass the result of a
        previous call to manage_cutObjects or manage_copyObjects as the first
        argument.

        Also sends IObjectCopiedEvent and IObjectClonedEvent
        or IObjectWillBeMovedEvent and IObjectMovedEvent.

        If `REQUEST` is None it returns a
        list of dicts {'id': orig_id, 'new_id': new_id} otherwise it renders
        a HTML page.
        """
        if cb_copy_data is None and REQUEST is not None and '__cp' in REQUEST:
            cb_copy_data = REQUEST['__cp']
        op, result = self._pasteObjects(cb_copy_data, cb_maxsize=8192)

        if REQUEST is not None:
            if op == 0:
                cb_valid = 1
            elif op == 1:
                REQUEST['RESPONSE'].setCookie(
                    '__cp', 'deleted',
                    path='%s' % cookie_path(REQUEST),
                    expires='Wed, 31-Dec-97 23:59:59 GMT')
                REQUEST['__cp'] = None
                cb_valid = 0
            return self.manage_main(self, REQUEST, cb_dataValid=cb_valid)

        return result

    security.declareProtected(view_management_screens, 'manage_renameForm')  # NOQA: D001,E501
    manage_renameForm = DTMLFile('dtml/renameForm', globals())

    @security.protected(view_management_screens)
    def manage_renameObjects(self, ids=[], new_ids=[], REQUEST=None):
        """Rename several sub-objects"""
        if len(ids) != len(new_ids):
            raise BadRequest('Please rename each listed object.')
        for i in range(len(ids)):
            if ids[i] != new_ids[i]:
                self.manage_renameObject(ids[i], new_ids[i], REQUEST)
        if REQUEST is not None:
            return self.manage_main(self, REQUEST)

    @security.protected(view_management_screens)
    def manage_renameObject(self, id, new_id, REQUEST=None):
        """Rename a particular sub-object.
        """
        try:
            self._checkId(new_id)
        except Exception:
            raise CopyError('Invalid Id')

        ob = self._getOb(id)

        if ob.wl_isLocked():
            raise ResourceLockedError('Object "%s" is locked' % ob.getId())
        if not ob.cb_isMoveable():
            raise CopyError('Not Supported')
        self._verifyObjectPaste(ob)

        try:
            ob._notifyOfCopyTo(self, op=1)
        except ConflictError:
            raise
        except Exception:
            raise CopyError('Rename Error')

        notify(ObjectWillBeMovedEvent(ob, self, id, self, new_id))

        try:
            self._delObject(id, suppress_events=True)
        except TypeError:
            self._delObject(id)
            warnings.warn(
                "%s._delObject without suppress_events is discouraged." %
                self.__class__.__name__, DeprecationWarning)
        ob = aq_base(ob)
        ob._setId(new_id)

        # Note - because a rename always keeps the same context, we
        # can just leave the ownership info unchanged.
        try:
            self._setObject(new_id, ob, set_owner=0, suppress_events=True)
        except TypeError:
            self._setObject(new_id, ob, set_owner=0)
            warnings.warn(
                "%s._setObject without suppress_events is discouraged." %
                self.__class__.__name__, DeprecationWarning)
        ob = self._getOb(new_id)

        notify(ObjectMovedEvent(ob, self, id, self, new_id))
        notifyContainerModified(self)

        ob._postCopy(self, op=1)

        if REQUEST is not None:
            return self.manage_main(self, REQUEST)

    @security.public
    def manage_clone(self, ob, id, REQUEST=None):
        """Clone an object, creating a new object with the given id.
        """
        if not ob.cb_isCopyable():
            raise CopyError('Not Supported')
        try:
            self._checkId(id)
        except Exception:
            raise CopyError('Invalid Id')

        self._verifyObjectPaste(ob)

        try:
            ob._notifyOfCopyTo(self, op=0)
        except ConflictError:
            raise
        except Exception:
            raise CopyError('Clone Error')

        orig_ob = ob
        ob = ob._getCopy(self)
        ob._setId(id)
        notify(ObjectCopiedEvent(ob, orig_ob))

        self._setObject(id, ob)
        ob = self._getOb(id)

        ob._postCopy(self, op=0)

        compatibilityCall('manage_afterClone', ob, ob)

        notify(ObjectClonedEvent(ob))

        return ob

    def cb_dataValid(self):
        # Return true if clipboard data seems valid.
        try:
            _cb_decode(self.REQUEST['__cp'])
        except Exception:
            return 0
        return 1

    def cb_dataItems(self):
        # List of objects in the clip board
        try:
            cp = _cb_decode(self.REQUEST['__cp'])
        except Exception:
            return []
        oblist = []

        app = self.getPhysicalRoot()
        for mdata in cp[1]:
            m = loadMoniker(mdata)
            oblist.append(m.bind(app))
        return oblist

    validClipData = cb_dataValid

    def _verifyObjectPaste(self, object, validate_src=1):
        # Verify whether the current user is allowed to paste the
        # passed object into self. This is determined by checking
        # to see if the user could create a new object of the same
        # meta_type of the object passed in and checking that the
        # user actually is allowed to access the passed in object
        # in its existing context.
        #
        # Passing a false value for the validate_src argument will skip
        # checking the passed in object in its existing context. This is
        # mainly useful for situations where the passed in object has no
        # existing context, such as checking an object during an import
        # (the object will not yet have been connected to the acquisition
        # heirarchy).

        if not hasattr(object, 'meta_type'):
            raise CopyError('Not Supported')

        if not hasattr(self, 'all_meta_types'):
            raise CopyError('Cannot paste into this object.')

        mt_permission = None
        meta_types = absattr(self.all_meta_types)

        for d in meta_types:
            if d['name'] == object.meta_type:
                mt_permission = d.get('permission')
                break

        if mt_permission is not None:
            sm = getSecurityManager()

            if sm.checkPermission(mt_permission, self):
                if validate_src:
                    # Ensure the user is allowed to access the object on the
                    # clipboard.
                    try:
                        parent = aq_parent(aq_inner(object))
                    except Exception:
                        parent = None

                    if not sm.validate(None, parent, None, object):
                        raise Unauthorized(absattr(object.id))

                    if validate_src == 2:  # moving
                        if not sm.checkPermission(delete_objects, parent):
                            raise Unauthorized('Delete not allowed.')
            else:
                raise CopyError('Insufficient privileges')
        else:
            raise CopyError('Not Supported')


InitializeClass(CopyContainer)


@implementer(ICopySource)
class CopySource(Base):

    """Interface for objects which allow themselves to be copied."""

    # declare a dummy permission for Copy or Move here that we check
    # in cb_isCopyable.
    security = ClassSecurityInfo()
    security.setPermissionDefault(copy_or_move, ('Anonymous', 'Manager'))

    def _canCopy(self, op=0):
        """Called to make sure this object is copyable.

        The op var is 0 for a copy, 1 for a move.
        """
        return 1

    def _notifyOfCopyTo(self, container, op=0):
        """Overide this to be pickly about where you go!

        If you dont want to go there, raise an exception. The op variable is 0
        for a copy, 1 for a move.
        """
        pass

    def _getCopy(self, container):
        # Commit a subtransaction to:
        # 1) Make sure the data about to be exported is current
        # 2) Ensure self._p_jar and container._p_jar are set even if
        #    either one is a new object
        transaction.savepoint(optimistic=True)

        if self._p_jar is None:
            raise CopyError(
                'Object "%r" needs to be in the database to be copied' % self)
        if container._p_jar is None:
            raise CopyError(
                'Container "%r" needs to be in the database' % container)

        # Ask an object for a new copy of itself.
        with tempfile.TemporaryFile() as f:
            self._p_jar.exportFile(self._p_oid, f)
            f.seek(0)
            ob = container._p_jar.importFile(f)

        # Cleanup the copy.  It may contain private objects that the current
        # user is not allowed to see.
        sm = getSecurityManager()
        if not sm.checkPermission('View', self):
            # The user is not allowed to view the object that is currently
            # being copied, so it makes no sense to check any of its sub
            # objects.  It probably means we are in a test.
            return ob
        return self._cleanupCopy(ob, container)

    def _cleanupCopy(self, cp, container):
        sm = getSecurityManager()
        ob = aq_base(self)
        if hasattr(ob, 'objectIds'):
            for k in self.objectIds():
                v = self._getOb(k)
                if not sm.checkPermission('View', v):
                    # We do not use cp._delObject, because this would fire
                    # events that are needless for objects that are not even in
                    # an Acquisition chain yet.
                    logger.warning(
                        'While copying %s to %s, removed %s from copy '
                        'because user is not allowed to view the original.',
                        '/'.join(self.getPhysicalPath()),
                        '/'.join(container.getPhysicalPath()),
                        '/'.join(v.getPhysicalPath())
                    )
                    cp._delOb(k)
                    # We need to cleanup the internal objects list, even when
                    # in some implementations this is always an empty tuple.
                    cp._objects = tuple([
                        i for i in cp._objects if i['id'] != k])
                else:
                    # recursively check
                    v._cleanupCopy(cp._getOb(k), container)
        return cp

    def _postCopy(self, container, op=0):
        # Called after the copy is finished to accomodate special cases.
        # The op var is 0 for a copy, 1 for a move.
        pass

    def _setId(self, id):
        # Called to set the new id of a copied object.
        self.id = id

    def cb_isCopyable(self):
        # Is object copyable? Returns 0 or 1
        if not (hasattr(self, '_canCopy') and self._canCopy(0)):
            return 0
        if not self.cb_userHasCopyOrMovePermission():
            return 0
        return 1

    def cb_isMoveable(self):
        # Is object moveable? Returns 0 or 1
        if not (hasattr(self, '_canCopy') and self._canCopy(1)):
            return 0
        if hasattr(self, '_p_jar') and self._p_jar is None:
            return 0
        try:
            n = aq_parent(aq_inner(self))._reserved_names
        except Exception:
            n = ()
        if absattr(self.id) in n:
            return 0
        if not self.cb_userHasCopyOrMovePermission():
            return 0
        return 1

    def cb_userHasCopyOrMovePermission(self):
        if getSecurityManager().checkPermission(copy_or_move, self):
            return 1


InitializeClass(CopySource)


def sanity_check(c, ob):
    # This is called on cut/paste operations to make sure that
    # an object is not cut and pasted into itself or one of its
    # subobjects, which is an undefined situation.
    ob = aq_base(ob)
    while 1:
        if aq_base(c) is ob:
            return 0
        inner = aq_inner(c)
        if aq_parent(inner) is None:
            return 1
        c = aq_parent(inner)


def absattr(attr):
    if callable(attr):
        return attr()
    return attr


def _cb_encode(d):
    """Encode a list of IDs for storage in a cookie.

    ``d`` must be a list or tuple of text IDs.

    Return text.
    """
    json_bytes = dumps(d).encode('utf-8')
    squashed_bytes = compress(json_bytes, 2)  # -> bytes w/ useful encoding
    # quote for embeding in cookie
    return base64.encodebytes(squashed_bytes)


def _cb_decode(s, maxsize=8192):
    """Decode a list of IDs from storage in a cookie.

    ``s`` is text as encoded by ``_cb_encode``.
    ``maxsize`` is the maximum size of uncompressed data. ``0`` means no limit.

    Return a list of text IDs.
    """
    dec = decompressobj()
    if isinstance(s, str):
        s = s.encode('latin-1')
    data = dec.decompress(base64.decodebytes(s), maxsize)
    if dec.unconsumed_tail:
        raise ValueError
    json_bytes = data.decode('utf-8')
    return loads(json_bytes)


def cookie_path(request):
    # Return a "path" value for use in a cookie that refers
    # to the root of the Zope object space.
    return request['BASEPATH1'] or "/"
