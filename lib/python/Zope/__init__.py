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
"""Initialize the Zope Package and provide a published module
"""

#######################################################################
# We need to get the right BTree extensions loaded
import sys, os, App.FindHomes
sys.path.insert(0, os.path.join(SOFTWARE_HOME, 'ZopeZODB3'))
#######################################################################
import ZODB, ZODB.ZApplication, imp
import Globals, OFS.Application, sys
import AccessControl.SecurityManagement, AccessControl.User

Globals.BobobaseName = os.path.join(Globals.data_dir, 'Data.fs')
Globals.DatabaseVersion='3'

# Import products
OFS.Application.import_products()

# Open the database
try:
    # Try to use custom storage
    m=imp.find_module('custom_zodb',[INSTANCE_HOME])
except:
    import ZODB.FileStorage
    DB=ZODB.FileStorage.FileStorage(Globals.BobobaseName)
    DB=ZODB.DB(DB)
else:
    m=imp.load_module('Zope.custom_zodb', m[0], m[1], m[2])
    if hasattr(m,'DB'):
        DB=m.DB
    else:
        DB=m.Storage
        DB=ZODB.DB(DB)

    Globals.BobobaseName = DB.getName()
    sys.modules['Zope.custom_zodb']=m

if DB.getActivityMonitor() is None:
    from ZODB.ActivityMonitor import ActivityMonitor
    DB.setActivityMonitor(ActivityMonitor())

Globals.DB=DB # Ick, this is temporary until we come up with some registry

# Hook for providing multiple transaction object manager undo support:
Globals.UndoManager=DB

Globals.opened.append(DB)
import ClassFactory
DB.setClassFactory(ClassFactory.ClassFactory)

# "Log on" as system user
AccessControl.SecurityManagement.newSecurityManager(
    None, AccessControl.User.system)

# Set up the "application" object that automagically opens
# connections
app=bobo_application=ZODB.ZApplication.ZApplicationWrapper(
    DB, 'Application', OFS.Application.Application, (),
    Globals.VersionNameName)

# Initialize products:
c=app()
OFS.Application.initialize(c)

if Globals.DevelopmentMode:
    # Set up auto-refresh.
    from App.RefreshFuncs import setupAutoRefresh
    setupAutoRefresh(c._p_jar)

c._p_jar.close()
del c

# "Log off" as system user
AccessControl.SecurityManagement.noSecurityManager()

# This is sneaky, but we don't want to play with Main:
sys.modules['Main']=sys.modules['Zope']

import ZODB.POSException, ZPublisher,  ZPublisher
import ExtensionClass
from zLOG import LOG, WARNING, INFO, BLATHER, log_time
from Acquisition import aq_acquire
conflict_errors = 0
startup_time = log_time()
def debug(*args, **kw):
    return apply(ZPublisher.test,('Zope',)+args, kw)

class RequestContainer(ExtensionClass.Base):
    def __init__(self,r): self.REQUEST=r

