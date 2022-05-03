##############################################################################
#
# Copyright (c) 2002-2005 Zope Foundation and Contributors.
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

(original: zope.app.container.browser.adding)
"""

import operator

from OFS.SimpleItem import SimpleItem
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import BadRequest
from zope.browser.interfaces import IAdding
from zope.browsermenu.menu import getMenu
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.component.interfaces import IFactory
from zope.container.constraints import checkFactory
from zope.container.constraints import checkObject
from zope.container.i18n import ZopeMessageFactory as _
from zope.container.interfaces import IContainerNamesContainer
from zope.container.interfaces import INameChooser
from zope.event import notify
from zope.exceptions.interfaces import UserError
from zope.interface import implementer
from zope.lifecycleevent import ObjectCreatedEvent
from zope.publisher.interfaces import IPublishTraverse
from zope.traversing.browser.absoluteurl import absoluteURL


@implementer(IAdding, IPublishTraverse)
class Adding(BrowserView):

    def add(self, content):
        """See zope.browser.interfaces.IAdding
        """
        container = self.context
        name = self.contentName
        chooser = INameChooser(container)

        # check precondition
        checkObject(container, name, content)

        if IContainerNamesContainer.providedBy(container):
            # The container picks its own names.
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
                name = chooser.chooseName(name, content)

        content.id = name
        container._setObject(name, content)
        self.contentName = name  # Set the added object Name
        return container._getOb(name)

    contentName = None  # usually set by Adding traverser

    def nextURL(self):
        """See zope.browser.interfaces.IAdding"""
        # XXX this is definitely not right for all or even most uses
        # of Five, but can be overridden by an AddView subclass
        return absoluteURL(self.context, self.request) + '/manage_main'

    # set in BrowserView.__init__
    request = None
    context = None

    def publishTraverse(self, request, name):
        """See zope.publisher.interfaces.IPublishTraverse"""
        if '=' in name:
            view_name, content_name = name.split("=", 1)
            self.contentName = content_name

            if view_name.startswith('@@'):
                view_name = view_name[2:]
            return getMultiAdapter((self, request), name=view_name)

        if name.startswith('@@'):
            view_name = name[2:]
        else:
            view_name = name

        view = queryMultiAdapter((self, request), name=view_name)
        if view is not None:
            return view

        factory = queryUtility(IFactory, name)
        if factory is None:
            return super().publishTraverse(request, name)

        return factory

    def action(self, type_name='', id=''):
        if not type_name:
            raise UserError(_("You must select the type of object to add."))

        if type_name.startswith('@@'):
            type_name = type_name[2:]

        if '/' in type_name:
            view_name = type_name.split('/', 1)[0]
        else:
            view_name = type_name

        if queryMultiAdapter((self, self.request),
                             name=view_name) is not None:
            url = f"{absoluteURL(self, self.request)}/{type_name}={id}"
            self.request.response.redirect(url)
            return

        if not self.contentName:
            self.contentName = id

        factory = getUtility(IFactory, type_name)
        content = factory()

        notify(ObjectCreatedEvent(content))

        self.add(content)
        self.request.response.redirect(self.nextURL())

    def nameAllowed(self):
        """Return whether names can be input by the user."""
        return not IContainerNamesContainer.providedBy(self.context)

    menu_id = None
    index = ViewPageTemplateFile("adding.pt")

    def addingInfo(self):
        """Return menu data.

        This is sorted by title.
        """
        container = self.context
        result = []
        for menu_id in (self.menu_id, 'zope.app.container.add'):
            if not menu_id:
                continue
            for item in getMenu(menu_id, self, self.request):
                extra = item.get('extra')
                if extra:
                    factory = extra.get('factory')
                    if factory:
                        factory = getUtility(IFactory, factory)
                        if not checkFactory(container, None, factory):
                            continue
                        elif item['extra']['factory'] != item['action']:
                            item['has_custom_add_view'] = True
                result.append(item)

        result.sort(key=operator.itemgetter('title'))
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


class ContentAdding(Adding, SimpleItem):

    menu_id = "add_content"


@implementer(INameChooser)
class ObjectManagerNameChooser:
    """A name chooser for a Zope object manager.
    """

    def __init__(self, context):
        self.context = context

    def checkName(self, name, object):
        try:
            self.context._checkId(name, allow_dup=False)
        except BadRequest as e:
            msg = ' '.join(e.args) or "Id is in use or invalid"
            raise UserError(msg)

    def chooseName(self, name, object):
        if not name:
            name = object.__class__.__name__

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
            except (AttributeError, KeyError):
                break
            n = name + '-' + str(i) + suffix

        # Make sure the name is valid.  We may have started with
        # something bad.
        self.checkName(n, object)

        return n
