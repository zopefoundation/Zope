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

from  Globals import DTMLFile
import Globals
from OFS.Folder import Folder
from OFS.FindSupport import FindSupport
from OFS.History import Historical
from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager, IFAwareObjectManager

import os, sys, time

from Acquisition import Implicit
from Persistence import Persistent
from zLOG import LOG, ERROR

from Products.PluginIndexes.common.PluggableIndex import PluggableIndexInterface

_marker = []

class ZCatalogIndexes (IFAwareObjectManager, Folder, Persistent, Implicit):
    """A mapping object, responding to getattr requests by looking up
    the requested indexes in an object manager."""

    # The interfaces we want to show up in our object manager
    _product_interfaces = (PluggableIndexInterface, )

    meta_type="ZCatalogIndex"
#    icon="misc_/ZCatalog/www/index.gif"

    manage_options = (
        ObjectManager.manage_options +
        Historical.manage_options +
        SimpleItem.manage_options
    )

    manage_main = DTMLFile('dtml/manageIndex',globals())
    addIndexForm= DTMLFile('dtml/addIndexForm',globals())

    __ac_permissions__ = (

        ('Manage ZCatalogIndex Entries',
            ['manage_foobar',],

            ['Manager']
        ),

        ('Search ZCatalogIndex',
            ['searchResults', '__call__', 'all_meta_types',
             'valid_roles', 'getobject'],

            ['Anonymous', 'Manager']
        )
    )


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