def zpublisher_exception_hook(
    published, REQUEST, t, v, traceback,
    # static
    StringType=type(''),
    ConflictError=ZODB.POSException.ConflictError,
    ListType=type([]),
    ):
    try:
        if isinstance(t, StringType):
            if t.lower() in ('unauthorized', 'redirect'):
                raise
        else:
            if t is SystemExit:
                raise
            if issubclass(t, ConflictError):
                # First, we need to close the current connection. We'll
                # do this by releasing the hold on it. There should be
                # some sane protocol for this, but for now we'll use
                # brute force:
                global conflict_errors
                conflict_errors = conflict_errors + 1
                method_name = REQUEST.get('PATH_INFO', '')
                err = ('ZODB conflict error at %s '
                       '(%s conflicts since startup at %s)')
                LOG(err % (method_name, conflict_errors, startup_time),
                    INFO, '')
                LOG('Conflict traceback', BLATHER, '', error=sys.exc_info())
                raise ZPublisher.Retry(t, v, traceback)
            if t is ZPublisher.Retry: v.reraise()
            
        try:
            log = aq_acquire(published, '__error_log__', containment=1)
        except AttributeError:
            error_log_url = ''
        else:
            error_log_url = log.raising((t, v, traceback))

        if (getattr(REQUEST.get('RESPONSE', None), '_error_format', '')
            !='text/html'): raise

        if (published is None or published is app or
            type(published) is ListType):
            # At least get the top-level object
            published=app.__bobo_traverse__(REQUEST).__of__(
                RequestContainer(REQUEST))

        get_transaction().begin() # Just to be sure.

        published=getattr(published, 'im_self', published)
        while 1:
            f=getattr(published, 'raise_standardErrorMessage', None)
            if f is None:
                published=getattr(published, 'aq_parent', None)
                if published is None: raise
            else:
                break

        client=published
        while 1:
            if getattr(client, 'standard_error_message', None) is not None:
                break
            client=getattr(client, 'aq_parent', None)
            if client is None: raise

        if REQUEST.get('AUTHENTICATED_USER', None) is None:
            REQUEST['AUTHENTICATED_USER']=AccessControl.User.nobody

        try:
            f(client, REQUEST, t, v, traceback, error_log_url=error_log_url)
        except TypeError:
            # Pre 2.6 call signature
            f(client, REQUEST, t, v, traceback)

    finally: traceback=None


class TransactionsManager:
    def begin(self,
              # Optimize global var lookups:
              get_transaction=get_transaction):
        get_transaction().begin()

    def commit(self,
              # Optimize global var lookups:
               get_transaction=get_transaction):
        get_transaction().commit()

    def abort(self,
              # Optimize global var lookups:
              get_transaction=get_transaction):
        get_transaction().abort()

    def recordMetaData(self, object, request,
                       # Optimize global var lookups:
                       hasattr=hasattr, getattr=getattr,
                       get_transaction=get_transaction,
                       LOG=LOG, WARNING=WARNING,
                       ):
        request_get = request.get
        if hasattr(object, 'getPhysicalPath'):
            path = '/'.join(object.getPhysicalPath())
        else:
            # Try hard to get the physical path of the object,
            # but there are many circumstances where that's not possible.
            to_append = ()

            if hasattr(object, 'im_self') and hasattr(object, '__name__'):
                # object is a Python method.
                to_append = (object.__name__,)
                object = object.im_self

            while object is not None and \
                  not hasattr(object, 'getPhysicalPath'):
                if not hasattr(object, '__name__'):
                    object = None
                    break
                to_append = (object.__name__,) + to_append
                object = getattr(object, 'aq_inner', object)
                object = getattr(object, 'aq_parent', None)

            if object is not None:
                path = '/'.join(object.getPhysicalPath() + to_append)
            else:
                # As Jim would say, "Waaaaaaaa!"
                # This may cause problems with virtual hosts
                # since the physical path is different from the path
                # used to retrieve the object.
                path = request_get('PATH_INFO')

        T=get_transaction()
        T.note(path)
        auth_user=request_get('AUTHENTICATED_USER',None)
        if auth_user is not None:
            try:
                auth_folder = auth_user.aq_parent
            except AttributeError:
                # Most likely some product forgot to call __of__()
                # on the user object.
                LOG('AccessControl', WARNING,
                    'A user object of type %s has no aq_parent.'
                    % str(type(auth_user)))
                auth_path = request_get('AUTHENTICATION_PATH')
            else:
                auth_path = '/'.join(auth_folder.getPhysicalPath()[1:-1])

            T.setUser(auth_user.getId(), auth_path)


zpublisher_transactions_manager = TransactionsManager()

zpublisher_validated_hook=AccessControl.SecurityManagement.newSecurityManager
__bobo_before__=AccessControl.SecurityManagement.noSecurityManager
