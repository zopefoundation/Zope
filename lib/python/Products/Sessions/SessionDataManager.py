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

BID_MGR_NAME = 'browser_id_manager'

bad_path_chars_in=re.compile('[^a-zA-Z0-9-_~\,\. \/]').search

class SessionDataManagerErr(Exception): pass

constructSessionDataManagerForm = Globals.DTMLFile('addDataManager', globals())

def constructSessionDataManager(self, id, title='', path=None)
    """ """
    ob = SessionDataManager(id, path, title)
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

    manage_sessiondatamgr = Globals.DTMLFile('manageDataManager', globals())

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
    
    def __init__(self, id, path=None, title=''):
        self.id = id
        self.setContainerPath(path)
        self.setTitle(title)

    security.declareProtected(CHANGE_DATAMGR_PERM, 'manage_changeSDM')
    def manage_changeSDM(self, title, path=None, REQUEST=None):
        """ """
        self.setContainerPath(path)
        self.setTitle(title)
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

            
