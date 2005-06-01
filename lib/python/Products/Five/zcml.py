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

$Id: zcml.py 12915 2005-05-31 10:23:19Z philikon $
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

def load_string(s):
    """Load a snipped of ZCML into the context.

    Use with extreme care.
    """
    global _context
    _context = xmlconfig.string(s, _context)

