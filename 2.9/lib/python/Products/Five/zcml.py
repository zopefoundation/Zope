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

$Id: zcml.py 14452 2005-07-09 21:15:33Z philikon $
"""
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
    if os.path.exists(site_zcml):
        file = site_zcml
    else:
        file = os.path.join(os.path.dirname(__file__), "skel", "site.zcml")

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
