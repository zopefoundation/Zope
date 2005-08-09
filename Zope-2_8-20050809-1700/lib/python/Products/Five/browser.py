##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Provide basic browser functionality

$Id: browser.py 12915 2005-05-31 10:23:19Z philikon $
"""
# python
import sys
from datetime import datetime

import transaction

# Zope 2
import Acquisition
from  Acquisition import aq_inner, aq_parent, aq_base
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

# Zope 3
from interfaces import ITraversable
from zope.interface import implements
from zope.component import getViewProviding
from zope.app.traversing.browser.interfaces import IAbsoluteURL
from zope.publisher.browser import isCGI_NAME
from zope.i18n.interfaces import IUserPreferredCharsets

from zope.app.location.interfaces import ILocation
from zope.app.location import LocationProxy
from zope.app.form.utility import setUpEditWidgets, applyWidgetsChanges
from zope.app.form.browser.submit import Update
from zope.app.form.interfaces import WidgetsError, MissingInputError
from zope.event import notify
from zope.app.form.utility import setUpWidgets, getWidgetsData
from zope.app.form.interfaces import IInputWidget, WidgetsError
from zope.schema.interfaces import ValidationError
from zope.app.event.objectevent import ObjectCreatedEvent, ObjectModifiedEvent

# Five
from Products.Five.pagetemplatefile import FivePageTemplateFile

class BrowserView(Acquisition.Explicit):
    security = ClassSecurityInfo()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    # XXX do not create any methods on the subclass called index_html,
    # as this makes Zope 2 traverse into that first!

InitializeClass(BrowserView)

class AbsoluteURL(BrowserView):
    """An adapter for Zope3-style absolute_url using Zope2 methods

    (original: zope.app.traversing.browser.absoluteurl)
    """

    def __init__(self, context, request):
        self.context, self.request = context, request

    implements(IAbsoluteURL)

    def __str__(self):
        context = aq_inner(self.context)
        return context.absolute_url()

    __call__ = __str__

    def breadcrumbs(self):
        context = self.context.aq_inner
        container = context.aq_parent
        request = self.request

        name = context.getId()
        
        if container is None or self._isVirtualHostRoot() \
            or not ITraversable.providedBy(container):
            return (
                {'name': name, 'url': context.absolute_url()},)

        view = getViewProviding(container, IAbsoluteURL, request)
        base = tuple(view.breadcrumbs())
        base += (
            {'name': name, 'url': ("%s/%s" % (base[-1]['url'], name))},)

        return base

    def _isVirtualHostRoot(self):
        virtualrootpath = self.request.get('VirtualRootPhysicalPath', None)
        if virtualrootpath is None:
            return False
        context = self.context.aq_inner
        return context.restrictedTraverse(virtualrootpath) == context

class SiteAbsoluteURL(AbsoluteURL):
    """An adapter for Zope3-style absolute_url using Zope2 methods

    This one is just used to stop breadcrumbs from crumbing up
    to the Zope root.

    (original: zope.app.traversing.browser.absoluteurl)
    """

    def breadcrumbs(self):
        context = self.context
        request = self.request

        return ({'name': context.getId(),
                 'url': context.absolute_url()
                 },)

class EditView(BrowserView):
    """Simple edit-view base class

    Subclasses should provide a schema attribute defining the schema
    to be edited.
    """

    errors = ()
    update_status = None
    label = ''
    charsets = None

    # Fall-back field names computes from schema
    fieldNames = property(lambda self: getFieldNamesInOrder(self.schema))
    # Fall-back template
    generated_form = FivePageTemplateFile('edit.pt')

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self._processInputs()
        self._setPageEncoding()
        self._setUpWidgets()

    def _setUpWidgets(self):
        adapted = self.schema(self.context)
        if adapted is not self.context:
            if not ILocation.providedBy(adapted):
                adapted = LocationProxy(adapted)
            adapted.__parent__ = self.context
        self.adapted = adapted
        setUpEditWidgets(self, self.schema, source=self.adapted,
                         names=self.fieldNames)

    # taken from zope.publisher.browser.BrowserRequest
    def _decode(self, text):
        """Try to decode the text using one of the available charsets."""
        if self.charsets is None:
            envadapter = IUserPreferredCharsets(self.request)
            self.charsets = envadapter.getPreferredCharsets() or ['utf-8']
        for charset in self.charsets:
            try:
                text = unicode(text, charset)
                break
            except UnicodeError:
                pass
        return text

    def _processInputs(self):
        request = self.request
        for name, value in request.form.items():
            if (not (isCGI_NAME(name) or name.startswith('HTTP_'))
                and isinstance(value, str)):
                request.form[name] = self._decode(value)

    def _setPageEncoding(self):
        """Set the encoding of the form page via the Content-Type header.
        ZPublisher uses the value of this header to determine how to
        encode unicode data for the browser."""
        envadapter = IUserPreferredCharsets(self.request)
        charsets = envadapter.getPreferredCharsets() or ['utf-8']
        self.request.RESPONSE.setHeader(
            'Content-Type', 'text/html; charset=%s' % charsets[0])

    def setPrefix(self, prefix):
        for widget in self.widgets():
            widget.setPrefix(prefix)

    def widgets(self):
        return [getattr(self, name+'_widget')
                for name in self.fieldNames]

    def changed(self):
        # This method is overridden to execute logic *after* changes
        # have been made.
        pass

    def update(self):
        if self.update_status is not None:
            # We've been called before. Just return the status we previously
            # computed.
            return self.update_status

        status = ''

        content = self.adapted

        if Update in self.request.form.keys():
            changed = False
            try:
                changed = applyWidgetsChanges(self, self.schema,
                    target=content, names=self.fieldNames)
                # We should not generate events when an adapter is used.
                # That's the adapter's job.
                if changed and self.context is self.adapted:
                    notify(ObjectModifiedEvent(content))
            except WidgetsError, errors:
                self.errors = errors
                status = "An error occured."
                transaction.abort()
            else:
                setUpEditWidgets(self, self.schema, source=self.adapted,
                                 ignoreStickyValues=True,
                                 names=self.fieldNames)
                if changed:
                    self.changed()
                    # XXX: Needs i18n support:
                    # formatter = self.request.locale.dates.getFormatter(
                    #     'dateTime', 'medium')
                    # status = _("Updated on ${date_time}")
                    # status.mapping = {'date_time': formatter.format(
                    #     datetime.utcnow())}
                    status = "Updated on %s" % str(datetime.utcnow())

        self.update_status = status
        return status

class AddView(EditView):
    """Simple edit-view base class.

    Subclasses should provide a schema attribute defining the schema
    to be edited.
    """

    def _setUpWidgets(self):
        setUpWidgets(self, self.schema, IInputWidget, names=self.fieldNames)

    def update(self):
        if self.update_status is not None:
            # We've been called before. Just return the previous result.
            return self.update_status

        if self.request.form.has_key(Update):

            self.update_status = ''
            try:
                data = getWidgetsData(self, self.schema, names=self.fieldNames)
                self.createAndAdd(data)
            except WidgetsError, errors:
                self.errors = errors
                self.update_status = "An error occured."
                return self.update_status

            self.request.response.redirect(self.nextURL())

        return self.update_status

    def create(self, *args, **kw):
        """Do the actual instantiation."""
        # hack to please typical Zope 2 factories, which expect id and title
        args = ('tmp_id', 'Temporary title') + args
        return self._factory(*args, **kw)

    def createAndAdd(self, data):
        """Add the desired object using the data in the data argument.

        The data argument is a dictionary with the data entered in the form.
        """

        args = []
        if self._arguments:
            for name in self._arguments:
                args.append(data[name])

        kw = {}
        if self._keyword_arguments:
            for name in self._keyword_arguments:
                if name in data:
                    kw[str(name)] = data[name]

        content = self.create(*args, **kw)
        adapted = self.schema(content)

        errors = []

        if self._set_before_add:
            for name in self._set_before_add:
                if name in data:
                    field = self.schema[name]
                    try:
                        field.set(adapted, data[name])
                    except ValidationError:
                        errors.append(sys.exc_info()[1])

        if errors:
            raise WidgetsError(*errors)

        notify(ObjectCreatedEvent(content))

        content = self.add(content)

        adapted = self.schema(content)

        if self._set_after_add:
            for name in self._set_after_add:
                if name in data:
                    field = self.schema[name]
                    try:
                        field.set(adapted, data[name])
                    except ValidationError:
                        errors.append(sys.exc_info()[1])

        if errors:
            raise WidgetsError(*errors)

        return content

    def add(self, content):
        return self.context.add(content)

    def nextURL(self):
        return self.context.nextURL()
