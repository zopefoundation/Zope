##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Provide a Main application for the Zope framework

The Job of this module is to:

 - Configure and open the database

 - Establish the top-level object for ZPublisher

 - Perform very high-level configuration tasks

"""

# We import BoboPOS before importing any other application
# modules.  This is needed to assure that the right
# versions of Persistent etc get registered.
from BoboPOS import SimpleDB, TJar, SingleThreadedTransaction

import sys, os,  Globals, OFS.Application
Globals.BobobaseName = os.path.join(Globals.data_dir, 'Data.bbb')
Globals.DatabaseVersion='2'

# Setup support for broken objects:
import OFS.Uninstalled, BoboPOS.PickleJar
BoboPOS.PickleJar.PickleJar.Broken=OFS.Uninstalled.Broken

# Open the application database
OFS.Application.import_products()
revision=read_only=None
if os.environ.has_key('ZOPE_READ_ONLY'):
    read_only=1
    try:
        from DateTime import DateTime
        revision=DateTime(os.environ['ZOPE_READ_ONLY']).timeTime()
    except: pass

Bobobase=Globals.Bobobase=BoboPOS.PickleDictionary(
    Globals.BobobaseName, read_only=read_only, revision=revision)
Globals.opened.append(Bobobase)
VersionBase=Globals.VersionBase=TJar.TM(Bobobase)
Globals.opened.append(VersionBase)

try: app=Bobobase['Application']
except KeyError:
    app=OFS.Application.Application()
    Bobobase['Application']=app
    get_transaction().note('created Application object')
    get_transaction().commit()

bobo_application=app

OFS.Application.initialize(app)

if os.environ.has_key('ZOPE_DATABASE_QUOTA'):
    quota=int(os.environ['ZOPE_DATABASE_QUOTA'])
    Bobobase._jar.db.set_quota(
        lambda x, quota=quota, otherdb=VersionBase.TDB:
        x + otherdb.pos > quota)
    VersionBase.TDB.set_quota(
        lambda x, quota=quota, otherdb=Bobobase._jar.db:
        x + otherdb.pos > quota)

SingleThreadedTransaction.Transaction.commit=VersionBase.committer()

__bobo_debug_mode__=Globals.DevelopmentMode
