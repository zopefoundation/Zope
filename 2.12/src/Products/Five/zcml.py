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
"""ZCML machinery

$Id$
"""
import os
import os.path
from zope.configuration import xmlconfig

_initialized = False
_context = None


def load_site():
    """Load a Five/Zope site by finding and loading the appropriate site
    configuration file."""
    global _initialized
    if _initialized:
        return
    _initialized = True

    import Globals
    Globals.INSTANCE_HOME

    # load instance site configuration file
    site_zcml = os.path.join(Globals.INSTANCE_HOME, "etc", "site.zcml")

    import Zope2.utilities
    zope_utilities = os.path.dirname(Zope2.utilities.__file__)
    skel_site_zcml = os.path.join(zope_utilities, "skel", "etc", "site.zcml")
    
    if os.path.exists(site_zcml):
        file = site_zcml
    else:
        # check for zope installation home skel during running unit tests
        file = skel_site_zcml

    global _context
    _context = xmlconfig.file(file)


def load_config(file, package=None, execute=True):
    """Load an additional ZCML file into the context.

    Use with extreme care.
    """
    global _context
    _context = xmlconfig.file(file, package, _context, execute=execute)

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

from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)
del addCleanUp
