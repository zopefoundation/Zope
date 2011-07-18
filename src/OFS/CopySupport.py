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

from cgi import escape
from marshal import dumps
from marshal import loads
import re
import sys
import tempfile
from urllib import quote
from urllib import unquote
import warnings
from zlib import compress
from zlib import decompress
import transaction

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import copy_or_move
from AccessControl.Permissions import delete_objects
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.Dialogs import MessageDialog
from App.special_dtml import HTML
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from webdav.Lockable import ResourceLockedError
from zExceptions import Unauthorized, BadRequest
from ZODB.POSException import ConflictError
from zope.interface import implements
from zope.event import notify
from zope.lifecycleevent import ObjectCopiedEvent
from zope.lifecycleevent import ObjectMovedEvent
from zope.container.contained import notifyContainerModified

from OFS.event import ObjectWillBeMovedEvent
from OFS.event import ObjectClonedEvent
from OFS.interfaces import ICopyContainer
from OFS.interfaces import ICopySource
from OFS.Moniker import loadMoniker
from OFS.Moniker import Moniker
from OFS.subscribers import compatibilityCall


class CopyError(Exception):
    pass

copy_re = re.compile('^copy([0-9]*)_of_(.*)')

_marker=[]


class CopyContainer(Base):

    """Interface for containerish objects which allow cut/copy/paste"""

    implements(ICopyContainer)

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

    security.declareProtected(delete_objects, 'manage_cutObjects')
    def manage_cutObjects(self, ids=None, REQUEST=None):
        """Put a reference to the objects named in ids in the clip board"""
        if ids is None and REQUEST is not None:
            return eNoItemsSpecified
        elif ids is None:
            raise ValueError('ids must be specified')

        if type(ids) is str:
            ids=[ids]
        oblist=[]
        for id in ids:
            ob=self._getOb(id)

            if ob.wl_isLocked():
                raise ResourceLockedError('Object "%s" is locked via WebDAV'
                                            % ob.getId())

            if not ob.cb_isMoveable():
                raise CopyError(eNotSupported % escape(id))
            m = Moniker(ob)
            oblist.append(m.dump())
        cp=(1, oblist)
        cp=_cb_encode(cp)
        if REQUEST is not None:
            resp=REQUEST['RESPONSE']
            resp.setCookie('__cp', cp, path='%s' % cookie_path(REQUEST))
            REQUEST['__cp'] = cp
            return self.manage_main(self, REQUEST)
        return cp

    security.declareProtected(view_management_screens, 'manage_copyObjects')
    def manage_copyObjects(self, ids=None, REQUEST=None, RESPONSE=None):
        """Put a reference to the objects named in ids in the clip board"""
        if ids is None and REQUEST is not None:
            return eNoItemsSpecified
        elif ids is None:
            raise ValueError('ids must be specified')

        if type(ids) is str:
            ids=[ids]
        oblist=[]
        for id in ids:
            ob=self._getOb(id)
            if not ob.cb_isCopyable():
                raise CopyError(eNotSupported % escape(id))
            m = Moniker(ob)
            oblist.append(m.dump())
        cp=(0, oblist)
        cp=_cb_encode(cp)
        if REQUEST is not None:
            resp=REQUEST['RESPONSE']
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
            id='copy%s_of_%s' % (n and n+1 or '', orig_id)
            n=n+1

    security.declareProtected(view_management_screens, 'manage_pasteObjects')
    def manage_pasteObjects(self, cb_copy_data=None, REQUEST=None):
        """Paste previously copied objects into the current object.

        If calling manage_pasteObjects from python code, pass the result of a
        previous call to manage_cutObjects or manage_copyObjects as the first
        argument.

        Also sends IObjectCopiedEvent and IObjectClonedEvent
        or IObjectWillBeMovedEvent and IObjectMovedEvent.
        """
        if cb_copy_data is not None:
            cp = cb_copy_data
        elif REQUEST is not None and REQUEST.has_key('__cp'):
            cp = REQUEST['__cp']
        else:
            cp = None
        if cp is None:
            raise CopyError(eNoData)

        try:
            op, mdatas = _cb_decode(cp)
        except:
            raise CopyError(eInvalid)

        oblist = []
        app = self.getPhysicalRoot()
        for mdata in mdatas:
            m = loadMoniker(mdata)
            try:
                ob = m.bind(app)
            except ConflictError:
                raise
            except:
                raise CopyError(eNotFound)
            self._verifyObjectPaste(ob, validate_src=op+1)
            oblist.append(ob)

        result = []
        if op == 0:
            # Copy operation
            for ob in oblist:
                orig_id = ob.getId()
                if not ob.cb_isCopyable():
                    raise CopyError(eNotSupported % escape(orig_id))

                try:
                    ob._notifyOfCopyTo(self, op=0)
                except ConflictError:
                    raise
                except:
                    raise CopyError(MessageDialog(
                        title="Copy Error",
                        message=sys.exc_info()[1],
                        action='manage_main'))

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

            if REQUEST is not None:
                return self.manage_main(self, REQUEST, update_menu=1,
                                        cb_dataValid=1)

        elif op == 1:
            # Move operation
            for ob in oblist:
                orig_id = ob.getId()
                if not ob.cb_isMoveable():
                    raise CopyError(eNotSupported % escape(orig_id))

                try:
                    ob._notifyOfCopyTo(self, op=1)
                except ConflictError:
                    raise
                except:
                    raise CopyError(MessageDialog(
                        title="Move Error",
                        message=sys.exc_info()[1],
                        action='manage_main'))

                if not sanity_check(self, ob):
                    raise CopyError(
                            "This object cannot be pasted into itself")

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

            if REQUEST is not None:
                REQUEST['RESPONSE'].setCookie('__cp', 'deleted',
                                    path='%s' % cookie_path(REQUEST),
                                    expires='Wed, 31-Dec-97 23:59:59 GMT')
                REQUEST['__cp'] = None
                return self.manage_main(self, REQUEST, update_menu=1,
                                        cb_dataValid=0)

        return result

    security.declareProtected(view_management_screens, 'manage_renameForm')
    manage_renameForm = DTMLFile('dtml/renameForm', globals())

    security.declareProtected(view_management_screens, 'manage_renameObjects')
    def manage_renameObjects(self, ids=[], new_ids=[], REQUEST=None):
        """Rename several sub-objects"""
        if len(ids) != len(new_ids):
            raise BadRequest('Please rename each listed object.')
        for i in range(len(ids)):
            if ids[i] != new_ids[i]:
                self.manage_renameObject(ids[i], new_ids[i], REQUEST)
        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1)
        return None

    security.declareProtected(view_management_screens, 'manage_renameObject')
    def manage_renameObject(self, id, new_id, REQUEST=None):
        """Rename a particular sub-object.
        """
        try:
            self._checkId(new_id)
        except:
            raise CopyError(MessageDialog(
                title='Invalid Id',
                message=sys.exc_info()[1],
                action ='manage_main'))

        ob = self._getOb(id)

        if ob.wl_isLocked():
            raise ResourceLockedError('Object "%s" is locked via WebDAV'
                                        % ob.getId())
        if not ob.cb_isMoveable():
            raise CopyError(eNotSupported % escape(id))
        self._verifyObjectPaste(ob)

        try:
            ob._notifyOfCopyTo(self, op=1)
        except ConflictError:
            raise
        except:
            raise CopyError(MessageDialog(
                title="Rename Error",
                message=sys.exc_info()[1],
                action ='manage_main'))

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
            return self.manage_main(self, REQUEST, update_menu=1)
        return None

    # Why did we give this a manage_ prefix if its really
    # supposed to be public since it does its own auth ?
    #
    # Because it's still a "management" function.

    security.declarePublic('manage_clone')
    def manage_clone(self, ob, id, REQUEST=None):
        """Clone an object, creating a new object with the given id.
        """
        if not ob.cb_isCopyable():
            raise CopyError(eNotSupported % escape(ob.getId()))
        try:
            self._checkId(id)
        except:
            raise CopyError(MessageDialog(
                title='Invalid Id',
                message=sys.exc_info()[1],
                action ='manage_main'))

        self._verifyObjectPaste(ob)

        try:
            ob._notifyOfCopyTo(self, op=0)
        except ConflictError:
            raise
        except:
            raise CopyError(MessageDialog(
                title="Clone Error",
                message=sys.exc_info()[1],
                action='manage_main'))

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
        try:    cp=_cb_decode(self.REQUEST['__cp'])
        except: return 0
        return 1

    def cb_dataItems(self):
        # List of objects in the clip board
        try:    cp=_cb_decode(self.REQUEST['__cp'])
        except: return []
        oblist=[]

        app = self.getPhysicalRoot()
        for mdata in cp[1]:
            m = loadMoniker(mdata)
            oblist.append(m.bind(app))
        return oblist

    validClipData=cb_dataValid

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
            raise CopyError(MessageDialog(
                  title   = 'Not Supported',
                  message = ('The object <em>%s</em> does not support this' \
                             ' operation' % escape(absattr(object.id))),
                  action  = 'manage_main'))

        if not hasattr(self, 'all_meta_types'):
            raise CopyError(MessageDialog(
                  title   = 'Not Supported',
                  message = 'Cannot paste into this object.',
                  action  = 'manage_main'))

        method_name = None
        mt_permission = None
        meta_types = absattr(self.all_meta_types)

        for d in meta_types:
            if d['name'] == object.meta_type:
                method_name = d['action']
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
                    except:
                        parent = None

                    if not sm.validate(None, parent, None, object):
                        raise Unauthorized(absattr(object.id))

                    if validate_src == 2: # moving
                        if not sm.checkPermission(delete_objects, parent):
                            raise Unauthorized('Delete not allowed.')
            else:
                raise CopyError(MessageDialog(
                    title = 'Insufficient Privileges',
                    message = ('You do not possess the %s permission in the '
                               'context of the container into which you are '
                               'pasting, thus you are not able to perform '
                               'this operation.' % mt_permission),
                    action = 'manage_main'))
        else:
            raise CopyError(MessageDialog(
                title = 'Not Supported',
                message = ('The object <em>%s</em> does not support this '
                           'operation.' % escape(absattr(object.id))),
                action = 'manage_main'))

