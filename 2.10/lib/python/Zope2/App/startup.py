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
"""Initialize the Zope2 Package and provide a published module
"""

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_acquire
from App.config import getConfiguration
from time import asctime
from types import StringType, ListType
from zExceptions import Unauthorized
from ZODB.POSException import ConflictError
import transaction
import AccessControl.User
import App.FindHomes
import ExtensionClass
import Globals
import imp
import logging
import OFS.Application
import os
import sys
import ZODB
import App.ZApplication
import Zope2
import ZPublisher


def startup():
    global app

    # Import products
    OFS.Application.import_products()

    configuration = getConfiguration()

    # Open the database
    dbtab = configuration.dbtab
    try:
        # Try to use custom storage
        try:
            m=imp.find_module('custom_zodb',[configuration.testinghome])
        except:
            m=imp.find_module('custom_zodb',[configuration.instancehome])
    except:
        # if there is no custom_zodb, use the config file specified databases
        DB = dbtab.getDatabase('/', is_root=1)
    else:
        m=imp.load_module('Zope2.custom_zodb', m[0], m[1], m[2])
        sys.modules['Zope2.custom_zodb']=m

        # Get the database and join it to the dbtab multidatabase
        # FIXME: this uses internal datastructures of dbtab
        databases = getattr(dbtab, 'databases', {})
        if hasattr(m,'DB'):
            DB=m.DB
            databases.update(getattr(DB, 'databases', {}))
            DB.databases = databases
        else:
            DB = ZODB.DB(m.Storage, databases=databases)

    Globals.BobobaseName = DB.getName()

    if DB.getActivityMonitor() is None:
        from ZODB.ActivityMonitor import ActivityMonitor
        DB.setActivityMonitor(ActivityMonitor())

    Globals.DB = DB # Ick, this is temporary until we come up with some registry
    Zope2.DB = DB

    # Hook for providing multiple transaction object manager undo support:
    Globals.UndoManager=DB

    Globals.opened.append(DB)
    import ClassFactory
    DB.classFactory = ClassFactory.ClassFactory

    # "Log on" as system user
    newSecurityManager(None, AccessControl.User.system)

    # Set up the "app" object that automagically opens
    # connections
    app = App.ZApplication.ZApplicationWrapper(
        DB, 'Application', OFS.Application.Application, (),
        Globals.VersionNameName)
    Zope2.bobo_application = app

    # Initialize the app object
    application = app()
    OFS.Application.initialize(application)
    if Globals.DevelopmentMode:
        # Set up auto-refresh.
        from App.RefreshFuncs import setupAutoRefresh
        setupAutoRefresh(application._p_jar)
    application._p_jar.close()

    # "Log off" as system user
    noSecurityManager()

    global startup_time
    startup_time = asctime()

    Zope2.zpublisher_transactions_manager = TransactionsManager()
    Zope2.zpublisher_exception_hook = zpublisher_exception_hook
    Zope2.zpublisher_validated_hook = validated_hook
    Zope2.__bobo_before__ = noSecurityManager


def validated_hook(request, user):
    newSecurityManager(request, user)
    version = request.get(Globals.VersionNameName, '')
    if version:
        object = user.aq_parent
        if not getSecurityManager().checkPermission(
            'Join/leave Versions', object):
            request['RESPONSE'].setCookie(
                Globals.VersionNameName,'No longer active',
                expires="Mon, 25-Jan-1999 23:59:59 GMT",
                path=(request['BASEPATH1'] or '/'),
                )
            Zope2.DB.removeVersionPool(version)
            raise Unauthorized, "You don't have permission to enter versions."
    


class RequestContainer(ExtensionClass.Base):
    def __init__(self,r): self.REQUEST=r

conflict_errors = 0
unresolved_conflict_errors = 0

conflict_logger = logging.getLogger('ZPublisher.Conflict')

def zpublisher_exception_hook(published, REQUEST, t, v, traceback):
    global unresolved_conflict_errors
    global conflict_errors
    try:
        if isinstance(t, StringType):
            if t.lower() in ('unauthorized', 'redirect'):
                raise
        else:
            if t is SystemExit:
                raise
            if issubclass(t, ConflictError):
                conflict_errors += 1
                level = getConfiguration().conflict_error_log_level
                if level:
                    conflict_logger.log(level,
                        "%s at %s: %s (%d conflicts (%d unresolved) "
                        "since startup at %s)",
                        v.__class__.__name__,
                        REQUEST.get('PATH_INFO', '<unknown>'),
                        v,
                        conflict_errors,
                        unresolved_conflict_errors,
                        startup_time)
                raise ZPublisher.Retry(t, v, traceback)
            if t is ZPublisher.Retry:
                try:
                    v.reraise()
                except:
                    # we catch the re-raised exception so that it gets
                    # stored in the error log and gets rendered with
                    # standard_error_message
                    t, v, traceback = sys.exc_info()
                if issubclass(t, ConflictError):
                    # ouch, a user saw this conflict error :-(
                    unresolved_conflict_errors += 1

        try:
            log = aq_acquire(published, '__error_log__', containment=1)
        except AttributeError:
            error_log_url = ''
        else:
            error_log_url = log.raising((t, v, traceback))

        if (getattr(REQUEST.get('RESPONSE', None), '_error_format', '')
            !='text/html'):
            raise t, v, traceback

        if (published is None or published is app or
            type(published) is ListType):
            # At least get the top-level object
            published=app.__bobo_traverse__(REQUEST).__of__(
                RequestContainer(REQUEST))

        published=getattr(published, 'im_self', published)
        while 1:
            f=getattr(published, 'raise_standardErrorMessage', None)
            if f is None:
                published=getattr(published, 'aq_parent', None)
                if published is None:
                    raise t, v, traceback
            else:
                break

        client=published
        while 1:
            if getattr(client, 'standard_error_message', None) is not None:
                break
            client=getattr(client, 'aq_parent', None)
            if client is None:
                raise t, v, traceback

        if REQUEST.get('AUTHENTICATED_USER', None) is None:
            REQUEST['AUTHENTICATED_USER']=AccessControl.User.nobody

        try:
            f(client, REQUEST, t, v, traceback, error_log_url=error_log_url)
        except TypeError:
            # Pre 2.6 call signature
            f(client, REQUEST, t, v, traceback)

    finally:
        traceback=None

ac_logger = logging.getLogger('event.AccessControl')

class TransactionsManager:
    def begin(self,
              # Optimize global var lookups:
              transaction=transaction):
        transaction.begin()

    def commit(self):
        transaction.commit()

    def abort(self):
        transaction.abort()

    def recordMetaData(self, object, request,
                       # Optimize global var lookups:
                       hasattr=hasattr, getattr=getattr,
                       logger=ac_logger,
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

        T = transaction.get()
        T.note(path)
        auth_user=request_get('AUTHENTICATED_USER',None)
        if auth_user is not None:
            try:
                auth_folder = auth_user.aq_parent
            except AttributeError:
                # Most likely some product forgot to call __of__()
                # on the user object.
                ac_logger.warning(
                    'A user object of type %s has no aq_parent.',
                    type(auth_user)
                    )
                auth_path = request_get('AUTHENTICATION_PATH')
            else:
                auth_path = '/'.join(auth_folder.getPhysicalPath()[1:-1])

            T.setUser(auth_user.getId(), auth_path)



