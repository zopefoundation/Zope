##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

def run():
    """ Start a Zope instance """
    from Zope.Startup import start_zope
    opts = _setconfig()
    start_zope(opts.configroot)

def configure(configfile):
    """ Provide an API which allows scripts like zopectl to configure
    Zope before attempting to do 'app = Zope.app(). Should be used as
    follows:  from Zope.Startup.run import configure;
    configure('/path/to/configfile'); import Zope; app = Zope.app() """
    from Zope.Startup import ZopeStarter
    opts = _setconfig(configfile)
    starter = ZopeStarter(opts.configroot)
    starter.setupSecurityOptions()
    starter.dropPrivileges()

def _setconfig(configfile=None):
    """ Configure a Zope instance based on ZopeOptions.  Optionally
    accept a configfile argument (string path) in order to specify
    where the configuration file exists. """
    from Zope.Startup import options, handlers
    from App import config
    opts = options.ZopeOptions()
    if configfile:
        opts.configfile=configfile
        opts.realize(doc="Sorry, no option docs yet.", raise_getopt_errs=0)
    else:
        opts.realize(doc="Sorry, no option docs yet.")
        
    handlers.handleConfig(opts.configroot, opts.confighandlers)
    import App.config
    App.config.setConfiguration(opts.configroot)
    return opts

if __name__ == '__main__':
    run()

