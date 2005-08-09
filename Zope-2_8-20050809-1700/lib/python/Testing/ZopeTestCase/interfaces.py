##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZopeTestCase interfaces

$Id$
"""

from Interface import Interface


class IZopeTestCase(Interface):

    def afterSetUp():
        '''Called after setUp() has completed. This is
           far and away the most useful hook.
        '''

    def beforeTearDown():
        '''Called before tearDown() is executed.
           Note that tearDown() is not called if
           setUp() fails.
        '''

    def afterClear():
        '''Called after the fixture has been cleared.
           Note that this may occur during setUp() *and*
           tearDown().
        '''

    def beforeSetUp():
        '''Called before the ZODB connection is opened,
           at the start of setUp(). By default begins a
           new transaction.
        '''

    def beforeClose():
        '''Called before the ZODB connection is closed,
           at the end of tearDown(). By default aborts
           the transaction.
        '''


class IZopeSecurity(Interface):

    def setRoles(roles, name=None):
        '''Changes the roles assigned to a user.
           If the 'name' argument is omitted, changes the
           roles of the default user.
        '''

    def setPermissions(permissions, role=None):
        '''Changes the permissions assigned to a role.
           If the 'role' argument is omitted, changes the
           permissions assigned to the default role.
        '''

    def login(name=None):
        '''Logs in as the specified user.
           If the 'name' argument is omitted, logs in
           as the default user.
        '''

    def logout():
        '''Logs out.'''


class IPortalTestCase(IZopeTestCase):

    def getPortal():
        '''Returns the portal object to the setup code.
           Will typically be overridden by subclasses
           to return the object serving as the "portal".

           Note: This method should not be called by tests!
        '''

    def createMemberarea(name):
        '''Creates a memberarea for the specified user.
           Subclasses may override to provide a customized
           or more lightweight version of the memberarea.
        '''


class IPortalSecurity(IZopeSecurity):
    '''This is currently the same as IZopeSecurity'''


class IProfiled(Interface):

    def runcall(func, *args, **kw):
        '''Allows to run a function under profiler control
           adding to the accumulated profiler statistics.
        '''


class IFunctional(Interface):

    def publish(path, basic=None, env=None, extra=None, request_method='GET', stdin=None):
        '''Publishes the object at 'path' returning an
           extended response object. The path may contain 
           a query string.
        '''


