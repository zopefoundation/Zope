import logging
import os

import App.config
import Products
from OFS.subscribers import deprecatedManageAddDeleteClasses
from zope.component import getUtility
from zope.configuration import xmlconfig
from zope.interface import implementedBy
from zope.security.interfaces import IPermission
from zope.testing.cleanup import addCleanUp  # NOQA


debug_mode = App.config.getConfiguration().debug_mode
logger = logging.getLogger('OFS')

_packages_to_initialize = []
_register_monkies = []
_registered_packages = []
_meta_type_regs = []


def findProducts():
    # Warning: This function only works reliable if called *after* running
    # OFS.Application.import_products. ZopeLite tests disable import_products.
    from types import ModuleType
    products = []
    for name in dir(Products):
        product = getattr(Products, name)
        if isinstance(product, ModuleType) and hasattr(product, '__file__'):
            products.append(product)
    return products


def loadProducts(_context, file=None, files=None, package=None):
    if file is None:
        # set the default
        file = 'configure.zcml'

    if files is not None or package is not None:
        raise ValueError("Neither the files or package argument is supported.")

    # now load the files if they exist
    for product in findProducts():
        zcml = os.path.join(os.path.dirname(product.__file__), file)
        if os.path.isfile(zcml):
            xmlconfig.include(_context, zcml, package=product)


def loadProductsOverrides(_context, file=None, files=None, package=None):
    if file is None:
        # set the default
        file = 'overrides.zcml'

    if files is not None or package is not None:
        raise ValueError("Neither the files or package argument is supported.")

    # now load the files if they exist
    for product in findProducts():
        zcml = os.path.join(os.path.dirname(product.__file__), file)
        if os.path.isfile(zcml):
            xmlconfig.includeOverrides(_context, zcml, package=product)


def get_registered_packages():
    global _registered_packages
    return _registered_packages


def set_registered_packages(packages):
    global _registered_packages
    _registered_packages = packages


def has_package(package):
    return package in [m.__name__ for m in get_registered_packages()]


def get_packages_to_initialize():
    global _packages_to_initialize
    return _packages_to_initialize


def package_initialized(module, init_func):
    global _packages_to_initialize
    _packages_to_initialize.remove((module, init_func))


def _registerPackage(module_, init_func=None):
    """Registers the given python package as a Zope 2 style product
    """
    if not hasattr(module_, '__path__'):
        raise ValueError("Must be a package and the "
                         "package must be filesystem based")

    registered_packages = get_registered_packages()
    registered_packages.append(module_)

    # Delay the actual setup until the usual product loading time in
    # OFS.Application. Otherwise, we may get database write errors in
    # ZEO, when there's no connection with which to write an entry to
    # Control_Panel. We would also get multiple calls to initialize().
    to_initialize = get_packages_to_initialize()
    to_initialize.append((module_, init_func,))


def registerPackage(_context, package, initialize=None):
    """ZCML directive function for registering a python package product
    """

    _context.action(
        discriminator=('registerPackage', package),
        callable=_registerPackage,
        args=(package, initialize)
    )


def _registerClass(class_, meta_type, permission, addview, icon, global_):
    setattr(class_, 'meta_type', meta_type)

    permission_obj = getUtility(IPermission, permission)
    interfaces = tuple(implementedBy(class_))

    info = {'name': meta_type,
            'action': addview and ('+/%s' % addview) or '',
            'product': 'OFS',
            'permission': str(permission_obj.title),
            'visibility': global_ and 'Global' or None,
            'interfaces': interfaces,
            'instance': class_,
            'container_filter': None}

    meta_types = getattr(Products, 'meta_types', ())
    meta_types += (info,)
    Products.meta_types = meta_types

    _register_monkies.append(class_)
    _meta_type_regs.append(meta_type)


def registerClass(_context, class_, meta_type, permission, addview=None,
                  icon=None, global_=True):
    _context.action(
        discriminator=('registerClass', meta_type),
        callable=_registerClass,
        args=(class_, meta_type, permission, addview, icon, global_)
    )


def unregisterClass(class_):
    delattr(class_, 'meta_type')


def setDeprecatedManageAddDelete(class_):
    """Instances of the class will still see their old methods called."""
    deprecatedManageAddDeleteClasses.append(class_)


def deprecatedManageAddDelete(_context, class_):
    _context.action(
        discriminator=('five:deprecatedManageAddDelete', class_),
        callable=setDeprecatedManageAddDelete,
        args=(class_,),
    )


def cleanUp():
    deprecatedManageAddDeleteClasses[:] = []

    global _register_monkies
    for class_ in _register_monkies:
        unregisterClass(class_)
    _register_monkies = []

    global _packages_to_initialize
    _packages_to_initialize = []

    global _registered_packages
    _registered_packages = []

    global _meta_type_regs
    old = getattr(Products, 'meta_types', ())
    new = tuple([info for info in old if info['name'] not in _meta_type_regs])
    setattr(Products, 'meta_types', new)
    _meta_type_regs = []


addCleanUp(cleanUp)
del addCleanUp
