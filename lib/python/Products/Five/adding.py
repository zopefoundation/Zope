##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
""" Z2 -> Z3 bridge utilities.

$Id: adding.py 15515 2005-08-02 17:42:08Z yuppie $
"""

# BBB: This file will be removed in future versions of Five.
from browser.adding import ContentAdding

import warnings
warnings.warn("\nThe Products.Five.adding module has been renamed to "
              "Products.Five.browser.adding \n"
              "and will be disabled starting in Five 1.2.\n",
              DeprecationWarning, stacklevel=2)
