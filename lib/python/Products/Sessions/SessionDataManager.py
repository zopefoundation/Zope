############################################################################
# 
# Zope Public License (ZPL) Version 1.1
# -------------------------------------
# 
# Copyright (c) Zope Corporation.  All rights reserved.
# 
# This license has been certified as open source.
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
# 3. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Zope Corporation 
#      for use in the Z Object Publishing Environment
#      (http://www.zope.com/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 4. Names associated with Zope or Zope Corporation must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Zope Corporation.
# 
# 5. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Zope Corporation
#      for use in the Z Object Publishing Environment
#      (http://www.zope.com/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 6. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY ZOPE CORPORATION ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL ZOPE CORPORATION OR ITS
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
# This software consists of contributions made by Zope Corporation and
# many individuals on behalf of Zope Corporation.  Specific
# attributions are listed in the accompanying credits file.
#
############################################################################

import re, time, string, sys
import Globals
from OFS.SimpleItem import Item
from Acquisition import Implicit, Explicit, aq_base
from Persistence import Persistent
from AccessControl.Owned import Owned
from AccessControl.Role import RoleManager
from App.Management import Tabs
from zLOG import LOG, WARNING
from AccessControl import ClassSecurityInfo
import SessionInterfaces
from SessionPermissions import *
from common import DEBUG
from ZPublisher.BeforeTraverse import registerBeforeTraverse, \
    unregisterBeforeTraverse
import traceback

BID_MGR_NAME = 'browser_id_manager'

bad_path_chars_in=re.compile('[^a-zA-Z0-9-_~\,\. \/]').search

class SessionDataManagerErr(Exception): pass

constructSessionDataManagerForm = Globals.DTMLFile('dtml/addDataManager',
    globals())

ADD_SESSION_DATAMANAGER_PERM="Add Session Data Manager"

