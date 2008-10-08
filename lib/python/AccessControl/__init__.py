##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from unauthorized import Unauthorized

# This has to happen early so things get initialized properly
from AccessControl.Implementation import setImplementation

from AccessControl.SecurityManagement import getSecurityManager, setSecurityPolicy
from AccessControl.SecurityInfo import ClassSecurityInfo, ModuleSecurityInfo
from AccessControl.SecurityInfo import ACCESS_PRIVATE
from AccessControl.SecurityInfo import ACCESS_PUBLIC
from AccessControl.SecurityInfo import ACCESS_NONE
from AccessControl.SecurityInfo import secureModule, allow_module, allow_class
from AccessControl.SimpleObjectPolicies import allow_type
from AccessControl.ZopeGuards import full_write_guard, safe_builtins

ModuleSecurityInfo('AccessControl').declarePublic('getSecurityManager')

from AccessControl import DTML
del DTML
