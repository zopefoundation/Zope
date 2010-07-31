##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Names exported by the ZopeTestCase package
"""

import ZopeLite as Zope2
import utils
import layer

from ZopeLite import hasProduct
from ZopeLite import installProduct
from ZopeLite import hasPackage
from ZopeLite import installPackage
from ZopeLite import _print

from ZopeTestCase import folder_name
from ZopeTestCase import user_name
from ZopeTestCase import user_password
from ZopeTestCase import user_role
from ZopeTestCase import standard_permissions
from ZopeTestCase import ZopeTestCase
from ZopeTestCase import FunctionalTestCase

from PortalTestCase import portal_name
from PortalTestCase import PortalTestCase

from sandbox import Sandboxed
from functional import Functional

from base import TestCase
from base import app
from base import close

from warnhook import WarningsHook
from unittest import main

from zopedoctest import ZopeDocTestSuite
from zopedoctest import ZopeDocFileSuite
from zopedoctest import FunctionalDocTestSuite
from zopedoctest import FunctionalDocFileSuite

import zopedoctest as doctest
import transaction
import placeless

Zope = Zope2

