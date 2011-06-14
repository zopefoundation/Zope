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

from zope.component import queryMultiAdapter
from zope.event import notify
from zope.processlifetime import DatabaseOpened
from zope.processlifetime import DatabaseOpenedWithRoot

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition.interfaces import IAcquirer
from App.config import getConfiguration
from time import asctime
from zExceptions import Redirect
from zExceptions import Unauthorized
from ZODB.POSException import ConflictError
import transaction
import AccessControl.User
import ExtensionClass
import imp
import logging
import OFS.Application
import sys
import ZODB
import App.ZApplication
import Zope2
import ZPublisher

app = None
startup_time = asctime()


def load_zcml():
    # This hook is overriden by ZopeTestCase
    from .zcml import load_site
    load_site()

    # Set up Zope2 specific vocabulary registry
    from .schema import configure_vocabulary_registry
    configure_vocabulary_registry()


def startup():
    from App.PersistentExtra import patchPersistent
    import Globals  # to set / fetch data
    patchPersistent()

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

    notify(DatabaseOpened(DB))

    Globals.BobobaseName = DB.getName()

    if DB.getActivityMonitor() is None:
        from ZODB.ActivityMonitor import ActivityMonitor
        DB.setActivityMonitor(ActivityMonitor())

    Globals.DB = DB
    Zope2.DB = DB

    # Hook for providing multiple transaction object manager undo support:
    Globals.UndoManager = DB

    Globals.opened.append(DB)
    import ClassFactory
    DB.classFactory = ClassFactory.ClassFactory

    # "Log on" as system user
    newSecurityManager(None, AccessControl.User.system)

    # Set up the CA
    load_zcml()

    # Set up the "app" object that automagically opens
    # connections
    app = App.ZApplication.ZApplicationWrapper(
        DB, 'Application', OFS.Application.Application, ()
    )
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

    notify(DatabaseOpenedWithRoot(DB))

    Zope2.zpublisher_transactions_manager = TransactionsManager()
    Zope2.zpublisher_exception_hook = zpublisher_exception_hook
    Zope2.zpublisher_validated_hook = validated_hook
    Zope2.__bobo_before__ = noSecurityManager


def validated_hook(request, user):
    newSecurityManager(request, user)


class RequestContainer(ExtensionClass.Base):

    def __init__(self, r):
        self.REQUEST=r


class ZPublisherExceptionHook:

    def __init__(self):
        self.conflict_errors = 0
        self.unresolved_conflict_errors = 0
        self.conflict_logger = logging.getLogger('ZPublisher.Conflict')
        self.error_message = 'standard_error_message'
        self.raise_error_message = 'raise_standardErrorMessage'

    def logConflicts(self, v, REQUEST):
        self.conflict_errors += 1
        level = getattr(getConfiguration(), 'conflict_error_log_level', 0)
        if not self.conflict_logger.isEnabledFor(level):
            return False
        self.conflict_logger.log(
            level,
            "%s at %s: %s (%d conflicts (%d unresolved) "
            "since startup at %s)",
            v.__class__.__name__,
            REQUEST.get('PATH_INFO', '<unknown>'),
            v,
            self.conflict_errors,
            self.unresolved_conflict_errors,
            startup_time)
        return True

    def __call__(self, published, REQUEST, t, v, traceback):
        try:
            if t is SystemExit or issubclass(t, Redirect):
                raise t, v, traceback

            if issubclass(t, ConflictError):
                self.logConflicts(v, REQUEST)
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
                    self.unresolved_conflict_errors += 1

            try:
                log = aq_acquire(published, '__error_log__', containment=1)
            except AttributeError:
                error_log_url = ''
            else:
                error_log_url = log.raising((t, v, traceback))

            if (REQUEST is None or
                (getattr(REQUEST.get('RESPONSE', None), '_error_format', '')
                 != 'text/html')):
                raise t, v, traceback

            # Lookup a view for the exception and render it, then
            # raise the rendered value as the exception value
            # (basically the same that 'raise_standardErrorMessage'
            # does. The view is named 'index.html' because that's what
            # zope.publisher uses as well.
            view = queryMultiAdapter((v, REQUEST), name=u'index.html')
            if view is not None:
                if IAcquirer.providedBy(view) and IAcquirer.providedBy(published):
                    view = view.__of__(published)
                else:
                    view.__parent__ = published
                v = view()
                if issubclass(t, Unauthorized):
                    # Re-raise Unauthorized to make sure it is handled
                    # correctly. We can't do that with all exceptions
                    # because some don't work with the rendered v as
                    # argument.
                    raise t, v, traceback
                response = REQUEST.RESPONSE
                response.setStatus(t)
                response.setBody(v)
                return response

            if (published is None or published is app or
                isinstance(published, list)):
                # At least get the top-level object
                published=app.__bobo_traverse__(REQUEST).__of__(
                    RequestContainer(REQUEST))

            published = getattr(published, 'im_self', published)
            while 1:
                f = getattr(published, self.raise_error_message, None)
                if f is None:
                    published = aq_parent(published)
                    if published is None:
                        raise t, v, traceback
                else:
                    break

            client = published
            while 1:
                if getattr(client, self.error_message, None) is not None:
                    break
                client = aq_parent(client)
                # If we are going in circles without getting the error_message
                # just raise
                if client is None or aq_base(client) is aq_base(published):
                    raise t, v, traceback

            if REQUEST.get('AUTHENTICATED_USER', None) is None:
                REQUEST['AUTHENTICATED_USER'] = AccessControl.User.nobody

            result = f(client, REQUEST, t, v, traceback,
                       error_log_url=error_log_url)
            if result is not None:
                t, v, traceback = result
                if issubclass(t, Unauthorized):
                    # Re-raise Unauthorized to make sure it is handled
                    # correctly. We can't do that with all exceptions
                    # because some don't work with the rendered v as
                    # argument.
                    raise t, v, traceback
                response = REQUEST.RESPONSE
                response.setStatus(t)
                response.setBody(v)
                return response
        finally:
            traceback = None

zpublisher_exception_hook = ZPublisherExceptionHook()
ac_logger = logging.getLogger('event.AccessControl')

class TransactionsManager:
    def begin(self,
              # Optimize global var lookups:
              transaction=transaction):
        transaction.begin()

    def commit(self):
        if hasattr(transaction, 'isDoomed') and transaction.isDoomed():
            transaction.abort()
        else:
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
                if getattr(object, '__name__', None) is None:
                    object = None
                    break
                to_append = (object.__name__,) + to_append
                object = aq_parent(aq_inner(object))

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
            auth_folder = aq_parent(auth_user)
            if auth_folder is None:
                ac_logger.warning(
                    'A user object of type %s has no aq_parent.',
                    type(auth_user)
                    )
                auth_path = request_get('AUTHENTICATION_PATH')
            else:
                auth_path = '/'.join(auth_folder.getPhysicalPath()[1:-1])

            T.setUser(auth_user.getId(), auth_path)
