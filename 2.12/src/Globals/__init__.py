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
"""Shared global data

o N.B.:  DO NOT IMPORT ANYTHING HERE!  This module is just for shared data!
"""
__version__='$Revision: 1.56 $'[11:-2]

# BBB imports
from zope.deferredimport import deprecated

deprecated("import TreeDisplay directly",
           TreeDisplay = "TreeDisplay",
          )

deprecated("import from App.Common instead",
           package_home = 'App.Common:package_home',
           attrget = 'App.Common:attrget',
           Dictionary = 'App.Common:Dictionary',
          )

deprecated("import from Persistence instead",
           Persistent = 'Persistence:Persistent',
           PersistentMapping = 'Persistence:PersistentMapping',
          )

deprecated("import from App.class_init instead",
           InitializeClass = 'App.class_init:InitializeClass',
          )

deprecated("import from AccessControl.Permission instead",
           ApplicationDefaultPermissions =
                'AccessControl.Permission:ApplicationDefaultPermissions',
          )

deprecated("import from App.special_dtml instead",
           HTML = 'App.special_dtml:HTML',
           HTMLFile = 'App.special_dtml:HTMLFile',
           DTMLFile = 'App.special_dtml:DTMLFile',
          )

deprecated("import from App.Dialogs instead",
           MessageDialog = 'App.Dialogs:MessageDialog',
          )

deprecated("import from App.ImageFile instead",
           ImageFile = 'App.ImageFile:ImageFile',
          )

deprecated("import from OFS.ObjectManager instead",
           UNIQUE = 'OFS.ObjectManager:UNIQUE',
           REPLACEABLE = 'OFS.ObjectManager:REPLACEABLE',
           NOT_REPLACEABLE = 'OFS.ObjectManager:NOT_REPLACEABLE',
          )

del deprecated

DevelopmentMode = False

# XXX ZODB stashes the main database object here
opened = []
