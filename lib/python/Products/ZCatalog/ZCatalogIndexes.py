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

from  Globals import DTMLFile
import Globals
from OFS.Folder import Folder
from OFS.FindSupport import FindSupport
from OFS.History import Historical
from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager, IFAwareObjectManager

import string, os, sys, time

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
    manage_workspace = manage_main

    def __init__(self, o):
        self.index = o


