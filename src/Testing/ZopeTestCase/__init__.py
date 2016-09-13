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

from . import ZopeLite as Zope2
from . import utils  # NOQA
from . import layer  # NOQA

from .ZopeLite import hasProduct  # NOQA
from .ZopeLite import installProduct  # NOQA
from .ZopeLite import hasPackage  # NOQA
from .ZopeLite import installPackage  # NOQA
from .ZopeLite import _print  # NOQA

from .ZopeTestCase import folder_name  # NOQA
from .ZopeTestCase import user_name  # NOQA
from .ZopeTestCase import user_password  # NOQA
from .ZopeTestCase import user_role  # NOQA
from .ZopeTestCase import standard_permissions  # NOQA
from .ZopeTestCase import ZopeTestCase  # NOQA
from .ZopeTestCase import FunctionalTestCase  # NOQA

from .PortalTestCase import portal_name  # NOQA
from .PortalTestCase import PortalTestCase  # NOQA

from .sandbox import Sandboxed  # NOQA
from .functional import Functional  # NOQA

from .base import TestCase  # NOQA
from .base import app  # NOQA
from .base import close  # NOQA

from .warnhook import WarningsHook  # NOQA
from unittest import main  # NOQA

from .zopedoctest import ZopeDocTestSuite  # NOQA
from .zopedoctest import ZopeDocFileSuite  # NOQA
from .zopedoctest import FunctionalDocTestSuite  # NOQA
from .zopedoctest import FunctionalDocFileSuite  # NOQA

from . import zopedoctest as doctest  # NOQA
import transaction  # NOQA
from . import placeless  # NOQA

Zope = Zope2
