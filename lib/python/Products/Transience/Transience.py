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
"""
Core session tracking SessionData class.

$Id: Transience.py,v 1.2 2001/10/22 16:23:51 matt Exp $
"""

__version__='$Revision: 1.2 $'[11:-2]

import Globals
from Globals import HTMLFile, MessageDialog
from TransienceInterfaces import Transient, DictionaryLike, ItemWithId,\
     TTWDictionary, ImmutablyValuedMappingOfPickleableObjects,\
     StringKeyedHomogeneousItemContainer, TransientItemContainer
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent, PersistentMapping
from Acquisition import Implicit, aq_base
from AccessControl import ClassSecurityInfo
import os.path
import time

_notfound = []

# permissions
ADD_DATAMGR_PERM = 'Add Transient Object Container'
CHANGE_DATAMGR_PERM = 'Change Transient Object Containers'
MGMT_SCREEN_PERM = 'View management screens'
ACCESS_CONTENTS_PERM = 'Access contents information'
ACCESS_SESSIONDATA_PERM = 'Access Transient Objects'
MANAGE_CONTAINER_PERM = 'Manage Transient Object Container'


constructTransientObjectContainerForm = HTMLFile(
    'dtml/addTransientObjectContainer', globals())

def constructTransientObjectContainer(self, id, title='', timeout_mins=20,
    addNotification=None, delNotification=None,
    REQUEST=None):

    """ """
    ob = TransientObjectContainer(id, title, timeout_mins,
        addNotification, delNotification)
    self._setObject(id, ob)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class TransientObjectContainer(SimpleItem):
    """ akin to Session Data Container """

    meta_type = "Transient Object Container"

    icon = "misc_/Transience/datacontainer.gif"

    __implements__ = (ItemWithId,
                      StringKeyedHomogeneousItemContainer,
                      TransientItemContainer
                      )


    manage_options = (
        {   'label':    'Manage',
            'action':   'manage_container',
            'help':     ('Transience', 'Transience.stx')
        }, 

        {   'label':    'Security',
            'action':   'manage_access'
        },

        {   'label':    'Advanced',
            'action':   'manage_advanced'
        }
    )

    security = ClassSecurityInfo()

    security.setPermissionDefault(MANAGE_CONTAINER_PERM,
                                ['Manager',])
    security.setPermissionDefault(MGMT_SCREEN_PERM,
                                ['Manager',])
    security.setPermissionDefault(ACCESS_CONTENTS_PERM,
                                ['Manager','Anonymous'])
    security.setPermissionDefault(ACCESS_SESSIONDATA_PERM,
                                ['Manager','Anonymous'])

    security.declareProtected(MGMT_SCREEN_PERM, 'manage_container')
    manage_container = HTMLFile('dtml/manageTransientObjectContainer',
        globals())

    security.declareProtected(MGMT_SCREEN_PERM, 'manage_advanced')
    manage_advanced = HTMLFile('dtml/manageImpExpTransientObjects', globals())

    security.setDefaultAccess('deny')

    #
    # Initializer
    #

    def __init__(self, id, title='', timeout_mins=20, addNotification=None,
        delNotification=None):

        self.id = id
        self.title=title
        self._container = {}
        self._addCallback = None
        self._delCallback = None
        self.setTimeoutMinutes(timeout_mins)

        self.setAddNotificationTarget(addNotification)
        self.setDelNotificationTarget(delNotification)

    # -----------------------------------------------------------------
    # ItemWithID
    #

    def getId(self):
        return self.id

    
    # -----------------------------------------------------------------
    # StringKeyedHomogenousItemContainer
    #

    def new(self, key):

        if type(key) is not type(''):
            raise TypeError, (key, "key is not a string type")
    
        if self._container.has_key(key):
            raise KeyError, key         # Not allowed to dup keys
        
        item = TransientObject(key, parent=self)

        self._container[key] = item

        return item
        

    def new_or_existing(self, key):

        item  = self._container.get(key,_notfound)
        if item is not _notfound: return item

        return self.new(key)

    # -----------------------------------------------------------------
    # TransientItemContainer 
    #

    security.declareProtected(MANAGE_CONTAINER_PERM, 'setTimeoutMinutes')
    def setTimeoutMinutes(self, timeout_mins):
        self._timeout = timeout_mins

    security.declareProtected(MGMT_SCREEN_PERM, 'getTimeoutMinutes')
    def getTimeoutMinutes(self):
        return self._timeout

    security.declareProtected(MGMT_SCREEN_PERM, 'getAddNotificationTarget')
    def getAddNotificationTarget(self):
        # What might we do here to help through the web stuff?
        return self._addCallback

    security.declareProtected(MANAGE_CONTAINER_PERM,
        'setAddNotificationTarget')
    def setAddNotificationTarget(self, f):
        # We should assert that the callback function 'f' implements
        # the TransientNotification interface
        self._addCallback = f             

    security.declareProtected(MGMT_SCREEN_PERM, 'getDelNotificationTarget')
    def getDelNotificationTarget(self):
        # What might we do here to help through the web stuff?
        return self._delCallback

    security.declareProtected(MANAGE_CONTAINER_PERM,
        'setDelNotificationTarget')
    def setDelNotificationTarget(self, f):
        # We should assert that the callback function 'f' implements
        # the TransientNotification interface
        self._delCallback = f

    def notifyAdd(self, item):
        if self._addCallback:
            try:
                self._addCallback(item, self)   # Use self as context
            except: pass                        # Eat all errors 

    def notifyDestruct(self, item):
        if self._delCallback:
            try:
                self._delCallback(item, self)   # Use self as context
            except: pass                        # Eat all errors 

    # -----------------------------------------------------------------
    # Management item support (non API)
    #


    security.declareProtected(MGMT_SCREEN_PERM, 'getLen')
    def getLen(self):

        """
        Potentially expensive helper function to figure out how
        many items are contained.
        """
        return len(self._container)


    security.declareProtected(MANAGE_CONTAINER_PERM,
        'manage_changeTransientObjectContainer')
    def manage_changeTransientObjectContainer(self, title='',
        timeout_mins=20, addNotification=None, delNotification=None,
        REQUEST=None):

        """
        Change an existing transient object container.
        """

        self.title = title
        self.setTimeoutMinutes(timeout_mins)
        self.setAddNotificationTarget(addNotification)
        self.setDelNotificationTarget(delNotification)

        if REQUEST is not None:
            return self.manage_container(self, REQUEST)


    security.declareProtected(MANAGE_CONTAINER_PERM,
        'manage_exportTransientObjects')
    def manage_exportTransientObjects(self, REQUEST=None):
    
        """
        Export the transient objects to a named file in the var directory.
        """

        f = os.path.join(Globals.data_dir, "transientobjects.zexp")
        self.c = PersistentMapping()
        for k, v in self._container.items():
            self.c[k] = v

        get_transaction().commit()
        self.c._p_jar.exportFile(self.c._p_oid, f)
        del self.c
        if REQUEST is not None:
            return MessageDialog(
                title="Transient objects exported",
                message="Transient objects exported to %s" % f,
                action="manage_container")
        
    security.declareProtected(MANAGE_CONTAINER_PERM,
        'manage_importTransientObjects')
    def manage_importTransientObjects(self, REQUEST=None):
        """
        Import the transient objects from a zexp file.
        """
        f = os.path.join(Globals.data_dir, "transientobjects.zexp")
        conn = self._p_jar
        ob = conn.importFile(f)
        for k,v in ob.items():
            self._container[k] = v
        if REQUEST is not None:
            return MessageDialog(
                title="Transient objects imported",
                message="Transient objects imported from %s" % f,
                action="manage_container")


