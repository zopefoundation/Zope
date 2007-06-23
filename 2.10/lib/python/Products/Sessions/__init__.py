##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
Session initialization routines

$Id$
"""

import ZODB # this is for testrunner to be happy
import BrowserIdManager
import SessionDataManager
from BrowserIdManager import BrowserIdManagerErr
from SessionDataManager import SessionDataManagerErr

def initialize(context):
    context.registerClass(
        BrowserIdManager.BrowserIdManager,
        icon="www/idmgr.gif",
        permission=BrowserIdManager.ADD_BROWSER_ID_MANAGER_PERM,
        constructors=(BrowserIdManager.constructBrowserIdManagerForm,
                      BrowserIdManager.constructBrowserIdManager)
        )

    context.registerClass(
        SessionDataManager.SessionDataManager,
        icon='www/datamgr.gif',
        permission=SessionDataManager.ADD_SESSION_DATAMANAGER_PERM,
        constructors=(SessionDataManager.constructSessionDataManagerForm,
                      SessionDataManager.constructSessionDataManager)
        )

    context.registerHelp()
    context.registerHelpTitle("Zope Help")
    # do module security declarations so folks can use some of the
    # module-level stuff in PythonScripts
    #
    # declare on behalf of Transience too, since ModuleSecurityInfo is too
    # stupid for me to declare in two places without overwriting one set
    # with the other. :-(
    from AccessControl import ModuleSecurityInfo
    security = ModuleSecurityInfo('Products')
    security.declarePublic('Sessions')
    security.declarePublic('Transience')
    security = ModuleSecurityInfo('Products.Sessions')
    security.declarePublic('BrowserIdManagerErr')
    security.declarePublic('SessionDataManagerErr')
    security = ModuleSecurityInfo('Products.Transience')
    security.declarePublic('MaxTransientObjectsExceeded')
