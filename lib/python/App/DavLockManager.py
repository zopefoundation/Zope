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

__version__ = "$Revision: 1.5 $"[11:-2]

import OFS, Acquisition, Globals
from AccessControl import getSecurityManager, ClassSecurityInfo
from webdav.Lockable import wl_isLocked

class DavLockManager(OFS.SimpleItem.Item, Acquisition.Implicit):
    id           = 'DavLockManager'
    name = title = 'WebDAV Lock Manager'
    meta_type    = 'WebDAV Lock Manager'
    icon = 'p_/davlocked'

    security = ClassSecurityInfo()
    security.declareProtected('Manage WebDAV Locks',
                              'findLockedObjects', 'manage_davlocks',
                              'manage_unlockObjects')
    security.declarePrivate('unlockObjects')

    manage_davlocks=manage_main=manage=Globals.DTMLFile(
        'dtml/davLockManager', globals())
    manage_davlocks._setName('manage_davlocks')

    manage_options = (
        {'label': 'Write Locks', 'action': 'manage_main',
         'help': ('OFSP', 'DavLocks-ManageLocks.stx'), },
        )
    
    def locked_in_version(self): return 0

    def findLockedObjects(self, frompath=''):
        app = self.getPhysicalRoot()

        if frompath:
            if frompath[0] == '/': frompath = frompath[1:]
            # since the above will turn '/' into an empty string, check
            # for truth before chopping a final slash
            if frompath and frompath[-1] == '/': frompath= frompath[:-1]

        # Now we traverse to the node specified in the 'frompath' if
        # the user chose to filter the search, and run a ZopeFind with
        # the expression 'wl_isLocked()' to find locked objects.
        obj = app.unrestrictedTraverse(frompath)
        lockedobjs = self._findapply(obj, path=frompath)

        return lockedobjs

    def unlockObjects(self, paths=[]):
        app = self.getPhysicalRoot()

        for path in paths:
            ob = app.unrestrictedTraverse(path)
            ob.wl_clearLocks()

    def manage_unlockObjects(self, paths=[], REQUEST=None):
        " Management screen action to unlock objects. "
        if paths: self.unlockObjects(paths)
        if REQUEST is not None:
            m = '%s objects unlocked.' % len(paths)
            return self.manage_davlocks(self, REQUEST, manage_tabs_message=m)

    def _findapply(self, obj, result=None, path=''):
        # recursive function to actually dig through and find the locked
        # objects.

        if result is None:
            result = []
        base = Acquisition.aq_base(obj)
        if not hasattr(base, 'objectItems'):
            return result
        try: items = obj.objectItems()
        except: return result

        addresult = result.append
        for id, ob in items:
            if path: p = '%s/%s' % (path, id)
            else: p = id

            dflag = hasattr(ob, '_p_changed') and (ob._p_changed == None)
            bs = Acquisition.aq_base(ob)
            if wl_isLocked(ob):
                li = []
                addlockinfo = li.append
                for token, lock in ob.wl_lockItems():
                    addlockinfo({'owner':lock.getCreatorPath(),
                                 'token':token})
                addresult(p, li)
                dflag = 0
            if hasattr(bs, 'objectItems'):
                self._findapply(ob, result, p)
            if dflag: ob._p_deactivate()

        return result

    
Globals.default__class_init__(DavLockManager)
