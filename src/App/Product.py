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

from AccessControl.class_init import InitializeClass
from AccessControl.owner import UnownableOwner
from OFS.Folder import Folder


class ProductFolder(Folder):
    "Manage a collection of Products"

    id = 'Products'
    name = title = 'Product Management'
    meta_type = 'Product Management'
    icon = 'p_/ProductFolder_icon'

    all_meta_types=()
    meta_types=()

    # This prevents subobjects from being owned!
    _owner = UnownableOwner

    def _product(self, name):
        return getattr(self, name)

    def _canCopy(self, op=0):
        return 0

InitializeClass(ProductFolder)
