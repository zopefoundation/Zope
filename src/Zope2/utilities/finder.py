##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os


class ZopeFinder:

    def __init__(self, argv):
        self.cmd = argv[0]

    def filter_warnings(self):
        import warnings
        warnings.simplefilter('ignore', Warning, append=True)

    def get_app(self, config_file=None):
        # given a config file, return a Zope application object
        if config_file is None:
            config_file = self.get_zope_conf()
        from Zope2.Startup import options, handlers
        import App.config
        import Zope2
        opts = options.ZopeOptions()
        opts.configfile = config_file
        opts.realize(args=[], doc="", raise_getopt_errs=0)
        handlers.handleConfig(opts.configroot, opts.confighandlers)
        App.config.setConfiguration(opts.configroot)
        app = Zope2.app()
        return app

    def get_zope_conf(self):
        # the default config file path is assumed to live in
        # $instance_home/etc/zope.conf, and the console scripts that use this
        # are assumed to live in $instance_home/bin; override if the
        # environ contains "ZOPE_CONF".
        ihome = os.path.dirname(os.path.abspath(os.path.dirname(self.cmd)))
        default_config_file = os.path.join(ihome, 'etc', 'zope.conf')
        zope_conf = os.environ.get('ZOPE_CONF', default_config_file)
        return zope_conf
