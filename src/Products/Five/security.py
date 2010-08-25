##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Five security handling
"""

from zope.deferredimport import deprecated

deprecated("Please import InitializeClass from App.class_init",
    initializeClass = 'App.class_init:InitializeClass',
)

deprecated("Please import from AccessControl.security",
    CheckerPublicId = 'AccessControl.security:CheckerPublicId',
    CheckerPrivateId = 'AccessControl.security:CheckerPrivateId',
    getSecurityInfo = 'AccessControl.security:getSecurityInfo',
    clearSecurityInfo = 'AccessControl.security:clearSecurityInfo',
    checkPermission = 'AccessControl.security:checkPermission',
    FiveSecurityPolicy = 'AccessControl.security:SecurityPolicy',
    newInteraction = 'AccessControl.security:newInteraction',
    _getSecurity = 'AccessControl.security:_getSecurity',
    protectName = 'AccessControl.security:protectName',
    protectClass = 'AccessControl.security:protectClass',
)
