##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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

import os


_config = None


def getConfiguration():
    """Return the global Zope configuration object.

    If a configuration hasn't been set yet, generates a simple
    configuration object and uses that.  Once generated, it may not be
    overridden by calling ``setConfiguration()``.
    """
    if _config is None:
        setConfiguration(DefaultConfiguration())
    return _config


def setConfiguration(cfg):
    """Set the global configuration object.

    Legacy sources of common configuration values are updated to
    reflect the new configuration; this may be removed in some future
    version.
    """
    global _config
    _config = cfg

    if cfg is None:
        return

    from App import FindHomes
    FindHomes.CLIENT_HOME = cfg.clienthome
    os.environ["CLIENT_HOME"] = cfg.clienthome

    FindHomes.INSTANCE_HOME = cfg.instancehome
    os.environ["INSTANCE_HOME"] = cfg.instancehome


class DefaultConfiguration:
    """
    This configuration should be used effectively only during unit tests
    """
    def __init__(self):
        from App import FindHomes
        self.clienthome = FindHomes.CLIENT_HOME
        self.instancehome = FindHomes.INSTANCE_HOME
        self.dbtab = None
        self.debug_mode = True
        self.locale = None

        # VerboseSecurity
        self.skip_ownership_checking = False
        self.skip_authentication_checking = False
