##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Legacy Zope "package" that redirects to the new Zope 2 package

$Id$
"""

import sys, Zope2
sys.modules['Zope'] = Zope2

import warnings
warnings.warn("The Zope package has been renamed to Zope2. "
              "Import of a package named 'Zope' is deprecated "
              "and will be disabled starting in Zope 2.11.",
              DeprecationWarning, stacklevel=2)
