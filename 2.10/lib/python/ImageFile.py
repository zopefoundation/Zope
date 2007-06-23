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
"""Image object that is stored in a file"""

__version__='$Revision: 1.13 $'[11:-2]

############################################################
# BBB 2005/11/18 -- This module will be removed in Zope 2.11
#
from App.ImageFile import ImageFile
import warnings
warnings.warn("The ImageFile module will be removed in Zope 2.11. "
              "Use App.ImageFile instead.", DeprecationWarning, stacklevel=2)
