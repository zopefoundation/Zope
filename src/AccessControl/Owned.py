##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Support for owned objects

$Id$
"""
import urlparse

from Acquisition import aq_base
from Acquisition import aq_get
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.special_dtml import DTMLFile
from App.class_init import InitializeClass
from ExtensionClass import Base
from zope.interface import implements

from AccessControl.interfaces import IOwned
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import take_ownership
from AccessControl.requestmethod import requestmethod
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
# avoid importing 'emergency_user' / 'nobody'  before set
from AccessControl import SpecialUsers as SU
from AccessControl.unauthorized import Unauthorized

UnownableOwner=[]
def ownableFilter(self):
    _owner = aq_get(self, '_owner', None, 1)
    return _owner is not UnownableOwner

# Marker to use as a getattr default.
_mark=ownableFilter

class Owned(Base):

    implements(IOwned)

    security = ClassSecurityInfo()
    security.setPermissionDefault(take_ownership, ('Owner',))

    manage_options=({'label':  'Ownership',
                     'action': 'manage_owner',
                     'help':   ('OFSP','Ownership.stx'),
                     'filter': ownableFilter
                     },
                   )

    security.declareProtected(view_management_screens, 'manage_owner')
    manage_owner = DTMLFile('dtml/owner', globals())

    security.declareProtected(view_management_screens, 'owner_info')
    def owner_info(self):
        """Get ownership info for display
        """
        owner=self.getOwnerTuple()

        if owner is None or owner is UnownableOwner:
            return owner

        d={'path': '/'.join(owner[0]), 'id': owner[1],
           'explicit': hasattr(self, '_owner'),
           'userCanChangeOwnershipType':
           getSecurityManager().checkPermission('Take ownership', self)
           }
        return d

    security.declarePrivate('getOwner')
    def getOwner(self, info=0,
                 aq_get=aq_get,
                 UnownableOwner=UnownableOwner,
                 getSecurityManager=getSecurityManager,
                 ):
        """Get the owner

        If a true argument is provided, then only the owner path and id are
        returned. Otherwise, the owner object is returned.
        """
        if info:
            import warnings
            warnings.warn('Owned.getOwner(1) is deprecated; '
                          'please use getOwnerTuple() instead.',
                          DeprecationWarning, stacklevel=2)


        owner=aq_get(self, '_owner', None, 1)
        if info or (owner is None): return owner

        if owner is UnownableOwner: return None

        udb, oid = owner

        root=self.getPhysicalRoot()
        udb=root.unrestrictedTraverse(udb, None)
        if udb is None:
            user = SU.nobody
        else:
            user = udb.getUserById(oid, None)
            if user is None: user = SU.nobody
        return user

    security.declarePrivate('getOwnerTuple')
    def getOwnerTuple(self):
        """Return a tuple, (userdb_path, user_id) for the owner.

        o Ownership can be acquired, but only from the containment path.

        o If unowned, return None.
        """
        return aq_get(self, '_owner', None, 1)

    security.declarePrivate('getWrappedOwner')
    def getWrappedOwner(self):
        """Get the owner, modestly wrapped in the user folder.

        o If the object is not owned, return None.

        o If the owner's user database doesn't exist, return Nobody.

        o If the owner ID does not exist in the user database, return Nobody.
        """
        owner = self.getOwnerTuple()

        if owner is None or owner is UnownableOwner:
            return None

        udb_path, oid = owner

        root = self.getPhysicalRoot()
        udb = root.unrestrictedTraverse(udb_path, None)

        if udb is None:
            return SU.nobody

        user = udb.getUserById(oid, None)

        if user is None:
            return SU.nobody

        return user.__of__(udb)

    security.declarePrivate('changeOwnership')
    def changeOwnership(self, user, recursive=0):
        """Change the ownership to the given user.

        If 'recursive' is true then also take ownership of all sub-objects,
        otherwise sub-objects retain their ownership information.
        """
        new = ownerInfo(user)
        if new is None: 
            return # Special user!
        old = self.getOwnerTuple()

        if not recursive:
            if old == new or old is UnownableOwner:
                return

        if recursive:
            children = getattr( aq_base(self), 'objectValues', lambda :() )()
            for child in children:
                child.changeOwnership(user, 1)

        if old is not UnownableOwner:
            self._owner = new

    def userCanTakeOwnership(self):
        security=getSecurityManager()
        user=security.getUser()
        info=ownerInfo(user)
        if info is None: return 0
        owner=self.getOwnerTuple()
        if owner == info: return 0
        return security.checkPermission('Take ownership', self)

    security.declareProtected(take_ownership, 'manage_takeOwnership')
    @requestmethod('POST')
    def manage_takeOwnership(self, REQUEST, RESPONSE, recursive=0):
        """Take ownership (responsibility) for an object.

        If 'recursive' is true, then also take ownership of all sub-objects.
        """
        security=getSecurityManager()
        want_referer=REQUEST['URL1']+'/manage_owner'
        got_referer=("%s://%s%s" %
                     urlparse.urlparse(REQUEST['HTTP_REFERER'])[:3])
        __traceback_info__=want_referer, got_referer
        if (want_referer != got_referer or security.calledByExecutable()):
            raise Unauthorized, (
                'manage_takeOwnership was called from an invalid context'
                )

        self.changeOwnership(security.getUser(), recursive)

        RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    security.declareProtected(take_ownership, 'manage_changeOwnershipType')
    @requestmethod('POST')
    def manage_changeOwnershipType(self, explicit=1,
                                   RESPONSE=None, REQUEST=None):
        """Change the type (implicit or explicit) of ownership.
        """
        old=getattr(self, '_owner', None)
        if explicit:
            if old is not None: return
            owner = self.getOwnerTuple()
            if owner is not None and owner is not UnownableOwner:
                self._owner=owner
        else:
            if old is None: return
            new=aq_get(aq_parent(self), '_owner', None, 1)
            if old is new and (
                self.__dict__.get('_owner', _mark) is not _mark
                ):
                del self._owner

        if RESPONSE is not None: RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    def _deleteOwnershipAfterAdd(self):

        # Only delete _owner if it is an instance attribute.
        if self.__dict__.get('_owner', _mark) is not _mark:
            del self._owner

        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            try: object._deleteOwnershipAfterAdd()
            except: pass
            if s is None: object._p_deactivate()

    def manage_fixupOwnershipAfterAdd(self):

        # Sigh, get the parent's _owner
        parent=getattr(self, '__parent__', None)
        if parent is not None: _owner=aq_get(parent, '_owner', None, 1)
        else: _owner=None

        if (_owner is None and
            ((getattr(self, '__parent__', None) is None) or
             (not hasattr(self, 'getPhysicalRoot'))
             )
            ):
            # This is a special case. An object is
            # being added to an object that hasn't
            # been added to the object hierarchy yet.
            # We can delay fixing up the ownership until the
            # object is actually added.
            return None

        if _owner is UnownableOwner:
            # We want to acquire Unownable ownership!
            return self._deleteOwnershipAfterAdd()
        else:
            # Otherwise change the ownership
            user=getSecurityManager().getUser()
            if (SU.emergency_user and aq_base(user) is SU.emergency_user):
                __creatable_by_emergency_user__=getattr(
                    self,'__creatable_by_emergency_user__', None)
                if (__creatable_by_emergency_user__ is None or
                    (not __creatable_by_emergency_user__())):
                    raise EmergencyUserCannotOwn, (
                        "Objects cannot be owned by the emergency user")
            self.changeOwnership(user)

        # Force all subs to acquire ownership!
        for object in self.objectValues():
            try: s=object._p_changed
            except: s=0
            try: object._deleteOwnershipAfterAdd()
            except: pass
            if s is None: object._p_deactivate()

InitializeClass(Owned)


class EmergencyUserCannotOwn(Exception):

    "The emergency user cannot own anything"


class EditUnowned(Exception):

    "Can't edit unowned executables"


def absattr(attr):
    if callable(attr): return attr()
    return attr

def ownerInfo(user, getattr=getattr):
    if user is None:
        return None
    uid=user.getId()
    if uid is None: return uid
    db=aq_parent(aq_inner(user))
    path=[absattr(db.id)]
    root=db.getPhysicalRoot()
    while 1:
        db=getattr(db,'aq_inner', None)
        if db is None: break
        db=aq_parent(db)
        if db is root: break
        id=db.id
        if not isinstance(id, str):
            try: id=id()
            except: id=str(id)
        path.append(id)

    path.reverse()

    return path, uid