def constructSessionDataManager(self, id, title='', path=None, automatic=None,
                                REQUEST=None):
    """ """
    ob = SessionDataManager(id, path, title, automatic)
    self._setObject(id, ob)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class SessionDataManager(Item, Implicit, Persistent, RoleManager, Owned, Tabs):
    """ The Zope default session data manager implementation """

    meta_type = 'Session Data Manager'

    manage_options=(
        {'label': 'Settings',
         'action':'manage_sessiondatamgr',
         },
        {'label': 'Security',
         'action':'manage_access',
         },
        {'label': 'Ownership',
         'action':'manage_owner'
         },
        )

    security = ClassSecurityInfo()

    security.setDefaultAccess('deny')
    security.setPermissionDefault(CHANGE_DATAMGR_PERM, ['Manager'])
    security.setPermissionDefault(MGMT_SCREEN_PERM, ['Manager'])
    security.setPermissionDefault(ACCESS_CONTENTS_PERM,['Manager','Anonymous'])
    security.setPermissionDefault(ARBITRARY_SESSIONDATA_PERM,['Manager'])
    security.setPermissionDefault(ACCESS_SESSIONDATA_PERM,
                                  ['Manager','Anonymous'])

    icon='misc_/CoreSessionTracking/datamgr.gif'

    __implements__ = (SessionInterfaces.SessionDataManagerInterface, )

    manage_sessiondatamgr = Globals.DTMLFile('dtml/manageDataManager',
        globals())

    # INTERFACE METHODS FOLLOW

    security.declareProtected(ACCESS_SESSIONDATA_PERM, 'getSessionData')
    def getSessionData(self, create=1):
        """ """
        key = self.getBrowserIdManager().getToken(create=create)
        if key is not None:
            return self._getSessionDataObject(key)

    security.declareProtected(ACCESS_SESSIONDATA_PERM, 'hasSessionData')
    def hasSessionData(self):
        """ """
        if self.getBrowserIdManager().getToken(create=0):
            if self._hasSessionDataObject(key):
                return 1

    security.declareProtected(ARBITRARY_SESSIONDATA_PERM,'getSessionDataByKey')
    def getSessionDataByKey(self, key):
        return self._getSessionDataObjectByKey(key)
    
    security.declareProtected(ACCESS_CONTENTS_PERM, 'getBrowserIdManager')
    def getBrowserIdManager(self):
        """ """
        mgr = getattr(self, BID_MGR_NAME, None)
        if mgr is None:
            raise SessionDataManagerErr,(
                'No browser id manager named %s could be found.' % BID_MGR_NAME
                )
        return mgr

    # END INTERFACE METHODS
    
    def __init__(self, id, path=None, title='', automatic=None):
        self.id = id
        self.setContainerPath(path)
        self.setTitle(title)

        if automatic:
            self._requestSessionName='SESSION'
        else:
            self._requestSessionName=None

    security.declareProtected(CHANGE_DATAMGR_PERM, 'manage_changeSDM')
    def manage_changeSDM(self, title, path=None, automatic=None, REQUEST=None):
        """ """
        self.setContainerPath(path)
        self.setTitle(title)
        if automatic:
            self.updateTraversalData('SESSION')
        else:
            self.updateTraversalData(None)
        if REQUEST is not None:
            return self.manage_sessiondatamgr(self, REQUEST)

    security.declareProtected(CHANGE_DATAMGR_PERM, 'setTitle')
    def setTitle(self, title):
        """ """
        if not title: self.title = ''
        else: self.title = str(title)

    security.declareProtected(CHANGE_DATAMGR_PERM, 'setContainerPath')
    def setContainerPath(self, path=None):
        """ """
        if not path:
            self.obpath = None # undefined state
        elif type(path) is type(''):
            if bad_path_chars_in(path):
                raise SessionDataManagerErr, (
                    'Container path contains characters invalid in a Zope '
                    'object path'
                    )
            self.obpath = string.split(path, '/')
        elif type(path) in (type([]), type(())):
            self.obpath = list(path) # sequence
        else:
            raise SessionDataManagerErr, ('Bad path value %s' % path)
            
    security.declareProtected(MGMT_SCREEN_PERM, 'getContainerPath')
    def getContainerPath(self):
        """ """
        if self.obpath is not None:
            return string.join(self.obpath, '/')
        return '' # blank string represents undefined state
    
    def _hasSessionDataObject(self, key):
        """ """
        c = self._getSessionDataContainer()
        return c.has_key(key)

    def _getSessionDataObject(self, key):
        """ returns new or existing session data object """
        container = self._getSessionDataContainer()
        ob = container.new_or_existing(key)
        return ob.__of__(self)

    def _getSessionDataObjectByKey(self, key):
        """ returns new or existing session data object """
        container = self._getSessionDataContainer()
        ob = container.get(key)
        if ob is not None:
            return ob.__of__(self)

    def _getSessionDataContainer(self):
        """ Do not cache the results of this call.  Doing so breaks the
        transactions for mounted storages. """
        if self.obpath is None:
            err = 'Session data container is unspecified in %s' % self.getId()
            if DEBUG:
                LOG('Session Tracking', 0, err)
            raise SessionIdManagerErr, err
        # return an external data container
        try:
            # This should arguably use restrictedTraverse, but it
            # currently fails for mounted storages.  This might
            # be construed as a security hole, albeit a minor one.
            # unrestrictedTraverse is also much faster.
            if DEBUG and not hasattr(self, '_v_wrote_dc_type'):
                args = string.join(self.obpath, '/')
                LOG('Session Tracking', 0,
                    'External data container at %s in use' % args)
                self._v_wrote_dc_type = 1
            return self.unrestrictedTraverse(self.obpath)
        except:
            raise SessionDataManagerErr, (
                "External session data container '%s' not found." %
                string.join(self.obpath,'/')
                )

    security.declareProtected(MGMT_SCREEN_PERM, 'getAutomatic')
    def getAutomatic(self):
        """ """
        if hasattr(self,'_hasTraversalHook'): return 1
        return 0

    def manage_afterAdd(self, item, container):
        """ Add our traversal hook """
        self.updateTraversalData(self._requestSessionName)

    def manage_beforeDelete(self, item, container):
        """ Clean up on delete """
        self.updateTraversalData(None)

    def updateTraversalData(self, requestSessionName=None):
        # Note this cant be called directly at add -- manage_afterAdd will work
        # though.

        parent = self.aq_inner.aq_parent

        if getattr(self,'_hasTraversalHook', None):
            unregisterBeforeTraverse(parent, 'SessionDataManager')
            del self._hasTraversalHook
            self._requestSessionName = None

        if requestSessionName:
            hook = SessionDataManagerTraverser(requestSessionName, self)
            registerBeforeTraverse(parent, hook, 'SessionDataManager', 50)
            self._hasTraversalHook = 1
            self._requestSessionName = requestSessionName

class SessionDataManagerTraverser:
    def __init__(self, requestSessionName, sdm):
        self._requestSessionName = requestSessionName
        self._sessionDataManager = sdm
        self._v_errors=0

    def __call__(self, container, request):
        sdm = self._sessionDataManager.__of__(container)
        # Yank our session & stuff into request
        try:
            session = sdm.getSessionData
            self._v_errors = 0
        except:
            errors = getattr(self,"_v_errors", 0)
            if errors < 4:
                LOG('Session Tracking', WARNING,'Session automatic traversal '
                    'failed to get session data', error=sys.exc_info())
            if errors == 3:
                LOG('Session Tracking', WARNING, 'Suppressing further '
                    'automatic session failure error messages on this thread')
            self._v_errors = errors + 1
            return    # Throw our hands up but dont fail 
        if self._requestSessionName is not None:
            request.set_lazy(self._requestSessionName, session)

