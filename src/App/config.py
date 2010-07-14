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

"""Simple access to configuration values.

The configuration values are represented as a single object with
attributes for each bit of information.
"""

import sys

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
    import __builtin__
    import os
    import Globals  # to set data

    __builtin__.CLIENT_HOME = FindHomes.CLIENT_HOME = cfg.clienthome
    os.environ["CLIENT_HOME"] = cfg.clienthome
    # Globals does not export CLIENT_HOME
    Globals.data_dir = cfg.clienthome

    __builtin__.INSTANCE_HOME = FindHomes.INSTANCE_HOME = cfg.instancehome
    os.environ["INSTANCE_HOME"] = cfg.instancehome
    Globals.INSTANCE_HOME = cfg.instancehome

    if hasattr(cfg, 'softwarehome') and cfg.softwarehome is not None:
        __builtin__.SOFTWARE_HOME = FindHomes.SOFTWARE_HOME = cfg.softwarehome
        os.environ["SOFTWARE_HOME"] = cfg.softwarehome
        Globals.SOFTWARE_HOME = cfg.softwarehome

    if hasattr(cfg, 'zopehome') and cfg.zopehome is not None:
        __builtin__.ZOPE_HOME = FindHomes.ZOPE_HOME = cfg.zopehome
        os.environ["ZOPE_HOME"] = cfg.zopehome
        Globals.ZOPE_HOME = cfg.zopehome

    Globals.DevelopmentMode = cfg.debug_mode

class DefaultConfiguration:
    """
    This configuration should be used effectively only during unit tests
    """
    def __init__(self):
        from App import FindHomes
        self.clienthome = FindHomes.CLIENT_HOME
        self.instancehome = FindHomes.INSTANCE_HOME
        if hasattr(FindHomes, 'SOFTWARE_HOME'):
            self.softwarehome = FindHomes.SOFTWARE_HOME
        if hasattr(FindHomes, 'ZOPE_HOME'):
            self.zopehome = FindHomes.ZOPE_HOME
        self.dbtab = None
        self.debug_mode = True
        self.enable_product_installation = True
        self.locale = None

        # restructured text
        default_enc = sys.getdefaultencoding()
        self.rest_input_encoding = default_enc
        self.rest_output_encoding = default_enc
        self.rest_header_level = 3
        self.rest_language_code = 'en'

        # ZServer.HTTPServer
        self.http_header_max_length = 8196

        # VerboseSecurity
        self.skip_ownership_checking = False
        self.skip_authentication_checking = False
