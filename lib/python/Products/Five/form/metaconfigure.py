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
"""Edit form directives

$Id$
"""
import ExtensionClass
from Globals import InitializeClass as initializeClass

import zope.component
from zope.interface import Interface
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('zope')

from zope.app.publisher.browser.menumeta import menuItemDirective
from zope.app.form.browser.metaconfigure import BaseFormDirective
from zope.app.container.interfaces import IAdding

from Products.Five.form import EditView, AddView
from Products.Five.metaclass import makeClass
from Products.Five.security import protectClass
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.browser.metaconfigure import makeClassForTemplate

def EditViewFactory(name, schema, label, permission, layer,
                    template, default_template, bases, for_, fields,
                    fulledit_path=None, fulledit_label=None, menu=u''):
    class_ = makeClassForTemplate(template, globals(), used_for=schema,
                                  bases=bases)
    class_.schema = schema
    class_.label = label
    class_.fieldNames = fields

    class_.fulledit_path = fulledit_path
    if fulledit_path and (fulledit_label is None):
        fulledit_label = "Full edit"

    class_.fulledit_label = fulledit_label

    class_.generated_form = ZopeTwoPageTemplateFile(default_template)

    if layer is None:
        layer = IDefaultBrowserLayer

    s = zope.component.getGlobalSiteManager()
    s.registerAdapter(class_, (for_, layer), Interface, name)

    # Reminder: the permission we got has already been processed by
    # BaseFormDirective, that means that zope.Public has been
    # translated to the CheckerPublic object
    protectClass(class_, permission)
    initializeClass(class_)

class FiveFormDirective(BaseFormDirective):

    def _processWidgets(self):
        if self._widgets:
            customWidgetsObject = makeClass(
                'CustomWidgetsMixin', (ExtensionClass.Base,), self._widgets)
            self.bases = self.bases + (customWidgetsObject,)

class EditFormDirective(FiveFormDirective):

    view = EditView
    default_template = 'edit.pt'
    title = _('Edit')

    def _handle_menu(self):
        if self.menu:
            menuItemDirective(
                self._context, self.menu, self.for_ or self.schema,
                '@@' + self.name, self.title, permission=self.permission,
                layer=self.layer)

    def __call__(self):
        self._processWidgets()
        self._handle_menu()
        self._context.action(
            discriminator=self._discriminator(),
            callable=EditViewFactory,
            args=self._args(),
            kw={'menu': self.menu},
        )


def AddViewFactory(name, schema, label, permission, layer,
                   template, default_template, bases, for_,
                   fields, content_factory, arguments,
                   keyword_arguments, set_before_add, set_after_add,
                   menu=u''):
    class_ = makeClassForTemplate(template, globals(), used_for=schema,
                                  bases=bases)

    class_.schema = schema
    class_.label = label
    class_.fieldNames = fields
    class_._factory = content_factory
    class_._arguments = arguments
    class_._keyword_arguments = keyword_arguments
    class_._set_before_add = set_before_add
    class_._set_after_add = set_after_add

    class_.generated_form = ZopeTwoPageTemplateFile(default_template)

    if layer is None:
        layer = IDefaultBrowserLayer

    s = zope.component.getGlobalSiteManager()
    s.registerAdapter(class_, (for_, layer), Interface, name)

    # Reminder: the permission we got has already been processed by
    # BaseFormDirective, that means that zope.Public has been
    # translated to the CheckerPublic object
    protectClass(class_, permission)
    initializeClass(class_)

class AddFormDirective(FiveFormDirective):

    view = AddView
    default_template = 'add.pt'
    for_ = IAdding

    # default add form information
    description = None
    content_factory = None
    arguments = None
    keyword_arguments = None
    set_before_add = None
    set_after_add = None

    def _handle_menu(self):
        if self.menu or self.title:
            if (not self.menu) or (not self.title):
                raise ValueError("If either menu or title are specified, "
                                 "they must both be specified")
            # Add forms are really for IAdding components, so do not use
            # for=self.schema.
            menuItemDirective(
                self._context, self.menu, self.for_, '@@' + self.name,
                self.title, permission=self.permission, layer=self.layer,
                description=self.description)

    def _handle_arguments(self, leftover=None):
        schema = self.schema
        fields = self.fields
        arguments = self.arguments
        keyword_arguments = self.keyword_arguments
        set_before_add = self.set_before_add
        set_after_add = self.set_after_add

        if leftover is None:
            leftover = fields

        if arguments:
            missing = [n for n in arguments if n not in fields]
            if missing:
                raise ValueError("Some arguments are not included in the form",
                                 missing)
            optional = [n for n in arguments if not schema[n].required]
            if optional:
                raise ValueError("Some arguments are optional, use"
                                 " keyword_arguments for them",
                                 optional)
            leftover = [n for n in leftover if n not in arguments]

        if keyword_arguments:
            missing = [n for n in keyword_arguments if n not in fields]
            if missing:
                raise ValueError(
                    "Some keyword_arguments are not included in the form",
                    missing)
            leftover = [n for n in leftover if n not in keyword_arguments]

        if set_before_add:
            missing = [n for n in set_before_add if n not in fields]
            if missing:
                raise ValueError(
                    "Some set_before_add are not included in the form",
                    missing)
            leftover = [n for n in leftover if n not in set_before_add]

        if set_after_add:
            missing = [n for n in set_after_add if n not in fields]
            if missing:
                raise ValueError(
                    "Some set_after_add are not included in the form",
                    missing)
            leftover = [n for n in leftover if n not in set_after_add]

            self.set_after_add += leftover

        else:
            self.set_after_add = leftover

    def __call__(self):
        self._processWidgets()
        self._handle_menu()
        self._handle_arguments()

        self._context.action(
            discriminator=self._discriminator(),
            callable=AddViewFactory,
            args=self._args()+(self.content_factory, self.arguments,
                                 self.keyword_arguments,
                                 self.set_before_add, self.set_after_add),
            kw={'menu': self.menu},
            )