InitializeClass(CopyContainer)


class CopySource(Base):

    """Interface for objects which allow themselves to be copied."""

    implements(ICopySource)

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
                'Object "%s" needs to be in the database to be copied' %
                `self`)
        if container._p_jar is None:
            raise CopyError(
                'Container "%s" needs to be in the database' %
                `container`)

        # Ask an object for a new copy of itself.
        f=tempfile.TemporaryFile()
        self._p_jar.exportFile(self._p_oid,f)
        f.seek(0)
        ob=container._p_jar.importFile(f)
        f.close()
        return ob

    def _postCopy(self, container, op=0):
        # Called after the copy is finished to accomodate special cases.
        # The op var is 0 for a copy, 1 for a move.
        pass

    def _setId(self, id):
        # Called to set the new id of a copied object.
        self.id=id

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
        try:    n=aq_parent(aq_inner(self))._reserved_names
        except: n=()
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
    if callable(attr): return attr()
    return attr

def _cb_encode(d):
    return quote(compress(dumps(d), 9))

def _cb_decode(s):
    return loads(decompress(unquote(s)))

def cookie_path(request):
    # Return a "path" value for use in a cookie that refers
    # to the root of the Zope object space.
    return request['BASEPATH1'] or "/"



fMessageDialog = HTML("""
<HTML>
<HEAD>
<TITLE>&dtml-title;</TITLE>
</HEAD>
<BODY BGCOLOR="#FFFFFF">
<FORM ACTION="&dtml-action;" METHOD="GET" <dtml-if
 target>TARGET="&dtml-target;"</dtml-if>>
<TABLE BORDER="0" WIDTH="100%%" CELLPADDING="10">
<TR>
  <TD VALIGN="TOP">
  <BR>
  <CENTER><B><FONT SIZE="+6" COLOR="#77003B">!</FONT></B></CENTER>
  </TD>
  <TD VALIGN="TOP">
  <BR><BR>
  <CENTER>
  <dtml-var message>
  </CENTER>
  </TD>
</TR>
<TR>
  <TD VALIGN="TOP">
  </TD>
  <TD VALIGN="TOP">
  <CENTER>
  <INPUT TYPE="SUBMIT" VALUE="   Ok   ">
  </CENTER>
  </TD>
</TR>
</TABLE>
</FORM>
</BODY></HTML>""", target='', action='manage_main', title='Changed')


eNoData=MessageDialog(
        title='No Data',
        message='No clipboard data found.',
        action ='manage_main',)

eInvalid=MessageDialog(
         title='Clipboard Error',
         message='The data in the clipboard could not be read, possibly due ' \
         'to cookie data being truncated by your web browser. Try copying ' \
         'fewer objects.',
         action ='manage_main',)

eNotFound=MessageDialog(
          title='Item Not Found',
          message='One or more items referred to in the clipboard data was ' \
          'not found. The item may have been moved or deleted after you ' \
          'copied it.',
          action ='manage_main',)

eNotSupported=fMessageDialog(
              title='Not Supported',
              message=(
              'The action against the <em>%s</em> object could not be carried '
              'out. '
              'One of the following constraints caused the problem: <br><br>'
              'The object does not support this operation.'
              '<br><br>-- OR --<br><br>'
              'The currently logged-in user does not have the <b>Copy or '
              'Move</b> permission respective to the object.'
              ),
              action ='manage_main',)

eNoItemsSpecified=MessageDialog(
                  title='No items specified',
                  message='You must select one or more items to perform ' \
                  'this operation.',
                  action ='manage_main'
                  )
