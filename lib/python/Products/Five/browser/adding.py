##############################################################################
#
# Copyright (c) 2002-2005 Zope Corporation and Contributors.
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
"""Adding View

The Adding View is used to add new objects to a container. It is sort of a
factory screen.
"""
__docformat__ = 'restructuredtext'

from warnings import warn
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.component.interfaces import IFactory

from zope.app.exception.interfaces import UserError
from zope.app.container.interfaces import IAdding, INameChooser
from zope.app.container.interfaces import IContainerNamesContainer
from zope.app.container.constraints import checkFactory, checkObject

from zope.app import zapi
from zope.app.event.objectevent import ObjectCreatedEvent
from zope.event import notify

from zExceptions import BadRequest

from Products.Five import BrowserView
from Products.Five.traversable import Traversable
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from Acquisition import Implicit
from OFS.SimpleItem import SimpleItem

class BasicAdding(Implicit, BrowserView):
    implements(IAdding, IPublishTraverse)

    def add(self, content):
        """See zope.app.container.interfaces.IAdding
        """
        container = self.context
        name = self.contentName
        chooser = INameChooser(container)

        # check precondition
        checkObject(container, name, content)

        if IContainerNamesContainer.providedBy(container):
            # The container picks it's own names.
            # We need to ask it to pick one.
            name = chooser.chooseName(self.contentName or '', content)
        else:
            request = self.request
            name = request.get('add_input_name', name)

            if name is None:
                name = chooser.chooseName(self.contentName or '', content)
            elif name == '':
                name = chooser.chooseName('', content)
            else:
                # Invoke the name chooser even when we have a
                # name. It'll do useful things with it like converting
                # the incoming unicode to an ASCII string.
                name = chooser.chooseName(name, container)
        
        content.id = name
        container._setObject(name, content)
        self.contentName = name # Set the added object Name
        return container._getOb(name)

    contentName = None # usually set by Adding traverser

    def nextURL(self):
        """See zope.app.container.interfaces.IAdding"""
        # XXX this is definitely not right for all or even most uses
        # of Five, but can be overridden by an AddView subclass, using
        # the class attribute of a zcml:addform directive
        return (str(zapi.getView(self.context, "absolute_url", self.request))
                + '/manage_main')

    # set in BrowserView.__init__
    request = None 
    context = None

    def renderAddButton(self):
        warn("The renderAddButton method is deprecated, use nameAllowed",
            DeprecationWarning, 2)
    

    def publishTraverse(self, request, name):
        """See zope.app.container.interfaces.IAdding"""
        if '=' in name:
            view_name, content_name = name.split("=", 1)
            self.contentName = content_name

            if view_name.startswith('@@'):
                view_name = view_name[2:]
            return zapi.getView(self, view_name, request)

        if name.startswith('@@'):
            view_name = name[2:]
        else:
            view_name = name

        view = zapi.queryView(self, view_name, request)
        if view is not None:
            return view

        factory = zapi.queryUtility(IFactory, name)
        if factory is None:
            return super(BasicAdding, self).publishTraverse(request, name)

        return factory

    def action(self, type_name='', id=''):
        if not type_name:
            raise UserError("You must select the type of object to add.")

        if type_name.startswith('@@'):
            type_name = type_name[2:]

        if '/' in type_name:
            view_name  = type_name.split('/', 1)[0]
        else:
            view_name = type_name

        if zapi.queryView(self, view_name, self.request) is not None:
            url = "%s/%s=%s" % (
                zapi.getView(self, "absolute_url", self.request),
                type_name, id)
            self.request.response.redirect(url)
            return

        if not self.contentName:
            self.contentName = id

        factory = zapi.getUtility(IFactory, type_name)
        content = factory()

        notify(ObjectCreatedEvent(content))
        self.add(content)
        self.request.response.redirect(self.nextURL())

    def namesAccepted(self):
        return not IContainerNamesContainer.providedBy(self.context)

    def nameAllowed(self):
        """Return whether names can be input by the user."""
        return not IContainerNamesContainer.providedBy(self.context)
    

class Adding(BasicAdding):

    menu_id = None
    index = ZopeTwoPageTemplateFile("adding.pt")

    def addingInfo(self):
        """Return menu data.

        This is sorted by title.
        """
        container = self.context
        menu_service = zapi.getService("BrowserMenu")
        result = []
        for menu_id in (self.menu_id, 'zope.app.container.add'):
            if not menu_id:
                continue
            for item in menu_service.getMenu(menu_id, self, self.request):
                extra = item.get('extra')
                if extra:
                    factory = extra.get('factory')
                    if factory:
                        factory = zapi.getUtility(IFactory, factory)
                        if not checkFactory(container, None, factory):
                            continue
                        elif item['extra']['factory'] != item['action']:
                            item['has_custom_add_view']=True
                result.append(item)

        result.sort(lambda a, b: cmp(a['title'], b['title']))
        return result

    def isSingleMenuItem(self):
        "Return whether there is single menu item or not."
        return len(self.addingInfo()) == 1

    def hasCustomAddView(self):
       "This should be called only if there is `singleMenuItem` else return 0"
       if self.isSingleMenuItem():
           menu_item = self.addingInfo()[0]
           if 'has_custom_add_view' in menu_item:
               return True
       return False

class ContentAdding(Adding, Traversable, SimpleItem):

    menu_id = "add_content"

class ObjectManagerNameChooser:
    """A name chooser for a Zope object manager.
    """
    
    implements(INameChooser)
    
    def __init__(self, context):
        self.context = context

    def checkName(self, name, object):
        # ObjectManager can only deal with ASCII names. Specially
        # ObjectManager._checkId can only deal with strings.
        try:
            name = name.encode('ascii')
        except UnicodeDecodeError:
            raise UserError, "Id must contain only ASCII characters."

        try:
            self.context._checkId(name, allow_dup=False)
        except BadRequest, e:
            msg = ' '.join(e.args) or "Id is in use or invalid"
            raise UserError, msg

    def chooseName(self, name, object):
        if not name:
            name = object.__class__.__name__
        else:
            try:
                name = name.encode('ascii')
            except UnicodeDecodeError:
                raise UserError, "Id must contain only ASCII characters."

        dot = name.rfind('.')
        if dot >= 0:
            suffix = name[dot:]
            name = name[:dot]
        else:
            suffix = ''

        n = name + suffix
        i = 0
        while True:
            i += 1
            try:
                self.context._getOb(n)
            except AttributeError:
                break
            n = name + '-' + str(i) + suffix
            
        # Make sure the name is valid.  We may have started with
        # something bad.
        self.checkName(n, object)

        return n
