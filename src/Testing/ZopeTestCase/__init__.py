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

# flake8: NOQA: E401

# This is a file to define public API in the base namespace of the package.
# use: isort:skip to supress all isort related warnings / errors,
# as this file should be logically grouped imports

from Testing.ZopeTestCase import ZopeLite as Zope2


from Testing.ZopeTestCase import utils  # isort:skip
from Testing.ZopeTestCase import layer  # isort:skip

from Testing.ZopeTestCase.ZopeLite import hasProduct  # isort:skip
from Testing.ZopeTestCase.ZopeLite import installProduct  # isort:skip
from Testing.ZopeTestCase.ZopeLite import hasPackage  # isort:skip
from Testing.ZopeTestCase.ZopeLite import installPackage  # isort:skip
from Testing.ZopeTestCase.ZopeLite import _print  # isort:skip

from Testing.ZopeTestCase.ZopeTestCase import folder_name  # isort:skip
from Testing.ZopeTestCase.ZopeTestCase import user_name  # isort:skip
from Testing.ZopeTestCase.ZopeTestCase import user_password  # isort:skip
from Testing.ZopeTestCase.ZopeTestCase import user_role  # isort:skip
from Testing.ZopeTestCase.ZopeTestCase import standard_permissions  # isort:skip
from Testing.ZopeTestCase.ZopeTestCase import ZopeTestCase  # isort:skip
from Testing.ZopeTestCase.ZopeTestCase import FunctionalTestCase  # isort:skip

from Testing.ZopeTestCase.PortalTestCase import portal_name  # isort:skip
from Testing.ZopeTestCase.PortalTestCase import PortalTestCase  # isort:skip

from Testing.ZopeTestCase.sandbox import Sandboxed  # isort:skip
from Testing.ZopeTestCase.functional import Functional  # isort:skip

from Testing.ZopeTestCase.base import TestCase  # isort:skip
from Testing.ZopeTestCase.base import app  # isort:skip
from Testing.ZopeTestCase.base import close  # isort:skip

from .warnhook import WarningsHook  # isort:skip
from unittest import main  # isort:skip

from Testing.ZopeTestCase.zopedoctest import ZopeDocTestSuite  # isort:skip
from Testing.ZopeTestCase.zopedoctest import ZopeDocFileSuite  # isort:skip
from Testing.ZopeTestCase.zopedoctest import FunctionalDocTestSuite  # isort:skip
from Testing.ZopeTestCase.zopedoctest import FunctionalDocFileSuite  # isort:skip

from Testing.ZopeTestCase import zopedoctest as doctest  # isort:skip
import transaction  # isort:skip
from Testing.ZopeTestCase import placeless  # isort:skip

Zope = Zope2
