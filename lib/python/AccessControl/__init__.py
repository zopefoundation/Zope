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

from unauthorized import Unauthorized

# This has to happen early so things get initialized properly
from Implementation import setImplementation

from SecurityManagement import getSecurityManager, setSecurityPolicy
from SecurityInfo import ClassSecurityInfo, ModuleSecurityInfo
from SecurityInfo import ACCESS_PRIVATE
from SecurityInfo import ACCESS_PUBLIC
from SecurityInfo import ACCESS_NONE
from SecurityInfo import secureModule, allow_module, allow_class
from SimpleObjectPolicies import allow_type
from ZopeGuards import full_write_guard, safe_builtins

ModuleSecurityInfo('AccessControl').declarePublic('getSecurityManager')

import DTML
del DTML
