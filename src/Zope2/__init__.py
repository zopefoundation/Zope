##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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
"""Zope application package."""

import os


_began_startup = 0

# Zope2.App.startup.startup() sets the following variables in this module.
bobo_application = None
DB = None
opened = []


def startup_wsgi():
    """Initialize the Zope Package and provide a published module"""
    global _began_startup
    if _began_startup:
        # Already began (and maybe finished) startup, so don't run again
        return
    _began_startup = 1
    _configure_wsgi()
    from Zope2.App.startup import startup as _startup
    _startup()


def app(*args, **kw):
    """Utility for scripts to open a connection to the database"""
    startup_wsgi()
    return bobo_application(*args, **kw)


def debug(*args, **kw):
    """Utility to try a Zope request using the interactive interpreter"""
    startup_wsgi()
    import ZPublisher
    return ZPublisher.test('Zope2', *args, **kw)


def _configure_wsgi():
    from Zope2.Startup.run import configure_wsgi
    configfile = os.environ.get('ZOPE_CONFIG')
    if configfile is not None:
        configure_wsgi(configfile)
