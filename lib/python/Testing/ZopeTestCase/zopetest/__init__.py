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
"""ZopeTestCase public interface

$Id: __init__.py,v 1.1 2005/02/25 11:01:07 shh42 Exp $
"""

__version__ = '0.9.7'

import Testing.ZopeTestCase
__path__.extend(Testing.ZopeTestCase.__path__)

from Testing.ZopeTestCase import *
from Testing.ZopeTestCase import _print
from Testing.ZopeTestCase.utils import *

