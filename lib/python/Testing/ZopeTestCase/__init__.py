#
# Names exported by the ZopeTestCase module
#

# $Id: __init__.py,v 1.11 2004/02/06 18:00:02 shh42 Exp $

import ZopeLite as Zope
import utils

from ZopeLite import installProduct
from ZopeLite import hasProduct
from ZopeLite import _print

from ZopeTestCase import folder_name
from ZopeTestCase import user_name
from ZopeTestCase import user_role
from ZopeTestCase import standard_permissions
from ZopeTestCase import ZopeTestCase

from PortalTestCase import portal_name
from PortalTestCase import PortalTestCase

from profiler import Profiled
from sandbox import Sandboxed
from functional import Functional

from ZopeTestCase import app
from ZopeTestCase import close
from ZopeTestCase import closeConnections

from unittest import main

# Convenience class for functional unit testing
class FunctionalTestCase(Functional, ZopeTestCase):
    pass

# b/w compatibility names
_folder_name = folder_name
_user_name = user_name
_user_role = user_role
_standard_permissions = standard_permissions
_portal_name = portal_name