class TransientObject(Persistent, Implicit):
    """ akin to Session Data Object """
    __implements__ = (ItemWithId, # randomly generate an id
                      Transient,
                      DictionaryLike,
                      TTWDictionary,
                      ImmutablyValuedMappingOfPickleableObjects
                      )

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')
    security.declareObjectPublic()

    #
    # Initialzer
    #

    def __init__(self, id, parent=None, time=time.time):
        self.id = id
        self._parent = parent
        self._container = {}
        self._created = self._last_accessed = time()
        self._timergranularity = 30 # timer granularity for last accessed


    # -----------------------------------------------------------------
    # ItemWithId
    #

    def getId(self):
        return self.id

    # -----------------------------------------------------------------
    # Transient
    #

    def invalidate(self):
        parent = self._parent
        if parent: parent.notifyDestruct(self)
        self._invalid = None

    def getLastAccessed(self):
        return self._last_accessed

    def setLastAccessed(self, time=time.time):
        # check to see if the last_accessed time is too recent, and avoid
        # setting if so, to cut down on heavy writes
        t = time()
        if self._last_accessed and (self._last_accessed +
            self._timergranularity < t):

            self._last_accessed = t

    def getCreated(self):
        return self._created


    # -----------------------------------------------------------------
    # DictionaryLike
    #


    def keys(self):
        return self._container.keys()

    def values(self):
        return self._container.values()

    def items(self):
        return self._container.items()

    def get(self, k, default=None):
        return self._container.get(k, default)
        
    def has_key(self, k, marker=_notfound):
        if self._container.get(k, marker) is not _notfound: return 1

    def clear(self):
        self._container.clear()
        self._p_changed = 1

    def update(self, d):
        for k in d.keys():
            self[k] = d[k]


    # -----------------------------------------------------------------
    # ImmutablyValuedMappingOfPickleableObjects (what a mouthful!)
    #

    def __setitem__(self, k, v):
        # if the key or value is a persistent instance,
        # set up its _p_jar immediately
        if hasattr(v, '_p_jar') and v._p_jar is None:
            v._p_jar = self._p_jar
            v._p_changed = 1
        if hasattr(k, '_p_jar') and k._p_jar is None:
            k._p_jar = self._p_jar
            k._p_changed = 1
        # unwrap this thing if it's wrapped
        k = aq_base(k)
        v = aq_base(v)
        self._container[k] = v
        self._p_changed = 1

    def __getitem__(self, k):
        return self._container[k]

    def __delitem__(self, k):
        del self._container[k]

    # -----------------------------------------------------------------
    # TTWDictionary
    #

    set = __setitem__

    def delete(self, k):
        del self._container[k]
        self._p_changed = 1
        
    __guarded_setitem__ = __setitem__


    # -----------------------------------------------------------------
    # Other non interface code
    #

    def _p_independent(self):
        # My state doesn't depend on or materially effect the state of
        # other objects (eliminates read conflicts).
        return 1

    getName = getId

Globals.InitializeClass(TransientObjectContainer)
Globals.InitializeClass(TransientObject)
