############################################################################
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
############################################################################

import re, time, string, sys
import Globals
from OFS.SimpleItem import Item
from Acquisition import Implicit, Explicit, aq_base
from Persistence import Persistent
from AccessControl.Owned import Owned
from AccessControl.Role import RoleManager
from App.Management import Tabs
from zLOG import LOG, WARNING, BLATHER
from AccessControl import ClassSecurityInfo
import SessionInterfaces
from SessionPermissions import *
from common import DEBUG
from ZPublisher.BeforeTraverse import registerBeforeTraverse, \
    unregisterBeforeTraverse

BID_MGR_NAME = 'browser_id_manager'

bad_path_chars_in=re.compile('[^a-zA-Z0-9-_~\,\. \/]').search

class SessionDataManagerErr(Exception): pass

constructSessionDataManagerForm = Globals.DTMLFile('dtml/addDataManager',
    globals())

ADD_SESSION_DATAMANAGER_PERM="Add Session Data Manager"

def constructSessionDataManager(self, id, title='', path=None,
                                requestName=None, REQUEST=None):
    """ """
    ob = SessionDataManager(id, path, title, requestName)
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

    ok = {'meta_type':1, 'id':1, 'icon':1, 'bobobase_modification_time':1 }
    security.setDefaultAccess(ok)
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
        key = self.getBrowserIdManager().getBrowserId(create=create)
        if key is not None:
            return self._getSessionDataObject(key)

    security.declareProtected(ACCESS_SESSIONDATA_PERM, 'hasSessionData')
    def hasSessionData(self):
        """ """
        return not not self.getSessionData(create=0)

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
    
    def __init__(self, id, path=None, title='', requestName=None):
        self.id = id
        self.setContainerPath(path)
        self.setTitle(title)
        self._requestSessionName = requestName

    security.declareProtected(CHANGE_DATAMGR_PERM, 'manage_changeSDM')
    def manage_changeSDM(self, title, path=None, requestName=None,
                         REQUEST=None):
        """ """
        self.setContainerPath(path)
        self.setTitle(title)
        if requestName:
            if requestName != self._requestSessionName:
                self.updateTraversalData(requestName)
        else:
            self.updateTraversalData(None)
        if REQUEST is not None:
            return self.manage_sessiondatamgr(
                self, REQUEST, manage_tabs_message = 'Changes saved.'
                )

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
        ob = aq_base(container.new_or_existing(key))
        return ob.__of__(self)

    def _getSessionDataObjectByKey(self, key):
        """ returns new or existing session data object """
        container = self._getSessionDataContainer()
        ob = aq_base(container.get(key))
        if ob is not None:
            return ob.__of__(self)

    def _getSessionDataContainer(self):
        """ Do not cache the results of this call.  Doing so breaks the
        transactions for mounted storages. """
        if self.obpath is None:
            err = 'Session data container is unspecified in %s' % self.getId()
            LOG('Session Tracking', WARNING, err)
            raise SessionIdManagerErr, err
        try:
            # This should arguably use restrictedTraverse, but it
            # currently fails for mounted storages.  This might
            # be construed as a security hole, albeit a minor one.
            # unrestrictedTraverse is also much faster.
            if DEBUG and not hasattr(self, '_v_wrote_dc_type'):
                args = string.join(self.obpath, '/')
                LOG('Session Tracking', BLATHER,
                    'External data container at %s in use' % args)
                self._v_wrote_dc_type = 1
            return self.unrestrictedTraverse(self.obpath)
        except:
            raise SessionDataManagerErr, (
                "External session data container '%s' not found." %
                string.join(self.obpath,'/')
                )

    security.declareProtected(MGMT_SCREEN_PERM, 'getRequestName')
    def getRequestName(self):
        """ """
        return self._requestSessionName or ''

    def manage_afterAdd(self, item, container):
        """ Add our traversal hook """
        self.updateTraversalData(self._requestSessionName)

    def manage_beforeDelete(self, item, container):
        """ Clean up on delete """
        self.updateTraversalData(None)

    def updateTraversalData(self, requestSessionName=None):
        # Note this cant be called directly at add -- manage_afterAdd will
        # work though.
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

    def __call__(self, container, request):
        try:
            sdm = self._sessionDataManager.__of__(container)
            session = sdm.getSessionData
        except:
            msg = 'Session automatic traversal failed to get session data'
            LOG('Session Tracking', WARNING, msg, error=sys.exc_info())
            return
        if self._requestSessionName is not None:
            request.set_lazy(self._requestSessionName, session)

