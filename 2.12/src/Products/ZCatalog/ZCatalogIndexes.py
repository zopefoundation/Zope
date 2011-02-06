##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Virtual container for ZCatalog indexes.

$Id$
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.Permissions import manage_zcatalog_indexes
from Acquisition import Implicit
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.Folder import Folder
from OFS.ObjectManager import IFAwareObjectManager
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from Products.PluginIndexes.interfaces import IPluggableIndex

_marker = []


class ZCatalogIndexes(IFAwareObjectManager, Folder, Persistent, Implicit):

    """A mapping object, responding to getattr requests by looking up
    the requested indexes in an object manager."""

    # The interfaces we want to show up in our object manager
    _product_interfaces = (IPluggableIndex,)

    meta_type = "ZCatalogIndex"
    manage_options = ()

    security = ClassSecurityInfo()

    security.declareObjectProtected(manage_zcatalog_indexes)
    security.setPermissionDefault(manage_zcatalog_indexes, ('Manager',))
    security.declareProtected(manage_zcatalog_indexes, 'addIndexForm')
    addIndexForm= DTMLFile('dtml/addIndexForm',globals())

    # You no longer manage the Indexes here, they are managed from ZCatalog
    def manage_main(self, REQUEST, RESPONSE):
        """Redirect to the parent where the management screen now lives"""
        RESPONSE.redirect('../manage_catalogIndexes')

    manage_workspace = manage_main

    #
    # Object Manager methods
    #

    # base accessors loop back through our dictionary interface
    def _setOb(self, id, object):
        indexes = self.aq_parent._catalog.indexes
        indexes[id] = object
        self.aq_parent._indexes = indexes
        #self.aq_parent._p_changed = 1

    def _delOb(self, id):
        indexes = self.aq_parent._catalog.indexes
        del indexes[id]
        self.aq_parent._indexes = indexes
        #self.aq_parent._p_changed = 1

    def _getOb(self, id, default=_marker):
        indexes = self.aq_parent._catalog.indexes
        if default is _marker:  return indexes.get(id)
        return indexes.get(id, default)

    security.declareProtected(manage_zcatalog_indexes, 'objectIds')
    def objectIds(self, spec=None):

        indexes = self.aq_parent._catalog.indexes
        if spec is not None:
            if type(spec) == type('s'):
                spec = [spec]
            set = []

            for ob in indexes.keys():
                o = indexes.get(ob)
                if hasattr(o, 'meta_type') and getattr(o,'meta_type') in spec:
                    set.append(ob)

            return set

        return indexes.keys()

    # Eat _setObject calls
    def _setObject(self, id, object, roles=None, user=None, set_owner=1):
        pass

    #
    # traversal
    #

    def __bobo_traverse__(self, REQUEST, name):
        indexes = self.aq_parent._catalog.indexes;

        o = indexes.get(name, None)
        if o is not None:
            if getattr(o,'manage_workspace', None) is None:
                o = OldCatalogWrapperObject(o)
            return o.__of__(self)

        return getattr(self, name)

InitializeClass(ZCatalogIndexes)


class OldCatalogWrapperObject(SimpleItem, Implicit):

    manage_options= (
        {'label': 'Settings',
         'action': 'manage_main'},
    )

    manage_main = DTMLFile('dtml/manageOldindex',globals())
    manage_main._setName('manage_main')
    manage_workspace = manage_main

    def __init__(self, o):
        self.index = o
