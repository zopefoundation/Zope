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


def configure_wsgi(configfile):
    """ Provide an API which allows scripts to configure Zope
    before attempting to do 'app = Zope2.app(). Should be used as
    follows: from Zope2.Startup.run import configure_wsgi;
    configure_wsgi('/path/to/configfile');
    import Zope2; app = Zope2.app()
    """
    import Zope2.Startup
    starter = Zope2.Startup.get_wsgi_starter()
    opts = _set_wsgi_config(configfile)
    starter.setConfiguration(opts.configroot)
    starter.setupSecurityOptions()
    return starter


def _set_wsgi_config(configfile=None):
    """ Configure a Zope instance based on ZopeWSGIOptions.
    Optionally accept a configfile argument (string path) in order
    to specify where the configuration file exists. """
    from Zope2.Startup import handlers
    from Zope2.Startup import options
    opts = options.ZopeWSGIOptions(configfile=configfile)()
    handlers.handleWSGIConfig(opts.configroot, opts.confighandlers)
    import App.config
    App.config.setConfiguration(opts.configroot)
    return opts


def make_wsgi_app(global_config, zope_conf):
    from App.config import setConfiguration
    from Zope2.Startup import get_wsgi_starter
    from Zope2.Startup.handlers import handleWSGIConfig
    from Zope2.Startup.options import ZopeWSGIOptions
    from ZPublisher.WSGIPublisher import publish_module
    starter = get_wsgi_starter()
    opts = ZopeWSGIOptions(configfile=zope_conf)()
    if 'debug_mode' in global_config:
        if global_config['debug_mode'] in ('true', 'on', '1'):
            opts.configroot.debug_mode = True
    if 'debug_exceptions' in global_config:
        if global_config['debug_exceptions'] in ('true', 'on', '1'):
            opts.configroot.debug_exceptions = True
    handleWSGIConfig(opts.configroot, opts.confighandlers)
    setConfiguration(opts.configroot)
    starter.setConfiguration(opts.configroot)
    starter.prepare()
    return publish_module
