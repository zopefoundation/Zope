##############################################################################
#
# Copyright (c) 2004 Five Contributors. All rights reserved.
#
# This software is distributed under the terms of the Zope Public
# License (ZPL) v2.1. See COPYING.txt for more information.
#
##############################################################################
"""ZCML machinery

$Id: zcml.py 9855 2005-03-17 16:41:09Z shh $
"""
import os
from zope.configuration import xmlconfig

_initialized = False
_context = None


def load_site():
    """Load the appropriate ZCML file.

    Note that this can be called multiple times, unlike in Zope 3. This
    is needed because in Zope 2 we don't (yet) have a master ZCML file
    which can include all the others.
    """
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


def load_config(file, package=None):
    """Load an additional ZCML file into the context.

    Use with extreme care.
    """
    global _context
    _context = xmlconfig.file(file, package, _context)

