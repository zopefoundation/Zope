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
"""Class initialization.
"""

from zope.deferredimport import deprecated


# BBB Zope 5.0
deprecated(
    'Please import from AccessControl.Permission.',
    ApplicationDefaultPermissions=(
        'AccessControl.Permission:ApplicationDefaultPermissions'),
)

deprecated(
    'Please import from AccessControl.class_init.',
    default__class_init__='AccessControl.class_init:InitializeClass',
    InitializeClass='AccessControl.class_init:InitializeClass',
)
