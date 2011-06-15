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

from logging import getLogger
import os
import re
import stat

from AccessControl.Permission import registerPermissions
from AccessControl.PermissionRole import PermissionRole
from App.Common import package_home
from App.ImageFile import ImageFile
from DateTime.DateTime import DateTime
from HelpSys import APIHelpTopic
from HelpSys import HelpTopic
from OFS.misc_ import Misc_
from OFS.misc_ import misc_
from OFS.ObjectManager import ObjectManager

from zope.interface import implementedBy

from App.FactoryDispatcher import FactoryDispatcher

# Waaaa
import Products
if not hasattr(Products, 'meta_types'):
    Products.meta_types=()
if not hasattr(Products, 'meta_classes'):
    Products.meta_classes={}
    Products.meta_class_info={}

_marker = []  # Create a new marker object
LOG = getLogger('ProductContext')

class ProductContext:

    def __init__(self, product, app, package):
        self.__prod = product
        # app is None by default which signals disabled product installation
        self.__app = app
        self.__pack = package

    def registerClass(self, instance_class=None, meta_type='',
                      permission=None, constructors=(),
                      icon=None, permissions=None, legacy=(),
                      visibility="Global", interfaces=_marker,
                      container_filter=None
        ):
        """Register a constructor

        Keyword arguments are used to provide meta data:

        instance_class -- The class of the object that will be created.

          This is not currently used, but may be used in the future to
          increase object mobility.

        meta_type -- The kind of object being created
           This appears in add lists.  If not specified, then the class
           meta_type will be used.

        permission -- The permission name for the constructors.
           If not specified, then a permission name based on the
           meta type will be used.

        constructors -- A list of constructor methods
          A method can me a callable object with a __name__
          attribute giving the name the method should have in the
          product, or the method may be a tuple consisting of a
          name and a callable object.  The method must be picklable.

          The first method will be used as the initial method called
          when creating an object.

        icon -- The name of an image file in the package to
                be used for instances. Note that the class icon
                attribute will be set automagically if an icon is
                provided.

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

        """
        pack=self.__pack
        initial=constructors[0]
        productObject=self.__prod
        pid=productObject.id

        if icon and instance_class is not None:
            setattr(instance_class, 'icon', 'misc_/%s/%s' %
                    (pid, os.path.split(icon)[1]))

        if permissions:
            if isinstance(permissions, basestring): # You goofed it!
                raise TypeError, ('Product context permissions should be a '
                    'list of permissions not a string', permissions)
            for p in permissions:
                if isinstance(p, tuple):
                    p, default= p
                    registerPermissions(((p, (), default),))
                else:
                    registerPermissions(((p, ()),))

        ############################################################
        # Constructor permission setup
        if permission is None:
            permission="Add %ss" % (meta_type or instance_class.meta_type)

        if isinstance(permission, tuple):
            permission, default = permission
        else:
            default = ('Manager',)

        pr = PermissionRole(permission,default)
        registerPermissions(((permission, (), default),))
        ############################################################

        OM = ObjectManager

        for method in legacy:
            if isinstance(method, tuple):
                name, method = method
                aliased = 1
            else:
                name=method.__name__
                aliased = 0
            if name not in OM.__dict__:
                setattr(OM, name, method)
                setattr(OM, name+'__roles__', pr)
                if aliased:
                    # Set the unaliased method name and its roles
                    # to avoid security holes.  XXX: All "legacy"
                    # methods need to be eliminated.
                    setattr(OM, method.__name__, method)
                    setattr(OM, method.__name__+'__roles__', pr)

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

        Products.meta_types = Products.meta_types + (
            { 'name': meta_type or instance_class.meta_type,
              # 'action': The action in the add drop down in the ZMI. This is
              #           currently also required by the _verifyObjectPaste
              #           method of CopyContainers like Folders.
              'action': ('manage_addProduct/%s/%s' % (pid, name)),
              # 'product': Used by ProductRegistry for TTW products and by
              #            OFS.Application for refreshing products.
              #            This key might not be available.
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

        m[name]=initial
        m[name+'__roles__']=pr

        for method in constructors[1:]:
            if isinstance(method, tuple):
                name, method = method
            else:
                name=os.path.split(method.__name__)[-1]
            if name not in productObject.__dict__:
                m[name]=method
                m[name+'__roles__']=pr

        if icon:
            name = os.path.split(icon)[1]
            icon = ImageFile(icon, self.__pack.__dict__)
            icon.__roles__=None
            if not hasattr(misc_, pid):
                setattr(misc_, pid, Misc_(pid, {}))
            getattr(misc_, pid)[name]=icon

    def getProductHelp(self):
        """
        Returns the ProductHelp associated with the current Product.
        """
        if self.__app is None:
            return self.__prod.getProductHelp()
        return self.__prod.__of__(self.__app.Control_Panel.Products).getProductHelp()

    def registerHelpTopic(self, id, topic):
        """
        Register a Help Topic for a product.
        """
        self.getProductHelp()._setObject(id, topic)

    def registerHelpTitle(self, title):
        """
        Sets the title of the Product's Product Help
        """
        h = self.getProductHelp()
        if getattr(h, 'title', None) != title:
            h.title = title

    def registerHelp(self, directory='help', clear=1,
            title_re=re.compile(r'<title>(.+?)</title>', re.I)):
        """
        Registers Help Topics for all objects in a directory.

        Nothing will be done if the files in the directory haven't
        changed since the last registerHelp call.

        'clear' indicates whether or not to delete all existing
        Topics from the Product.

        HelpTopics are created for these kind of files

        .dtml            -- DTMLHelpTopic
        .html .htm       -- TextHelpTopic
        .stx .txt        -- STXHelpTopic
        .jpg .png .gif   -- ImageHelpTopic
        .py              -- APIHelpTopic
        """

        if not self.__app:
            return

        help=self.getProductHelp()
        path=os.path.join(package_home(self.__pack.__dict__),
                          directory)

        # If help directory does not exist, log a warning and return.
        try:
            dir_mod_time=DateTime(os.stat(path)[stat.ST_MTIME])
        except OSError, (errno, text):
            LOG.warn('%s: %s' % (text, path))
            return

        # test to see if nothing has changed since last registration
        if help.lastRegistered is not None and \
                help.lastRegistered >= dir_mod_time:
            return
        help.lastRegistered=DateTime()

        if clear:
            for id in help.objectIds(['Help Topic','Help Image']):
                help._delObject(id)

        for file in os.listdir(path):
            ext=os.path.splitext(file)[1]
            ext=ext.lower()
            if ext in ('.dtml',):
                contents = open(os.path.join(path,file),'rb').read()
                m = title_re.search(contents)
                if m:
                    title = m.group(1)
                else:
                    title = ''
                ht=HelpTopic.DTMLTopic(file, '', os.path.join(path,file))
                self.registerHelpTopic(file, ht)
            elif ext in ('.html', '.htm'):
                contents = open(os.path.join(path,file),'rb').read()
                m = title_re.search(contents)
                if m:
                    title = m.group(1)
                else:
                    title = ''
                ht=HelpTopic.TextTopic(file, title, os.path.join(path,file))
                self.registerHelpTopic(file, ht)
            elif ext in ('.stx', '.txt'):
                title=(open(os.path.join(path,file),'rb').readline()).split(':')[0]
                ht=HelpTopic.STXTopic(file, title, os.path.join(path, file))
                self.registerHelpTopic(file, ht)
            elif ext in ('.jpg', '.gif', '.png'):
                ht=HelpTopic.ImageTopic(file, '', os.path.join(path, file))
                self.registerHelpTopic(file, ht)
            elif ext in ('.py',):
                if file[0] == '_': # ignore __init__.py
                    continue
                ht=APIHelpTopic.APIHelpTopic(file, '', os.path.join(path, file))
                self.registerHelpTopic(file, ht)


class AttrDict:

    def __init__(self, ob):
        self.ob = ob

    def __setitem__(self, name, v):
        setattr(self.ob, name, v)
