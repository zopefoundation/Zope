##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Initialize the Zope2 Package and provide a published module
"""

import os
import sys
import types
from time import asctime

import AccessControl.users
import App.ZApplication
import OFS.Application
import ZODB
import Zope2
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from App.config import getConfiguration
from zope.event import notify
from zope.processlifetime import DatabaseOpened
from zope.processlifetime import DatabaseOpenedWithRoot


app = None
startup_time = asctime()


def load_zcml():
    # This hook is overriden by ZopeTestCase
    from .zcml import load_site
    load_site()

    # Set up Zope2 specific vocabulary registry
    from .schema import configure_vocabulary_registry
    configure_vocabulary_registry()


def _load_custom_zodb(location):
    """Return a module, or None."""
    target = os.path.join(location, 'custom_zodb.py')
    if os.path.exists(target):
        with open(target) as f:
            try:
                code_obj = compile(f.read(), target, mode='exec')
            except SyntaxError:
                return None
        module = types.ModuleType('Zope2.custom_zodb', 'Custom database')
        exec(code_obj, module.__dict__)
        sys.modules['Zope2.custom_zodb'] = module
        return module


def startup():
    from Zope2.App import patches
    patches.apply_patches()

    global app

    # Import products
    OFS.Application.import_products()

    configuration = getConfiguration()

    # Open the database
    dbtab = configuration.dbtab
    DB = None

    custom_locations = [
        getattr(configuration, 'testinghome', None),
        configuration.instancehome,
    ]
    for location in custom_locations:
        if not location:
            continue
        module = _load_custom_zodb(location)
        if module is not None:
            # Get the database and join it to the dbtab multidatabase
            # FIXME: this uses internal datastructures of dbtab
            databases = getattr(dbtab, 'databases', {})
            if hasattr(module, 'DB'):
                DB = module.DB
                databases.update(getattr(DB, 'databases', {}))
                DB.databases = databases
            else:
                DB = ZODB.DB(module.Storage, databases=databases)

            break
    else:
        # if there is no custom_zodb, use the config file specified databases
        DB = dbtab.getDatabase('/', is_root=1)

    # Force a connection to every configured database, to ensure all of them
    # can indeed be opened. This avoids surprises during runtime when traversal
    # to some database mountpoint fails as the underlying storage cannot be
    # opened at all
    if dbtab is not None:
        for mount, name in dbtab.listMountPaths():
            _db = dbtab.getDatabase(mount)
            _conn = _db.open()
            _conn.close()
            del _conn
            del _db

    notify(DatabaseOpened(DB))

    Zope2.DB = DB
    Zope2.opened.append(DB)

    from . import ClassFactory
    DB.classFactory = ClassFactory.ClassFactory

    # "Log on" as system user
    newSecurityManager(None, AccessControl.users.system)

    # Set up the CA
    load_zcml()

    # Set up the "app" object that automagically opens
    # connections
    app = App.ZApplication.ZApplicationWrapper(
        DB, 'Application', OFS.Application.Application)
    Zope2.bobo_application = app

    # Initialize the app object
    application = app()
    OFS.Application.initialize(application)
    application._p_jar.close()

    # "Log off" as system user
    noSecurityManager()

    global startup_time
    startup_time = asctime()

    notify(DatabaseOpenedWithRoot(DB))
