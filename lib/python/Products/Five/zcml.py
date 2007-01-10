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
"""ZCML machinery

$Id$
"""
import warnings
import os
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

    # load instance site configuration file
    site_zcml = os.path.join(INSTANCE_HOME, "etc", "site.zcml")
    skel_site_zcml = os.path.join(INSTANCE_HOME, "skel", "etc", "site.zcml")
    skel_site2_zcml = os.path.join(ZOPE_HOME, "skel", "etc", "site.zcml")
    
    if os.path.exists(site_zcml):
        file = site_zcml
    elif os.path.exists(skel_site_zcml):
        # check for zope installation home skel during running unit tests
        file = skel_site_zcml
    else:
        file = skel_site2_zcml
        msg = "site.zcml should now live at '%s', for " \
              "sites upgraded from Zope 2.9 please copy '%s' " \
              "to '%s'" \
              % (site_zcml, skel_site2_zcml, site_zcml)
        warnings.warn(msg, DeprecationWarning)

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
