from Interface import Interface

# $Id: IZopeTestCase.py,v 1.14 2004/09/04 18:01:11 shh42 Exp $


#
#   ZopeTestCase.__implements__ = (
#           IZopeTestCase, ISimpleSecurity, IExtensibleSecurity)
#
#   PortalTestCase.__implements__ = (
#           IPortalTestCase, ISimpleSecurity, IExtensibleSecurity)
#


class ISimpleSecurity(Interface):

    def setRoles(roles):
        '''Changes the user's roles.'''

    def getRoles():
        '''Returns the user's roles.'''

    def setPermissions(permissions):
        '''Changes the user's permissions.'''

    def getPermissions():
        '''Returns the user's permissions.'''

    def login():
        '''Logs in.'''

    def logout():
        '''Logs out.'''


class IExtensibleSecurity(Interface):

    def setRoles(roles, name):
        '''Changes the roles assigned to a user.'''

    def getRoles(name):
        '''Returns the specified user's roles.'''

    def setPermissions(permissions, role):
        '''Changes the permissions assigned to a role.'''

    def getPermissions(role):
        '''Returns the permissions assigned to a role.'''

    def login(name):
        '''Logs in as the specified user.'''

    def logout():
        '''Logs out.'''


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


class IPortalTestCase(IZopeTestCase):

    def getPortal():
        '''Returns the portal object to the setup code.
           Will typically be overridden by subclasses
           to return the object serving as the "portal".

           Note: This method should not be called by tests!
        '''

    def createMemberarea(member_id):
        '''Creates a memberarea for the specified member.
           Subclasses may override to provide a customized 
           or more lightweight version of the memberarea.
        '''


class IProfiled(Interface):

    def runcall(func, *args, **kw):
        '''Allows to run a function under profiler control
           adding to the accumulated profiler statistics.
        '''


class IFunctional(Interface):

    def publish(path, basic=None, env=None, extra=None, request_method='GET'):
        '''Publishes the object at 'path' returning an
           extended response object. The path may contain 
           a query string.
        '''


