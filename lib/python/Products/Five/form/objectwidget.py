##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Five-compatible version of ObjectWidget

This is needed because ObjectWidget uses ViewPageTemplateFile whose
macro definition is unfortunately incompatible with ZopeTwoPageTemplateFile.
So this subclass uses ZopeTwoPageTemplateFile for the template that renders
the widget's sub-editform.

$Id$
"""
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.app.form.browser.objectwidget import ObjectWidget as OWBase
from zope.app.form.browser.objectwidget import ObjectWidgetView as OWVBase

class ObjectWidgetView(OWVBase):
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    template = ViewPageTemplateFile('objectwidget.pt')

InitializeClass(ObjectWidgetView)

class ObjectWidgetClass(OWBase):

    def setRenderedValue(self, value):
        """Slightly more robust re-implementation this method."""
        # re-call setupwidgets with the content
        self._setUpEditWidgets()
        for name in self.names:
            val = getattr(value, name, None)
            if val is None:
                # this is where we are more robust than Zope 3.2's
                # object widget: we supply subwidgets with the default
                # from the schema, not None (Zope 3.2's list widget
                # breaks when the rendered value is None)
                val = self.context.schema[name].default
            self.getSubWidget(name).setRenderedValue(val)

ObjectWidget = ObjectWidgetClass
