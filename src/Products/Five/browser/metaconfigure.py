##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Browser directives

Directives to emulate the 'http://namespaces.zope.org/browser'
namespace in ZCML known from zope.app.
"""

import os
import sys
from inspect import isfunction
from inspect import ismethod

import zope.browserpage.metaconfigure
import zope.browserpage.simpleviewclass
from AccessControl.class_init import InitializeClass
from AccessControl.security import CheckerPrivateId
from AccessControl.security import getSecurityInfo
from AccessControl.security import protectClass
from AccessControl.security import protectName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser.resource import DirectoryResourceFactory
from Products.Five.browser.resource import FileResourceFactory
from Products.Five.browser.resource import ImageResourceFactory
from Products.Five.browser.resource import PageTemplateResourceFactory
from zope.browserpage.metaconfigure import _handle_allowed_attributes
from zope.browserpage.metaconfigure import _handle_allowed_interface
from zope.browserpage.metaconfigure import _handle_for
from zope.browserpage.metaconfigure import _handle_menu
from zope.browserpage.metaconfigure import _handle_permission
from zope.browserpage.metaconfigure import providesCallable
from zope.browserpage.metadirectives import IViewDirective
from zope.component import queryMultiAdapter
from zope.component.interface import provideInterface
from zope.component.zcml import handler
from zope.configuration.exceptions import ConfigurationError
from zope.interface import Interface
from zope.interface import classImplements
from zope.publisher.interfaces import NotFound
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.security.zcml import Permission


def is_method(func):
    # Under Python 3, there are no unbound methods
    return isfunction(func) or ismethod(func)


def _configure_z2security(_context, new_class, required):
    _context.action(
        discriminator=('five:protectClass', new_class),
        callable=protectClass,
        args=(new_class, required.pop(''))
    )
    for attr, permission in required.items():
        _context.action(
            discriminator=('five:protectName', new_class, attr),
            callable=protectName,
            args=(new_class, attr, permission)
        )
    # Make everything else private
    private_attrs = [name for name in dir(new_class)
                     if ((not name.startswith('_'))
                         and (name not in required)
                         and is_method(getattr(new_class, name)))]
    for attr in private_attrs:
        _context.action(
            discriminator=('five:protectName', new_class, attr),
            callable=protectName,
            args=(new_class, attr, CheckerPrivateId, False)
        )
    # Protect the class
    _context.action(
        discriminator=('five:initialize:class', new_class),
        callable=InitializeClass,
        args=(new_class,)
    )


def page(_context, name, permission, for_=Interface,
         layer=IDefaultBrowserLayer, template=None, class_=None,
         allowed_interface=None, allowed_attributes=None,
         attribute='__call__', menu=None, title=None):
    name = str(name)  # De-unicode
    _handle_menu(_context, menu, title, [for_], name, permission, layer)
    required = {}

    permission = _handle_permission(_context, permission)

    if not (class_ or template):
        raise ConfigurationError("Must specify a class or template")

    if attribute != '__call__':
        if template:
            raise ConfigurationError(
                "Attribute and template cannot be used together.")

        if not class_:
            raise ConfigurationError(
                "A class must be provided if attribute is used")

    if template:
        template = os.path.abspath(str(_context.path(template)))
        if not os.path.isfile(template):
            raise ConfigurationError("No such file", template)

    # TODO: new __name__ attribute must be tested
    if class_:
        if attribute != '__call__':
            if not hasattr(class_, attribute):
                raise ConfigurationError(
                    "The provided class doesn't have the specified attribute."
                )
        if template:
            # class and template
            new_class = SimpleViewClass(template, bases=(class_, ), name=name)
        else:
            cdict = {}
            cdict['__name__'] = name
            cdict['__page_attribute__'] = attribute
            cdict.update(getSecurityInfo(class_))
            new_class = type(class_.__name__, (class_, simple,), cdict)

            if attribute != "__call__":
                # in case the attribute does not provide a docstring,
                # ZPublisher refuses to publish it.  So, as a workaround,
                # we provide a stub docstring
                func = getattr(new_class, attribute)
                if not func.__doc__:
                    # cannot test for MethodType/UnboundMethod here
                    # because of ExtensionClass
                    if hasattr(func, '__func__'):
                        # you can only set a docstring on functions, not
                        # on method objects
                        func = func.__func__
                    func.__doc__ = "Stub docstring to make ZPublisher work"

        if hasattr(class_, '__implements__'):
            classImplements(new_class, IBrowserPublisher)

    else:
        # template
        new_class = SimpleViewClass(template, name=name)

    for n in ('', attribute):
        required[n] = permission

    _handle_allowed_interface(_context, allowed_interface, permission,
                              required)
    _handle_allowed_attributes(_context, allowed_attributes, permission,
                               required)

    _handle_for(_context, for_)
    expected = [attribute, 'browserDefault', '__call__', 'publishTraverse']
    new_class._simple__whitelist = set(required) - set(expected)

    _configure_z2security(_context, new_class, required)

    _context.action(
        discriminator=('view', (for_, layer), name, IBrowserRequest),
        callable=handler,
        args=('registerAdapter',
              new_class, (for_, layer), Interface, name, _context.info),
    )


class pages(zope.browserpage.metaconfigure.pages):

    def page(self, _context, name, attribute='__call__', template=None,
             menu=None, title=None):
        return page(_context,
                    name=name,
                    attribute=attribute,
                    template=template,
                    menu=menu, title=title,
                    **(self.opts))


class IFiveViewDirective(IViewDirective):

    permission = Permission(
        title="Permission",
        description="The permission needed to use the view.",
        required=False,
    )


class view(zope.browserpage.metaconfigure.view):

    def __call__(self):
        (_context, name, (for_, layer), permission, class_,
         allowed_interface, allowed_attributes) = self.args

        name = str(name)  # De-unicode

        required = {}

        cdict = {}
        pages = {}

        for pname, attribute, template in self.pages:

            if template:
                cdict[pname] = ViewPageTemplateFile(template)
                if attribute and attribute != name:
                    cdict[attribute] = cdict[pname]
            else:
                if not hasattr(class_, attribute):
                    raise ConfigurationError("Undefined attribute",
                                             attribute)

            attribute = attribute or pname
            required[pname] = permission

            pages[pname] = attribute

        # This should go away, but noone seems to remember what to do. :-(
        if hasattr(class_, 'publishTraverse'):

            def publishTraverse(self, request, name,
                                pages=pages, getattr=getattr):

                if name in pages:
                    return getattr(self, pages[name])
                view = queryMultiAdapter((self, request), name=name)
                if view is not None:
                    return view

                m = class_.publishTraverse.__get__(self)
                return m(request, name)

        else:
            def publishTraverse(self, request, name,
                                pages=pages, getattr=getattr):

                if name in pages:
                    return getattr(self, pages[name])
                view = queryMultiAdapter((self, request), name=name)
                if view is not None:
                    return view

                raise NotFound(self, name, request)

        cdict['publishTraverse'] = publishTraverse

        if not hasattr(class_, 'browserDefault'):
            if self.default or self.pages:
                default = self.default or self.pages[0][0]
                cdict['browserDefault'] = (
                    lambda self, request, default=default:
                    (self, (default, ))
                )
            elif providesCallable(class_):
                cdict['browserDefault'] = (
                    lambda self, request: (self, ())
                )

        if class_ is not None:
            cdict.update(getSecurityInfo(class_))
            bases = (class_, simple)
        else:
            bases = (simple,)

        try:
            cname = str(name)
        except Exception:
            cname = "GeneratedClass"

        cdict['__name__'] = name
        newclass = type(cname, bases, cdict)

        for n in ('',):
            required[n] = permission

        _handle_allowed_interface(_context, allowed_interface, permission,
                                  required)
        _handle_allowed_attributes(_context, allowed_attributes, permission,
                                   required)
        _handle_for(_context, for_)

        _configure_z2security(_context, newclass, required)

        if self.provides is not None:
            _context.action(
                discriminator=None,
                callable=provideInterface,
                args=('', self.provides)
            )

        _context.action(
            discriminator=('view', (for_, layer), name, self.provides),
            callable=handler,
            args=('registerAdapter',
                  newclass, (for_, layer), self.provides, name,
                  _context.info),
        )


_factory_map = {'image': {'prefix': 'ImageResource',
                          'count': 0,
                          'factory': ImageResourceFactory},
                'file': {'prefix': 'FileResource',
                         'count': 0,
                         'factory': FileResourceFactory},
                'template': {'prefix': 'PageTemplateResource',
                             'count': 0,
                             'factory': PageTemplateResourceFactory}
                }


def resource(_context, name, layer=IDefaultBrowserLayer,
             permission='zope.Public', file=None, image=None, template=None):

    if (file and image) or \
       (file and template) or \
       (image and template) or \
       not (file or image or template):
        raise ConfigurationError(
            "Must use exactly one of file or image or template"
            "attributes for resource directives"
        )

    res = file or image or template
    res_type = (file and 'file') or \
               (image and 'image') or \
               (template and 'template')
    factory_info = _factory_map.get(res_type)
    factory_info['count'] += 1
    res_factory = factory_info['factory']
    class_name = f'{factory_info["prefix"]}{factory_info["count"]}'
    new_class = type(class_name, (res_factory.resource,), {})
    factory = res_factory(name, res, resource_factory=new_class)

    _context.action(
        discriminator=('resource', name, IBrowserRequest, layer),
        callable=handler,
        args=('registerAdapter',
              factory, (layer,), Interface, name, _context.info),
    )
    _context.action(
        discriminator=('five:protectClass', new_class),
        callable=protectClass,
        args=(new_class, permission)
    )
    _context.action(
        discriminator=('five:initialize:class', new_class),
        callable=InitializeClass,
        args=(new_class,)
    )


_rd_map = {
    ImageResourceFactory: {'prefix': 'DirContainedImageResource',
                           'count': 0},
    FileResourceFactory: {'prefix': 'DirContainedFileResource',
                          'count': 0},
    PageTemplateResourceFactory: {'prefix': 'DirContainedPTResource',
                                  'count': 0},
    DirectoryResourceFactory: {'prefix': 'DirectoryResource',
                               'count': 0}
}


def resourceDirectory(_context, name, directory, layer=IDefaultBrowserLayer,
                      permission='zope.Public'):

    if not os.path.isdir(directory):
        raise ConfigurationError(
            "Directory %s does not exist" % directory)

    resource = DirectoryResourceFactory.resource
    f_cache = {}
    resource_factories = dict(resource.resource_factories)
    resource_factories['default'] = resource.default_factory
    for ext, factory in resource_factories.items():
        if f_cache.get(factory) is not None:
            continue
        factory_info = _rd_map.get(factory)
        factory_info['count'] += 1
        class_name = f'{factory_info["prefix"]}{factory_info["count"]}'
        factory_name = f'{factory.__name__}{factory_info["count"]}'
        f_resource = type(class_name, (factory.resource,), {})
        f_cache[factory] = type(factory_name, (factory,),
                                {'resource': f_resource})
    for ext, factory in list(resource_factories.items()):
        resource_factories[ext] = f_cache[factory]
    default_factory = resource_factories['default']
    del resource_factories['default']

    cdict = {'resource_factories': resource_factories,
             'default_factory': default_factory}

    factory_info = _rd_map.get(DirectoryResourceFactory)
    factory_info['count'] += 1
    class_name = f'{factory_info["prefix"]}{factory_info["count"]}'
    dir_factory = type(class_name, (resource,), cdict)
    factory = DirectoryResourceFactory(name, directory,
                                       resource_factory=dir_factory)

    new_classes = [dir_factory] + [f.resource for f in f_cache.values()]

    _context.action(
        discriminator=('resource', name, IBrowserRequest, layer),
        callable=handler,
        args=('registerAdapter',
              factory, (layer,), Interface, name, _context.info),
    )
    for new_class in new_classes:
        _context.action(
            discriminator=('five:protectClass', new_class),
            callable=protectClass,
            args=(new_class, permission)
        )
        _context.action(
            discriminator=('five:initialize:class', new_class),
            callable=InitializeClass,
            args=(new_class,)
        )


class ViewNotCallableError(AttributeError, NotImplementedError):
    pass


class simple(zope.browserpage.metaconfigure.simple):

    # __call__ should have the same signature as the original method
    @property
    def __call__(self):
        # If a class doesn't provide it's own call, then get the attribute
        # given by the browser default.

        attr = self.__page_attribute__
        if attr == '__call__':
            raise ViewNotCallableError('__call__')

        return getattr(self, attr)


class ViewMixinForTemplates(zope.browserpage.simpleviewclass.simple):

    def __getitem__(self, name):
        if name == 'macros':
            return self.index.macros
        return self.index.macros[name]


# Original version: zope.browserpage.simpleviewclass.SimpleViewClass
def SimpleViewClass(src, offering=None, used_for=None, bases=(), name=''):
    if offering is None:
        offering = sys._getframe(1).f_globals

    bases += (ViewMixinForTemplates,)

    cdict = {'index': ViewPageTemplateFile(src, offering),
             '__name__': name}
    if bases:
        cdict.update(getSecurityInfo(bases[0]))
    class_ = type("SimpleViewClass from %s" % src, bases,
                  cdict)

    if used_for is not None:
        class_.__used_for__ = used_for

    return class_
