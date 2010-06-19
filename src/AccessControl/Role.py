##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Access control support
"""

# BBB
from .rolemanager import DEFAULTMAXLISTUSERS
from .rolemanager import _isBeingUsedAsAMethod
from .rolemanager import _isNotBeingUsedAsAMethod
from .rolemanager import reqattr
from .rolemanager import classattr
from .rolemanager import instance_dict
from .rolemanager import class_dict
from .rolemanager import instance_attrs
from .rolemanager import class_attrs
from .rolemanager import gather_permissions

from zope.deferredimport import deprecated
deprecated("RoleManager is no longer part of AccessControl, please "
           "depend on Zope2 and import from OFS.role or use the new minimal "
           "RoleManager class from AccessControl.rolemanager.",
    RoleManager = 'OFS.role:RoleManager',
)
