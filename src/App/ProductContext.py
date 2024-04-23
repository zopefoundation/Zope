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
"""Objects providing context for product initialization
"""

import os
from logging import getLogger

import Products
from AccessControl.Permission import registerPermissions
from AccessControl.PermissionRole import PermissionRole
from App.FactoryDispatcher import FactoryDispatcher
from OFS.ObjectManager import ObjectManager
from zope.interface import implementedBy
from ZPublisher import zpublish
from ZPublisher import zpublish_marked
from ZPublisher import zpublish_wrap


if not hasattr(Products, 'meta_types'):
    Products.meta_types = ()
if not hasattr(Products, 'meta_classes'):
    Products.meta_classes = {}
    Products.meta_class_info = {}


_marker = []  # Create a new marker object
LOG = getLogger('ProductContext')


class ProductContext:

    def __init__(self, product, app, package):
        self.__prod = product
        self.__app = app
        self.__pack = package

    def registerClass(self, instance_class=None, meta_type='',
                      permission=None, constructors=(),
                      icon=None, permissions=None, legacy=(),
                      visibility="Global", interfaces=_marker,
                      container_filter=None, resources=()):
        """Register a constructor

        Keyword arguments are used to provide meta data:

        instance_class -- The class of the object that will be created.

        meta_type -- The kind of object being created
           This appears in add lists.  If not specified, then the class
           meta_type will be used.

        permission -- The permission name for the constructors.
           If not specified, then a permission name based on the
           meta type will be used.

        constructors -- A list of constructor methods
          A method can be a callable object with a __name__
          attribute giving the name the method should have in the
          product, or the method may be a tuple consisting of a
          name and a callable object.

          The first method will be used as the initial method called
          when creating an object.

        icon -- No longer used.

        permissions -- Additional permissions to be registered
           If not provided, then permissions defined in the
           class will be registered.

        legacy -- A list of legacy methods to be added to ObjectManager
                  for backward compatibility

        visibility -- "Global" if the object is globally visible, None else

        interfaces -- a list of the interfaces the object supports

        container_filter -- function that is called with an ObjectManager
           object as the only parameter, which should return a true object
           if the object is happy to be created in that container. The
           filter is called before showing ObjectManager's Add list,
           and before pasting (after object copy or cut), but not
           before calling an object's constructor.

        resources -- a sequence of resource specifications
           A resource specification is either an object with
           a __name__ attribute or a pair consisting of the resource
           name and an object.
           The resources are put into the ProductFactoryDispather's
           namespace under the specified name.

        """
        pack = self.__pack
        initial = constructors[0]
        productObject = self.__prod
        pid = productObject.id

        if instance_class is not None and not zpublish_marked(instance_class):
            zpublish(instance_class)

        if permissions:
            if isinstance(permissions, str):  # You goofed it!
                raise TypeError(
                    'Product context permissions should be a '
                    'list of permissions not a string', permissions)
            for p in permissions:
                if isinstance(p, tuple):
                    p, default = p
                    registerPermissions(((p, (), default),))
                else:
                    registerPermissions(((p, ()),))

        ############################################################
        # Constructor permission setup
        if permission is None:
            permission = "Add %ss" % (meta_type or instance_class.meta_type)

        if isinstance(permission, tuple):
            permission, default = permission
        else:
            default = ('Manager',)

        pr = PermissionRole(permission, default)
        registerPermissions(((permission, (), default),))
        ############################################################

        OM = ObjectManager

        for method in legacy:
            if isinstance(method, tuple):
                name, method = method
                mname = method.__name__
                aliased = 1
            else:
                name = method.__name__
                aliased = 0
            if name not in OM.__dict__:
                method = zpublish_wrap(method)
                setattr(OM, name, method)
                setattr(OM, name + '__roles__', pr)
                if aliased:
                    # Set the unaliased method name and its roles
                    # to avoid security holes.  XXX: All "legacy"
                    # methods need to be eliminated.
                    setattr(OM, mname, method)
                    setattr(OM, mname + '__roles__', pr)

        if isinstance(initial, tuple):
            name, initial = initial
        else:
            name = initial.__name__

        fd = getattr(pack, '__FactoryDispatcher__', None)
        if fd is None:
            class __FactoryDispatcher__(FactoryDispatcher):
                "Factory Dispatcher for a Specific Product"

            fd = pack.__FactoryDispatcher__ = __FactoryDispatcher__

        if not hasattr(pack, '_m'):
            pack._m = AttrDict(fd)

        m = pack._m

        if interfaces is _marker:
            if instance_class is None:
                interfaces = ()
            else:
                interfaces = tuple(implementedBy(instance_class))

        Products.meta_types = Products.meta_types + ({
            'name': meta_type or instance_class.meta_type,
            # 'action': The action in the add drop down in the ZMI. This is
            #           currently also required by the _verifyObjectPaste
            #           method of CopyContainers like Folders.
            'action': (f'manage_addProduct/{pid}/{name}'),
            # 'product': product id
            'product': pid,
            # 'permission': Guards the add action.
            'permission': permission,
            # 'visibility': A silly name. Doesn't have much to do with
            #               visibility. Allowed values: 'Global', None
            'visibility': visibility,
            # 'interfaces': A tuple of oldstyle and/or newstyle interfaces.
            'interfaces': interfaces,
            'instance': instance_class,
            'container_filter': container_filter
        },)

        m[name] = zpublish_wrap(initial)
        m[name + '__roles__'] = pr

        for method in constructors[1:]:
            if isinstance(method, tuple):
                name, method = method
            else:
                name = os.path.split(method.__name__)[-1]
            if name not in productObject.__dict__:
                if not callable(method):
                    # This code is here because ``Products.CMFCore`` and
                    # ``Products.CMFPlone`` abuse the ``constructors``
                    # parameter to register resources violating the explicit
                    # condition that constructors must be callable.
                    # It should go away once those components have been fixed.
                    from warnings import warn
                    warn("Constructors must be callable; "
                         "please use `resources` "
                         "(rather than `constructors`) to register "
                         "non callable objects",
                         DeprecationWarning,
                         2)
                    m[name] = method
                else:
                    m[name] = zpublish_wrap(method)
                m[name + '__roles__'] = pr

        for resource in resources:
            if isinstance(resource, tuple):
                name, resource = resource
            else:
                name = resource.__name__
            if name not in productObject.__dict__:
                m[name] = resource
                m[name + '__roles__'] = pr

    def getApplication(self):
        return self.__app


class AttrDict:

    def __init__(self, ob):
        self.ob = ob

    def __contains__(self, name):
        return hasattr(self.ob, name)

    def __getitem__(self, name):
        return getattr(self.ob, name)

    def __setitem__(self, name, v):
        setattr(self.ob, name, v)
