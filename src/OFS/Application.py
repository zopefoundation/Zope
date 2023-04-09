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
"""Application support
"""

import os
import sys
from logging import getLogger

import Products
import transaction
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permission import ApplicationDefaultPermissions
from AccessControl.Permissions import view_management_screens
from Acquisition import aq_base
from App import FactoryDispatcher
from App.ApplicationManager import ApplicationManager
from App.ProductContext import ProductContext
from App.version_txt import getZopeVersion
from DateTime import DateTime
from OFS.FindSupport import FindSupport
from OFS.metaconfigure import get_packages_to_initialize
from OFS.metaconfigure import package_initialized
from OFS.userfolder import UserFolder
from webdav.NullResource import NullResource
from zExceptions import Forbidden
from zExceptions import Redirect as RedirectException
from zope.interface import implementer

from . import Folder
from . import misc_
from .interfaces import IApplication
from .misc_ import Misc_


LOG = getLogger('Application')

APP_MANAGER = None


@implementer(IApplication)
class Application(ApplicationDefaultPermissions, Folder.Folder, FindSupport):
    """Top-level system object"""

    security = ClassSecurityInfo()

    title = 'Zope'
    __defined_roles__ = ('Manager', 'Anonymous', 'Owner')
    __error_log__ = None
    isTopLevelPrincipiaApplicationObject = 1

    p_ = misc_.p_
    misc_ = misc_.misc_
    _reserved_names = ('Control_Panel', )

    # This class-default __allow_groups__ ensures that the
    # emergency user can still access the system if the top-level
    # UserFolder is deleted. This is necessary to allow people
    # to replace the top-level UserFolder object.
    __allow_groups__ = UserFolder()

    def __init__(self):
        # Initialize users
        uf = UserFolder()
        self.__allow_groups__ = uf
        self._setObject('acl_users', uf)

    def getId(self):
        try:
            return self.REQUEST['SCRIPT_NAME'][1:]
        except (KeyError, TypeError):
            return self.title

    def title_and_id(self):
        return self.title

    def title_or_id(self):
        return self.title

    def __class_init__(self):
        InitializeClass(self)

    @property
    def Control_Panel(self):
        return APP_MANAGER.__of__(self)

    def Redirect(self, destination, URL1):
        # Utility function to allow user-controlled redirects.
        # No docstring please, we do not want an open redirect
        # available as url.
        if destination.find('//') >= 0:
            raise RedirectException(destination)
        raise RedirectException(f"{URL1}/{destination}")

    ZopeRedirect = Redirect

    def __bobo_traverse__(self, REQUEST, name=None):
        if name is None:
            # Make this more explicit, otherwise getattr(self, name)
            # would raise a TypeError getattr(): attribute name must be string
            return None

        if name == 'Control_Panel':
            return APP_MANAGER.__of__(self)
        try:
            return getattr(self, name)
        except AttributeError:
            pass

        try:
            return self[name]
        except KeyError:
            pass

        method = REQUEST.get('REQUEST_METHOD', 'GET')

        if method not in ('GET', 'POST'):
            return NullResource(self, name, REQUEST).__of__(self)

        # Waaa. unrestrictedTraverse calls us with a fake REQUEST.
        # There is probably a better fix for this.
        try:
            REQUEST.RESPONSE.notFoundError(f"{name}\n{method}")
        except AttributeError:
            raise KeyError(name)

    def ZopeTime(self, *args):
        """Utility function to return current date/time"""
        return DateTime(*args)

    @security.protected(view_management_screens)
    def ZopeVersion(self, major=False):
        """Utility method to return the Zope version

        Restricted to ZMI to prevent information disclosure
        """
        zversion = getZopeVersion()
        if major:
            return zversion.major
        else:
            version = f'{zversion.major}.{zversion.minor}.{zversion.micro}'
            if zversion.status:
                version += f'.{zversion.status}{zversion.release}'

            return version

    def DELETE(self, REQUEST, RESPONSE):
        """Delete a resource object."""
        self.dav__init(REQUEST, RESPONSE)
        raise Forbidden('This resource cannot be deleted.')

    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location."""
        self.dav__init(REQUEST, RESPONSE)
        raise Forbidden('This resource cannot be moved.')

    def absolute_url(self, relative=0):
        """The absolute URL of the root object is BASE1 or "/".
        """
        if relative:
            return ''
        try:
            # Take advantage of computed URL cache
            return self.REQUEST['BASE1']
        except (AttributeError, KeyError):
            return '/'

    def absolute_url_path(self):
        """The absolute URL path of the root object is BASEPATH1 or "/".
        """
        try:
            return self.REQUEST['BASEPATH1'] or '/'
        except (AttributeError, KeyError):
            return '/'

    def virtual_url_path(self):
        """The virtual URL path of the root object is empty.
        """
        return ''

    def getPhysicalRoot(self):
        return self

    def getPhysicalPath(self):
        # Get the physical path of the object.
        #
        # Returns a path (an immutable sequence of strings) that can be used to
        # access this object again later, for example in a copy/paste
        # operation.  getPhysicalRoot() and getPhysicalPath() are designed to
        # operate together.
        #
        # We're at the base of the path.
        return ('', )


InitializeClass(Application)


def initialize(app):
    initializer = AppInitializer(app)
    initializer.initialize()


class AppInitializer:
    """ Initialize an Application object (called at startup) """

    def __init__(self, app):
        self.app = (app,)

    def getApp(self):
        # this is probably necessary, but avoid acquisition anyway
        return self.app[0]

    def commit(self, note):
        transaction.get().note(note)
        transaction.commit()

    def initialize(self):
        # make sure to preserve relative ordering of calls below.
        self.install_app_manager()
        self.install_required_roles()
        self.install_inituser()
        self.install_products()
        self.install_standards()
        self.install_virtual_hosting()
        self.install_root_view()

    def install_app_manager(self):
        global APP_MANAGER
        APP_MANAGER = ApplicationManager()

        # Remove persistent Control Panel.
        app = self.getApp()
        app._p_activate()

        if 'Control_Panel' in list(app.__dict__.keys()):
            del app.__dict__['Control_Panel']
            app._objects = tuple(i for i in app._objects
                                 if i['id'] != 'Control_Panel')
            self.commit('Removed persistent Control_Panel')

    def install_required_roles(self):
        app = self.getApp()

        # Ensure that Owner role exists.
        if hasattr(app, '__ac_roles__') and not ('Owner' in app.__ac_roles__):
            app.__ac_roles__ = app.__ac_roles__ + ('Owner',)
            self.commit('Added Owner role')

        # ensure the Authenticated role exists.
        if hasattr(app, '__ac_roles__'):
            if 'Authenticated' not in app.__ac_roles__:
                app.__ac_roles__ = app.__ac_roles__ + ('Authenticated',)
                self.commit('Added Authenticated role')

    def install_inituser(self):
        app = self.getApp()
        # Install the initial user.
        if hasattr(app, 'acl_users'):
            users = app.acl_users
            if hasattr(users, '_createInitialUser'):
                app.acl_users._createInitialUser()
                self.commit('Created initial user')
            users = aq_base(users)
            migrated = getattr(users, '_ofs_migrated', False)
            if not migrated:
                klass = users.__class__
                from OFS.userfolder import UserFolder
                if klass is UserFolder:
                    # zope.deferredimport does a thourough job, so the class
                    # looks like it's from the new location already. And we
                    # don't want to migrate any custom user folders here.
                    users.__class__ = UserFolder
                    users._ofs_migrated = True
                    users._p_changed = True
                    app._p_changed = True
                    transaction.get().note('Migrated user folder')
                    transaction.commit()

    def install_virtual_hosting(self):
        app = self.getApp()
        if 'virtual_hosting' not in app:
            from Products.SiteAccess.VirtualHostMonster import \
                VirtualHostMonster
            any_vhm = [obj for obj in app.values()
                       if isinstance(obj, VirtualHostMonster)]
            if not any_vhm:
                vhm = VirtualHostMonster()
                vhm.id = 'virtual_hosting'
                vhm.addToContainer(app)
                self.commit('Added virtual_hosting')

    def install_root_view(self):
        app = self.getApp()
        if 'index_html' not in app:
            from Products.PageTemplates.ZopePageTemplate import \
                ZopePageTemplate
            root_pt = ZopePageTemplate('index_html')
            root_pt.pt_setTitle('Auto-generated default page')
            app._setObject('index_html', root_pt)
            self.commit('Added default view for root object')

    def install_products(self):
        return install_products(self.getApp())

    def install_standards(self):
        app = self.getApp()
        if getattr(app, '_standard_objects_have_been_added', None) is not None:
            delattr(app, '_standard_objects_have_been_added')
        if getattr(app, '_initializer_registry', None) is not None:
            delattr(app, '_initializer_registry')
        transaction.get().note('Removed unused application attributes.')
        transaction.commit()


def install_products(app=None):
    folder_permissions = get_folder_permissions()
    meta_types = []
    done = {}
    for priority, product_name, index, product_dir in get_products():
        # For each product, we will import it and try to call the
        # intialize() method in the product __init__ module. If
        # the method doesnt exist, we put the old-style information
        # together and do a default initialization.
        if product_name in done:
            continue
        done[product_name] = 1
        install_product(app, product_dir, product_name, meta_types,
                        folder_permissions)

    # Delayed install of packages-as-products
    for module, init_func in tuple(get_packages_to_initialize()):
        install_package(app, module, init_func)

    Products.meta_types = Products.meta_types + tuple(meta_types)
    InitializeClass(Folder.Folder)


def _is_package(product_dir, product_name):
    package_dir = os.path.join(product_dir, product_name)
    if not os.path.isdir(package_dir):
        return False

    init_py = os.path.join(package_dir, '__init__.py')
    if not os.path.exists(init_py) and \
       not os.path.exists(init_py + 'c') and \
       not os.path.exists(init_py + 'o'):
        return False
    return True


def get_products():
    """ Return a list of tuples in the form:
    [(priority, dir_name, index, base_dir), ...] for each Product directory
    found, sort before returning """
    products = []
    for index, product_dir in enumerate(Products.__path__):
        product_names = os.listdir(product_dir)
        for product_name in product_names:
            if _is_package(product_dir, product_name):
                # i is used as sort ordering in case a conflict exists
                # between Product names.  Products will be found as
                # per the ordering of Products.__path__
                products.append((0, product_name, index, product_dir))
    products.sort()
    return products


def import_products():
    done = {}
    for priority, product_name, index, product_dir in get_products():
        if product_name in done:
            LOG.warning(
                'Duplicate Product name: '
                'After loading Product %r from %r, '
                'I skipped the one in %r.' % (
                    product_name, done[product_name], product_dir))
            continue
        done[product_name] = product_dir
        import_product(product_dir, product_name)
    return list(done.keys())


def import_product(product_dir, product_name, raise_exc=None):
    if not _is_package(product_dir, product_name):
        return

    global_dict = globals()
    product = __import__("Products.%s" % product_name,
                         global_dict, global_dict, ('__doc__', ))
    if hasattr(product, '__module_aliases__'):
        for k, v in product.__module_aliases__:
            if k not in sys.modules:
                if isinstance(v, str) and v in sys.modules:
                    v = sys.modules[v]
                sys.modules[k] = v


def get_folder_permissions():
    folder_permissions = {}
    for p in Folder.Folder.__ac_permissions__:
        permission, names = p[:2]
        folder_permissions[permission] = names
    return folder_permissions


def install_product(app, product_dir, product_name, meta_types,
                    folder_permissions, raise_exc=None):
    if not _is_package(product_dir, product_name):
        return

    __traceback_info__ = product_name
    global_dict = globals()
    product = __import__("Products.%s" % product_name,
                         global_dict, global_dict, ('__doc__', ))

    # Install items into the misc_ namespace, used by products
    # and the framework itself to store common static resources
    # like icon images.
    misc_ = pgetattr(product, 'misc_', {})
    if misc_:
        if isinstance(misc_, dict):
            misc_ = Misc_(product_name, misc_)
        setattr(Application.misc_, product_name, misc_)

    productObject = FactoryDispatcher.Product(product_name)
    context = ProductContext(productObject, app, product)

    # Look for an 'initialize' method in the product.
    initmethod = pgetattr(product, 'initialize', None)
    if initmethod is not None:
        initmethod(context)


def install_package(app, module, init_func, raise_exc=None):
    """Installs a Python package like a product."""
    name = module.__name__
    product = FactoryDispatcher.Product(name)
    product.package_name = name

    if init_func is not None:
        newContext = ProductContext(product, app, module)
        init_func(newContext)

    package_initialized(module, init_func)


def pgetattr(product, name, default=install_products, __init__=0):
    if not __init__ and hasattr(product, name):
        return getattr(product, name)
    if hasattr(product, '__init__'):
        product = product.__init__
        if hasattr(product, name):
            return getattr(product, name)

    if default is not install_products:
        return default

    raise AttributeError(name)
