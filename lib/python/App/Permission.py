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
__doc__='''Zope registerable permissions

$Id: Permission.py,v 1.1 1999/07/21 13:15:24 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import OFS.SimpleItem, Acquisition, Globals, ExtensionClass, AccessControl.Role

class Permission(
    AccessControl.Role.RoleManager,
    Globals.Persistent, Acquisition.Implicit, OFS.SimpleItem.Item
    ):
    "Model Permission meta-data"
    meta_type='Zope Permission'
    icon='p_/Permission_icon'

    manage_options=(
        {'label':'Edit', 'action':'manage_main'},
        {'label':'Security', 'action':'manage_access'},
    )
    
    def __init__(self, id, title, name):
        self.id=id
        self.title=title
        self.name=name

    def manage_edit(self, title, name, REQUEST=None):
        "Modify Permission properties."
        if title != self.title: self.title=title
        if name != self.name:
            self._unregister()
            self.name=name
            self._register()
        if REQUEST is not None: return self.manage_main(self, REQUEST)

    def manage_afterAdd(self, item, container):
        self._register()

    def manage_beforeDelete(self, item, container):
        self._unregister()

    def _register(self):
        # Register with the product folder
        product=self.aq_parent
        product.aq_acquire('_manage_add_product_permission')(
            product, self.name)

    def _unregister(self):
        # Unregister with the product folder
        product=self.aq_parent
        product.aq_acquire('_manage_remove_product_permission')(
            product, self.name)

    manage_main=Globals.HTMLFile('editPermission',globals())

    index_html=None

class PermissionManager(ExtensionClass.Base):

    __ac_permissions__=(
        ('Define permissions',
         ('manage_addPermissionForm', 'manage_addPermission')),
        )

    meta_types={
        'name': Permission.meta_type, 'action': 'manage_addPermissionForm'
        },

    manage_addPermissionForm=Globals.HTMLFile('addPermission',globals())
    def manage_addPermission(
        self, id, title, permission, REQUEST=None):
        ' '
        i=Permission(id, title, permission)
        self._setObject(id,i)
        if REQUEST is not None:
            return self.manage_main(self,REQUEST,update_menu=1)
    
