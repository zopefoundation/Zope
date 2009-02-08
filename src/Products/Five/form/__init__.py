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
"""Add and edit views

$Id$
"""
import sys
from datetime import datetime

import transaction
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.lifecycleevent import Attributes
from zope.location.interfaces import ILocation
from zope.location import LocationProxy
from zope.schema.interfaces import ValidationError
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('zope')

from zope.app.form.browser.submit import Update
from zope.app.form.interfaces import IInputWidget
from zope.app.form.interfaces import WidgetsError
from zope.app.form.utility import setUpEditWidgets, applyWidgetsChanges
from zope.app.form.utility import setUpWidgets, getWidgetsData

from Products.Five.browser import BrowserView
from Products.Five.browser.decode import processInputs, setPageEncoding
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

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
    generated_form = ZopeTwoPageTemplateFile('edit.pt')

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        processInputs(self.request, self.charsets)
        setPageEncoding(self.request)
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
                # That's the adapter's job.  We need to unwrap the objects to
                # compare them, as they are wrapped differently.
                # Additionally, we can't use Acquisition.aq_base() because
                # it strangely returns different objects for these two even
                # when they are identical.  In particular
                # aq_base(self.adapted) != self.adapted.aq_base :-(
                if changed and getattr(self.context, 'aq_base', self.context)\
                            is getattr(self.adapted, 'aq_base', self.adapted):
                    description = Attributes(self.schema, *self.fieldNames)
                    notify(ObjectModifiedEvent(content, description))
            except WidgetsError, errors:
                self.errors = errors
                status = _("An error occurred.")
                transaction.abort()
            else:
                setUpEditWidgets(self, self.schema, source=self.adapted,
                                 ignoreStickyValues=True,
                                 names=self.fieldNames)
                if changed:
                    self.changed()
                    formatter = self.request.locale.dates.getFormatter(
                       'dateTime', 'medium')
                    status = _("Updated on ${date_time}",
                              mapping={'date_time':
                                       formatter.format(datetime.utcnow())})

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
                self.update_status = _("An error occurred.")
                return self.update_status

            self.request.response.redirect(self.nextURL())

        return self.update_status

    def create(self, *args, **kw):
        """Do the actual instantiation."""
        # hack to please typical Zope 2 factories, which expect id and title
        # Any sane schema will use a unicode title, and may fail on a
        # non-unicode one.
        args = ('tmp_id', u'Temporary title') + args
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
            # We have modified the object, so we need to publish an
            # object-modified event:
            description = Attributes(self.schema, *self._set_after_add)
            notify(ObjectModifiedEvent(content, description))

        if errors:
            raise WidgetsError(*errors)

        return content

    def add(self, content):
        return self.context.add(content)

    def nextURL(self):
        return self.context.nextURL()
