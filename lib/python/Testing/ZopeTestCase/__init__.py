#
# Names exported by the ZopeTestCase package
#

# $Id: __init__.py,v 1.25 2005/02/22 14:59:16 shh42 Exp $

import ZopeLite as Zope2
import utils

from ZopeLite import hasProduct
from ZopeLite import installProduct
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

from base import TestCase
from base import app
from base import close

from profiler import Profiled
from sandbox import Sandboxed
from functional import Functional

from warnhook import WarningsHook
from unittest import main

# TODO
#from doctest import ZopeDocFileSuite
#from doctest import FunctionalDocFileSuite

# b/w compatibility names
_folder_name = folder_name
_user_name = user_name
_user_role = user_role
_standard_permissions = standard_permissions
_portal_name = portal_name
from base import closeConnections

