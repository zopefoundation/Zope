##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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

import os.path

from App.config import getConfiguration
from zope.configuration import xmlconfig
from zope.testing.cleanup import addCleanUp  # NOQA


_initialized = False
_context = None


def load_site(force=False):
    """Load a Zope site by finding and loading the appropriate site
    configuration file."""
    global _initialized
    if _initialized and not force:
        return
    _initialized = True

    # load instance site configuration file
    instancehome = getConfiguration().instancehome
    site_zcml = os.path.join(instancehome, "etc", "site.zcml")

    if not os.path.exists(site_zcml):
        # check for zope installation home skel during running unit tests
        import Zope2.utilities
        zope_utils = os.path.dirname(Zope2.utilities.__file__)
        site_zcml = os.path.join(zope_utils, "skel", "etc", "site.zcml")

    global _context
    _context = xmlconfig.file(site_zcml)


def load_config(config, package=None, execute=True):
    """Load an additional ZCML file into the context.

    Use with extreme care.
    """
    global _context
    _context = xmlconfig.file(config, package, _context, execute=execute)


def load_string(s):
    """Load a snipped of ZCML into the context.

    Use with extreme care.
    """
    global _context
    _context = xmlconfig.string(s, _context)


# clean up code

def cleanUp():
    global _context
    _context = None


addCleanUp(cleanUp)
del addCleanUp
