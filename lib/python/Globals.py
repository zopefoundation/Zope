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

__version__='$Revision: 1.52 $'[11:-2]

# Global constants: __replaceable__ flags:
NOT_REPLACEABLE = 0
REPLACEABLE = 1
UNIQUE = 2

import Acquisition, ComputedAttribute, App.PersistentExtra, os
import TreeDisplay

from App.FindHomes import INSTANCE_HOME, SOFTWARE_HOME, ZOPE_HOME
from App.Common import package_home, attrget, Dictionary
from Persistence import Persistent, PersistentMapping
from App.special_dtml import HTML, HTMLFile, DTMLFile
from App.class_init import default__class_init__, ApplicationDefaultPermissions

# Nicer alias for class initializer.
InitializeClass = default__class_init__

from App.Dialogs import MessageDialog
from App.ImageFile import ImageFile

VersionNameName='Zope-Version'

data_dir = os.path.join(INSTANCE_HOME, 'var')
opened=[]

# Check,if DEBUG variables are set
DevelopmentMode=None

z1 = os.environ.get('Z_DEBUG_MODE','')
z2 = os.environ.get('BOBO_DEBUG_MODE','')

if z1.lower() in ('yes','y') or z1.isdigit():
    DevelopmentMode=1
elif z2.lower() in ('yes','y') or z2.isdigit():
    DevelopmentMode=1
