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
"""

import urlparse

from Acquisition import aq_get
from Acquisition import aq_parent

from App.special_dtml import DTMLFile

from AccessControl.class_init import InitializeClass
from AccessControl.owner import Owned as BaseOwned
from AccessControl.owner import ownableFilter
from AccessControl.owner import UnownableOwner
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import take_ownership
from AccessControl.requestmethod import requestmethod
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.unauthorized import Unauthorized


class Owned(BaseOwned):

    security = ClassSecurityInfo()
    security.setPermissionDefault(take_ownership, ('Owner', ))

    manage_options=({'label': 'Ownership',
                     'action': 'manage_owner',
                     'filter': ownableFilter},
                   )

    security.declareProtected(view_management_screens, 'manage_owner')
    manage_owner = DTMLFile('dtml/owner', globals())

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
            raise Unauthorized(
                'manage_takeOwnership was called from an invalid context')

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
            if old is not None:
                return
            owner = self.getOwnerTuple()
            if owner is not None and owner is not UnownableOwner:
                self._owner=owner
        else:
            if old is None:
                return
            new = aq_get(aq_parent(self), '_owner', None, 1)
            _m = object()
            if old is new and (self.__dict__.get('_owner', _m) is not _m):
                del self._owner

        if RESPONSE is not None:
            RESPONSE.redirect(REQUEST['HTTP_REFERER'])

InitializeClass(Owned)
