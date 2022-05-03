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

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import webdav_manage_locks
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_base
from App.special_dtml import DTMLFile
from OFS.Lockable import wl_isLocked
from OFS.SimpleItem import Item


class DavLockManager(Item, Implicit):
    id = 'DavLockManager'
    name = title = 'WebDAV Lock Manager'
    meta_type = 'WebDAV Lock Manager'
    zmi_icon = 'fa fa-lock'

    security = ClassSecurityInfo()

    security.declareProtected(webdav_manage_locks,  # NOQA: D001
                              'manage_davlocks')
    manage_davlocks = manage_main = manage = manage_workspace = DTMLFile(
        'dtml/davLockManager', globals())
    manage_davlocks._setName('manage_davlocks')
    manage_options = (
        {'label': 'Control Panel', 'action': '../manage_main'},
        {'label': 'Databases', 'action': '../Database/manage_main'},
        {'label': 'Configuration', 'action': '../Configuration/manage_main'},
        {'label': 'DAV Locks', 'action': 'manage_main'},
        {'label': 'Debug Information', 'action': '../DebugInfo/manage_main'},
    )

    @security.protected(webdav_manage_locks)
    def findLockedObjects(self, frompath=''):
        app = self.getPhysicalRoot()

        if frompath:
            if frompath[0] == '/':
                frompath = frompath[1:]
            # since the above will turn '/' into an empty string, check
            # for truth before chopping a final slash
            if frompath and frompath[-1] == '/':
                frompath = frompath[:-1]

        # Now we traverse to the node specified in the 'frompath' if
        # the user chose to filter the search, and run a ZopeFind with
        # the expression 'wl_isLocked()' to find locked objects.
        obj = app.unrestrictedTraverse(frompath)
        lockedobjs = self._findapply(obj, path=frompath)

        return lockedobjs

    @security.private
    def unlockObjects(self, paths=[]):
        app = self.getPhysicalRoot()

        for path in paths:
            ob = app.unrestrictedTraverse(path)
            ob.wl_clearLocks()

    @security.protected(webdav_manage_locks)
    def manage_unlockObjects(self, paths=[], REQUEST=None):
        " Management screen action to unlock objects. "
        if paths:
            self.unlockObjects(paths)
        if REQUEST is not None:
            m = '%s objects unlocked.' % len(paths)
            return self.manage_davlocks(self, REQUEST, manage_tabs_message=m)

    def _findapply(self, obj, result=None, path=''):
        # recursive function to actually dig through and find the locked
        # objects.

        if result is None:
            result = []
        base = aq_base(obj)
        if not hasattr(base, 'objectItems'):
            return result
        try:
            items = obj.objectItems()
        except Exception:
            return result

        addresult = result.append
        for id, ob in items:
            if path:
                p = f'{path}/{id}'
            else:
                p = id

            dflag = hasattr(ob, '_p_changed') and (ob._p_changed is None)
            bs = aq_base(ob)
            if wl_isLocked(ob):
                li = []
                addlockinfo = li.append
                for token, lock in ob.wl_lockItems():
                    addlockinfo({'owner': lock.getCreatorPath(),
                                 'token': token})
                addresult((p, li))
                dflag = 0
            if hasattr(bs, 'objectItems'):
                self._findapply(ob, result, p)
            if dflag:
                ob._p_deactivate()

        return result


InitializeClass(DavLockManager)
