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
__doc__='''Support for owned objects


$Id: Owned.py,v 1.10 2001/01/12 15:23:05 chrism Exp $'''
__version__='$Revision: 1.10 $'[11:-2]

import Globals, urlparse, SpecialUsers, ExtensionClass, string
from AccessControl import getSecurityManager
from Acquisition import aq_get, aq_parent, aq_base

UnownableOwner=[]
def ownableFilter(self,
                  aq_get=aq_get,
                  UnownableOwner=UnownableOwner):
    _owner=aq_get(self, '_owner', None, 1)
    return _owner is not UnownableOwner

# Marker to use as a getattr default.
_mark=ownableFilter

class Owned(ExtensionClass.Base):

    __ac_permissions__=(
        ('View management screens',
         ('manage_owner', 'owner_info', 'userCanChangeOwnershipType')),
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
        owner=self.getOwner(1)
        if owner is None or owner is UnownableOwner: return owner
        d={'path': string.join(owner[0], '/'), 'id': owner[1],
           'explicit': hasattr(self, '_owner'),
           'userCanChangeOwnershipType':
           getSecurityManager().checkPermission('Take ownership', self)
           }
        return d
    
    getOwner__roles__=()
    def getOwner(self, info=0,
                 aq_get=aq_get, None=None, UnownableOwner=UnownableOwner,
                 ):
        """Get the owner

        If a true argument is provided, then only the owner path and id are
        returned. Otherwise, the owner object is returned.
        """
        owner=aq_get(self, '_owner', None, 1)
        if owner is None: return owner

        if info: return owner
            
        if owner is UnownableOwner: return None

        udb, oid = owner
        root=self.getPhysicalRoot()
        udb=root.unrestrictedTraverse(udb, None)
        if udb is None: return SpecialUsers.nobody
        owner = udb.getUserById(oid, None)
        if owner is None: return SpecialUsers.nobody
        return owner

    changeOwnership__roles__=()
    def changeOwnership(self, user, recursive=0,
                        aq_get=aq_get, None=None,
                        ):
        """Change the ownership to the given user.  If 'recursive' is
        true then also take ownership of all sub-objects, otherwise
        sub-objects retain their ownership information."""

        new=ownerInfo(user)
        if new is None: return # Special user!
        old=aq_get(self, '_owner', None, 1)
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
        owner=self.getOwner(1)
        if owner == info: return 0
        return security.checkPermission('Take ownership', self)

    def manage_takeOwnership(self, REQUEST, RESPONSE, recursive=0):
        """
        Take ownership (responsibility) for an object. If 'recursive'
        is true, then also take ownership of all sub-objects.
        """
        security=getSecurityManager()
        want_referer=REQUEST['URL1']+'/manage_owner'
        got_referer=("%s://%s%s" %
                     urlparse.urlparse(REQUEST['HTTP_REFERER'])[:3])
        __traceback_info__=want_referer, got_referer
        if (want_referer != got_referer or security.calledByExecutable()):
            raise 'Unauthorized', (
                'manage_takeOwnership was called from an invalid context'
                )    

        self.changeOwnership(security.getUser(), recursive)

        RESPONSE.redirect(REQUEST['HTTP_REFERER'])

    def manage_changeOwnershipType(self, explicit=1,
                                   RESPONSE=None, REQUEST=None):
        """Change the type (implicit or explicit) of ownership.
        """
        old=getattr(self, '_owner', None)
        if explicit:
            if old is not None: return
            owner=aq_get(self, '_owner', None, 1)
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
        

def ownerInfo(user,
              getattr=getattr, type=type, st=type(''), None=None):
    uid=user.getId()
    if uid is None: return uid
    db=user.aq_inner.aq_parent
    path=[db.id]
    root=db.getPhysicalRoot()
    while 1:
        db=getattr(db,'aq_inner', None)
        if db is None: break
        db=db.aq_parent
        if db is root: break
        id=db.id
        if type(id) is not st:
            try: id=id()
            except: id=str(id)
        path.append(id)

    path.reverse()

    return path, uid

