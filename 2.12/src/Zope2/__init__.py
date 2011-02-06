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

# Before this version of Zope, "import Zope" always opened the
# database automatically.  Unfortunately, that strategy caused the
# Python import lock to be held by the main thread during database
# initialization, which lead to a deadlock if other threads required
# something to be imported before completing initialization.  This can
# be a big problem for ZEO.

# Now the database is opened when you call startup(), app(), or
# debug().

# This version is transitional.  If you have a script that no longer
# works because it needs the database to be opened on calling "import
# Zope", you can set the environment variable ZOPE_COMPATIBLE_STARTUP
# to a non-empty value.  Then "import Zope2" will automatically open
# the database as it used to.  Or better, update the script to call
# Zope2.startup() right after importing the Zope package.  A future
# version of Zope will remove this backward compatibility, since the
# old behavior is likely to cause problems as ZODB backends, like ZEO,
# gain new features.

_began_startup = 0

def startup():
    """Initialize the Zope Package and provide a published module"""
    global _began_startup
    if _began_startup:
        # Already began (and maybe finished) startup, so don't run again
        return
    _began_startup = 1
    _configure()
    from Zope2.App.startup import startup as _startup
    _startup()

def app(*args, **kw):
    """Utility for scripts to open a connection to the database"""
    startup()
    return bobo_application(*args, **kw)

def debug(*args, **kw):
    """Utility to try a Zope request using the interactive interpreter"""
    startup()
    import ZPublisher
    return ZPublisher.test('Zope2', *args, **kw)

from Zope2.Startup.run import configure

def _configure():
    # Load configuration file from (optional) environment variable
    # Also see http://zope.org/Collectors/Zope/1233
    import os
    configfile = os.environ.get('ZOPE_CONFIG')
    if configfile is not None:
        configure(configfile)

# Zope2.App.startup.startup() sets the following variables in this module.
DB = None
bobo_application = None
zpublisher_transactions_manager = None
zpublisher_validated_hook = None
zpublisher_exception_hook = None
__bobo_before__ = None


import os
if os.environ.get('ZOPE_COMPATIBLE_STARTUP'):
    # Open the database immediately (see comment above).
    startup()

