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
"""Support for owned objects

$Id$
"""

import Globals, urlparse, SpecialUsers, ExtensionClass
from AccessControl import getSecurityManager, Unauthorized
from Acquisition import aq_get, aq_parent, aq_base
from requestmethod import postonly


UnownableOwner=[]
def ownableFilter(self):
    _owner = aq_get(self, '_owner', None, 1)
    return _owner is not UnownableOwner

# Marker to use as a getattr default.
_mark=ownableFilter

class Owned(ExtensionClass.Base):

    __ac_permissions__=(
        ('View management screens',
         ('manage_owner', 'owner_info')),
        ('Take ownership',
         ('manage_takeOwnership','manage_changeOwnershipType'),
         ("Owner",)),
        )

    manage_options=({'label':  'Ownership',
                     'action': 'manage_owner',
                     'help':   ('OFSP','Ownership.stx'),
                     'filter': ownableFilter
                     },
                   )

    manage_owner=Globals.DTMLFile('dtml/owner', globals())

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

    getOwner__roles__=()
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
            user = SpecialUsers.nobody
        else:
            user = udb.getUserById(oid, None)
            if user is None: user = SpecialUsers.nobody
        return user

    getOwnerTuple__roles__=()
    def getOwnerTuple(self):
        """Return a tuple, (userdb_path, user_id) for the owner.

        o Ownership can be acquired, but only from the containment path.

        o If unowned, return None.
        """
        return aq_get(self, '_owner', None, 1)

    getWrappedOwner__roles__=()
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
            return SpecialUsers.nobody

        user = udb.getUserById(oid, None)

        if user is None:
            return SpecialUsers.nobody

        return user.__of__(udb)

    changeOwnership__roles__=()
    def changeOwnership(self, user, recursive=0):
        """Change the ownership to the given user.

        If 'recursive' is true then also take ownership of all sub-objects,
        otherwise sub-objects retain their ownership information.
        """

        new=ownerInfo(user)
        if new is None: return # Special user!
        old = self.getOwnerTuple()
        if not recursive:
            if old==new: return
            if old is UnownableOwner: return

        for child in self.objectValues():
            if recursive:
                child.changeOwnership(user, 1)
            else:
                # make ownership explicit
                child._owner=new

        if old is not UnownableOwner:
            self._owner=new

    def userCanTakeOwnership(self):
        security=getSecurityManager()
        user=security.getUser()
        info=ownerInfo(user)
        if info is None: return 0
        owner=self.getOwnerTuple()
        if owner == info: return 0
        return security.checkPermission('Take ownership', self)

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
    manage_takeOwnership = postonly(manage_takeOwnership)

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
    manage_changeOwnershipType = postonly(manage_changeOwnershipType)

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
        parent=getattr(self, 'aq_parent', None)
        if parent is not None: _owner=aq_get(parent, '_owner', None, 1)
        else: _owner=None

        if (_owner is None and
            ((not hasattr(self, 'aq_parent')) or
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
            if (SpecialUsers.emergency_user and
                aq_base(user) is SpecialUsers.emergency_user):
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

Globals.default__class_init__(Owned)


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
    db=user.aq_inner.aq_parent
    path=[absattr(db.id)]
    root=db.getPhysicalRoot()
    while 1:
        db=getattr(db,'aq_inner', None)
        if db is None: break
        db=db.aq_parent
        if db is root: break
        id=db.id
        if not isinstance(id, str):
            try: id=id()
            except: id=str(id)
        path.append(id)

    path.reverse()

    return path, uid
