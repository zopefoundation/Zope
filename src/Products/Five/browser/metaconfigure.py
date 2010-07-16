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
from inspect import ismethod

from zope import component
from zope.interface import implements
from zope.interface import Interface
from zope.component.zcml import handler
from zope.component.interface import provideInterface
from zope.configuration.exceptions import ConfigurationError
from zope.publisher.interfaces import NotFound
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.security.zcml import Permission

import zope.browserpage.metaconfigure
from zope.browserpage.metaconfigure import providesCallable
from zope.browserpage.metaconfigure import _handle_menu
from zope.browserpage.metaconfigure import _handle_for
from zope.browserpage.metadirectives import IViewDirective

from AccessControl.class_init import InitializeClass
from AccessControl.security import getSecurityInfo
from AccessControl.security import protectClass
from AccessControl.security import protectName
from AccessControl.security import CheckerPrivateId

from Products.Five.browser import BrowserView
from Products.Five.browser.resource import FileResourceFactory
from Products.Five.browser.resource import ImageResourceFactory
from Products.Five.browser.resource import PageTemplateResourceFactory
from Products.Five.browser.resource import DirectoryResourceFactory
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.metaclass import makeClass


def page(_context, name, permission, for_,
         layer=IDefaultBrowserLayer, template=None, class_=None,
         allowed_interface=None, allowed_attributes=None,
         attribute='__call__', menu=None, title=None,
         ):

    _handle_menu(_context, menu, title, [for_], name, permission)

    if not (class_ or template):
        raise ConfigurationError("Must specify a class or template")
    if allowed_attributes is None:
        allowed_attributes = []
    if allowed_interface is not None:
        for interface in allowed_interface:
            allowed_attributes.extend(interface.names(all=True))

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

    if class_:
        if attribute != '__call__':
            if not hasattr(class_, attribute):
                raise ConfigurationError(
                    "The provided class doesn't have the specified attribute "
                    )
        cdict = getSecurityInfo(class_)
        cdict['__name__'] = name
        if template:
            new_class = makeClassForTemplate(template, bases=(class_, ),
                                             cdict=cdict, name=name)
        elif attribute != "__call__":
            # we're supposed to make a page for an attribute (read:
            # method) and it's not __call__.  We thus need to create a
            # new class using our mixin for attributes.
            cdict.update({'__page_attribute__': attribute})
            new_class = makeClass(class_.__name__,
                                  (class_, ViewMixinForAttributes),
                                  cdict)

            # in case the attribute does not provide a docstring,
            # ZPublisher refuses to publish it.  So, as a workaround,
            # we provide a stub docstring
            func = getattr(new_class, attribute)
            if not func.__doc__:
                # cannot test for MethodType/UnboundMethod here
                # because of ExtensionClass
                if hasattr(func, 'im_func'):
                    # you can only set a docstring on functions, not
                    # on method objects
                    func = func.im_func
                func.__doc__ = "Stub docstring to make ZPublisher work"
        else:
            # we could use the class verbatim here, but we'll execute
            # some security declarations on it so we really shouldn't
            # modify the original.  So, instead we make a new class
            # with just one base class -- the original
            new_class = makeClass(class_.__name__, 
                                  (class_, BrowserView), cdict)

    else:
        # template
        new_class = makeClassForTemplate(template, name=name)

    _handle_for(_context, for_)

    _context.action(
        discriminator = ('view', for_, name, IBrowserRequest, layer),
        callable = handler,
        args = ('registerAdapter',
                new_class, (for_, layer), Interface, name, _context.info),
        )
    _context.action(
        discriminator = ('five:protectClass', new_class),
        callable = protectClass,
        args = (new_class, permission)
        )
    if allowed_attributes:
        for attr in allowed_attributes:
            _context.action(
                discriminator = ('five:protectName', new_class, attr),
                callable = protectName,
                args = (new_class, attr, permission)
                )
    # Make everything else private
    allowed = [attribute] + (allowed_attributes or [])
    private_attrs = [name for name in dir(new_class)
                     if (not name.startswith('_')) and
                        (name not in allowed) and
                        ismethod(getattr(new_class, name))]
    for attr in private_attrs:
        _context.action(
            discriminator = ('five:protectName', new_class, attr),
            callable = protectName,
            args = (new_class, attr, CheckerPrivateId)
            )
    # Protect the class
    _context.action(
        discriminator = ('five:initialize:class', new_class),
        callable = InitializeClass,
        args = (new_class,)
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

# view (named view with pages)

class IFiveViewDirective(IViewDirective):

    permission = Permission(
        title=u"Permission",
        description=u"The permission needed to use the view.",
        required=False,
        )


class view(zope.browserpage.metaconfigure.view):

    def __call__(self):
        (_context, name, for_, permission, layer, class_,
         allowed_interface, allowed_attributes) = self.args

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
                view = component.queryMultiAdapter((self, request), name=name,
                                                   default=None)
                if view is not None:
                    return view

                m = class_.publishTraverse.__get__(self)
                return m(request, name)

        else:
            def publishTraverse(self, request, name,
                                pages=pages, getattr=getattr):

                if name in pages:
                    return getattr(self, pages[name])
                view = component.queryMultiAdapter((self, request), name=name,
                                                   default=None)
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
            bases = (class_, ViewMixinForTemplates)
        else:
            bases = (ViewMixinForTemplates,)

        try:
            cname = str(name)
        except:
            cname = "GeneratedClass"
            
        cdict['__name__'] = name
        newclass = makeClass(cname, bases, cdict)
        
        _handle_for(_context, for_)

        if self.provides is not None:
            _context.action(
                discriminator = None,
                callable = provideInterface,
                args = ('', self.provides)
                )

        _context.action(
            discriminator = ('view', for_, name, IBrowserRequest, layer,
                             self.provides),
            callable = handler,
            args = ('registerAdapter',
                    newclass, (for_, layer), self.provides, name,
                    _context.info),
            )
        
        # Security
        
        _context.action(
            discriminator = ('five:protectClass', newclass),
            callable = protectClass,
            args = (newclass, permission)
            )
        
        if allowed_attributes:
            for attr in allowed_attributes:
                _context.action(
                    discriminator = ('five:protectName', newclass, attr),
                    callable = protectName,
                    args = (newclass, attr, permission)
                    )
        
        # Make everything else private
        allowed = allowed_attributes or []
        private_attrs = [name for name in dir(newclass)
                         if (not name.startswith('_')) and
                            (name not in allowed) and
                            ismethod(getattr(newclass, name))]
        for attr in private_attrs:
            _context.action(
                discriminator = ('five:protectName', newclass, attr),
                callable = protectName,
                args = (newclass, attr, CheckerPrivateId, False)
                )
        
        # Protect the class
        _context.action(
            discriminator = ('five:initialize:class', newclass),
            callable = InitializeClass,
            args = (newclass,)
            )

_factory_map = {'image':{'prefix':'ImageResource',
                         'count':0,
                         'factory':ImageResourceFactory},
                'file':{'prefix':'FileResource',
                        'count':0,
                        'factory':FileResourceFactory},
                'template':{'prefix':'PageTemplateResource',
                            'count':0,
                            'factory':PageTemplateResourceFactory}
                }

def resource(_context, name, layer=IDefaultBrowserLayer, permission='zope.Public',
             file=None, image=None, template=None):

    if ((file and image) or (file and template) or
        (image and template) or not (file or image or template)):
        raise ConfigurationError(
            "Must use exactly one of file or image or template"
            "attributes for resource directives"
            )

    res = file or image or template
    res_type = ((file and 'file') or
                 (image and 'image') or
                 (template and 'template'))
    factory_info = _factory_map.get(res_type)
    factory_info['count'] += 1
    res_factory = factory_info['factory']
    class_name = '%s%s' % (factory_info['prefix'], factory_info['count'])
    new_class = makeClass(class_name, (res_factory.resource,), {})
    factory = res_factory(name, res, resource_factory=new_class)

    _context.action(
        discriminator = ('resource', name, IBrowserRequest, layer),
        callable = handler,
        args = ('registerAdapter',
                factory, (layer,), Interface, name, _context.info),
        )
    _context.action(
        discriminator = ('five:protectClass', new_class),
        callable = protectClass,
        args = (new_class, permission)
        )
    _context.action(
        discriminator = ('five:initialize:class', new_class),
        callable = InitializeClass,
        args = (new_class,)
        )

_rd_map = {ImageResourceFactory:{'prefix':'DirContainedImageResource',
                                 'count':0},
           FileResourceFactory:{'prefix':'DirContainedFileResource',
                                'count':0},
           PageTemplateResourceFactory:{'prefix':'DirContainedPTResource',
                                        'count':0},
           DirectoryResourceFactory:{'prefix':'DirectoryResource',
                                     'count':0}
           }

def resourceDirectory(_context, name, directory, layer=IDefaultBrowserLayer,
                      permission='zope.Public'):

    if not os.path.isdir(directory):
        raise ConfigurationError(
            "Directory %s does not exist" % directory
            )

    resource = DirectoryResourceFactory.resource
    f_cache = {}
    resource_factories = dict(resource.resource_factories)
    resource_factories['default'] = resource.default_factory
    for ext, factory in resource_factories.items():
        if f_cache.get(factory) is not None:
            continue
        factory_info = _rd_map.get(factory)
        factory_info['count'] += 1
        class_name = '%s%s' % (factory_info['prefix'], factory_info['count'])
        factory_name = '%s%s' % (factory.__name__, factory_info['count'])
        f_resource = makeClass(class_name, (factory.resource,), {})
        f_cache[factory] = makeClass(factory_name, (factory,),
                                     {'resource':f_resource})
    for ext, factory in resource_factories.items():
        resource_factories[ext] = f_cache[factory]
    default_factory = resource_factories['default']
    del resource_factories['default']

    cdict = {'resource_factories':resource_factories,
             'default_factory':default_factory}

    factory_info = _rd_map.get(DirectoryResourceFactory)
    factory_info['count'] += 1
    class_name = '%s%s' % (factory_info['prefix'], factory_info['count'])
    dir_factory = makeClass(class_name, (resource,), cdict)
    factory = DirectoryResourceFactory(name, directory,
                                       resource_factory=dir_factory)

    new_classes = [dir_factory,
                   ] + [f.resource for f in f_cache.values()]

    _context.action(
        discriminator = ('resource', name, IBrowserRequest, layer),
        callable = handler,
        args = ('registerAdapter',
                factory, (layer,), Interface, name, _context.info),
        )
    for new_class in new_classes:
        _context.action(
            discriminator = ('five:protectClass', new_class),
            callable = protectClass,
            args = (new_class, permission)
            )
        _context.action(
            discriminator = ('five:initialize:class', new_class),
            callable = InitializeClass,
            args = (new_class,)
            )

class ViewMixinForAttributes(BrowserView,
                             zope.browserpage.metaconfigure.simple):

    # For some reason, the 'simple' baseclass doesn't implement this
    # mandatory method (see https://bugs.launchpad.net/zope3/+bug/129296)
    def browserDefault(self, request):
        return getattr(self, self.__page_attribute__), ()

    # __call__ should have the same signature as the original method
    @property
    def __call__(self):
        return getattr(self, self.__page_attribute__)

class ViewMixinForTemplates(BrowserView):
    # Cloned from zope.app.pagetemplate.simpleviewclass.simple
    implements(IBrowserPublisher)

    def browserDefault(self, request):
        return self, ()

    def publishTraverse(self, request, name):
        if name == 'index.html':
            return self.index

        raise NotFound(self, name, request)

    def __getitem__(self, name):
        if name == 'macros':
            return self.index.macros
        return self.index.macros[name]

    def __call__(self, *args, **kw):
        return self.index(*args, **kw)

def makeClassForTemplate(filename, globals=None, used_for=None,
                         bases=(), cdict=None, name=u''):
    # XXX needs to deal with security from the bases?
    if cdict is None:
        cdict = {}
    cdict.update({'index': ViewPageTemplateFile(filename, globals),
                  '__name__': name})
    bases += (ViewMixinForTemplates,)
    class_ = makeClass("SimpleViewClass from %s" % filename, bases, cdict)

    if used_for is not None:
        class_.__used_for__ = used_for

    return class_

