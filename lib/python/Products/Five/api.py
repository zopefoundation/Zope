##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Convenience package for short imports

$Id: api.py 6174 2004-08-25 17:19:28Z faassen $
"""

import warnings

warnings.warn('The use of the Products.Five.api module has been deprecated. '
              'Import directly from Products.Five instead for public API.',
              DeprecationWarning)

from browser import BrowserView, StandardMacros
from traversable import Traversable
from viewable import Viewable
