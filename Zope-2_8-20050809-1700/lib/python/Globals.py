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

"""Global definitions"""

__version__='$Revision: 1.56 $'[11:-2]

# Global constants: __replaceable__ flags:
NOT_REPLACEABLE = 0
REPLACEABLE = 1
UNIQUE = 2

import Acquisition, ComputedAttribute, App.PersistentExtra, os
import TreeDisplay

from App.Common import package_home, attrget, Dictionary
from App.config import getConfiguration as _getConfiguration
from Persistence import Persistent, PersistentMapping
from App.special_dtml import HTML, HTMLFile, DTMLFile
from App.class_init import default__class_init__, ApplicationDefaultPermissions

# Nicer alias for class initializer.
InitializeClass = default__class_init__

from App.Dialogs import MessageDialog
from App.ImageFile import ImageFile

VersionNameName='Zope-Version'

_cfg = _getConfiguration()
data_dir = _cfg.clienthome

# backward compatibility
INSTANCE_HOME = _cfg.instancehome
SOFTWARE_HOME = _cfg.softwarehome
ZOPE_HOME = _cfg.zopehome

opened=[]

DevelopmentMode=_cfg.debug_mode

del _cfg, _getConfiguration

