##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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

    Legacy sources of common configuraiton values are updated to
    reflect the new configuration; this may be removed in some future
    version.
    """
    global _config
    _config = cfg

    if cfg is None:
        return

    from App import FindHomes
    import __builtin__
    __builtin__.CLIENT_HOME = FindHomes.CLIENT_HOME = cfg.clienthome
    __builtin__.INSTANCE_HOME = FindHomes.INSTANCE_HOME = cfg.instancehome
    __builtin__.SOFTWARE_HOME = FindHomes.SOFTWARE_HOME = cfg.softwarehome
    __builtin__.ZOPE_HOME = FindHomes.ZOPE_HOME = cfg.zopehome

    # XXX make sure the environment variables, if set, don't get out
    # of sync.  This is needed to support 3rd-party code written to
    # support Zope versions prior to 2.7.
    import os
    os.environ["CLIENT_HOME"] = cfg.clienthome
    os.environ["INSTANCE_HOME"] = cfg.instancehome
    os.environ["SOFTWARE_HOME"] = cfg.softwarehome
    os.environ["ZOPE_HOME"] = cfg.zopehome

    if "Globals" in sys.modules:
        # XXX We *really* want to avoid this if Globals hasn't already
        # been imported, due to circular imports.  ;-(
        import Globals
        Globals.data_dir = cfg.clienthome
        # Globals does not export CLIENT_HOME
        Globals.INSTANCE_HOME = cfg.instancehome
        Globals.SOFTWARE_HOME = cfg.softwarehome
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
        self.softwarehome = FindHomes.SOFTWARE_HOME
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
