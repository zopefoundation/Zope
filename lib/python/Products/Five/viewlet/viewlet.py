##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Viewlet.

$Id$
"""
import os
from Acquisition import Explicit
from zope.viewlet import viewlet as orig_viewlet

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

# We add Acquisition to all the base classes to enable security machinery
class ViewletBase(orig_viewlet.ViewletBase, Explicit):
    pass

class SimpleAttributeViewlet(orig_viewlet.SimpleAttributeViewlet, Explicit):
    pass

class simple(orig_viewlet.simple):
    # We need to ensure that the proper __init__ is called.
    __init__ = ViewletBase.__init__.im_func

def SimpleViewletClass(template, bases=(), attributes=None,
                       name=u''):
    """A function that can be used to generate a viewlet from a set of
    information.
    """

    # Create the base class hierarchy
    bases += (simple, ViewletBase)

    attrs = {'index' : ZopeTwoPageTemplateFile(template),
             '__name__' : name}
    if attributes:
        attrs.update(attributes)

    # Generate a derived view class.
    class_ = type("SimpleViewletClass from %s" % template, bases, attrs)

    return class_


class ResourceViewletBase(orig_viewlet.ResourceViewletBase, Explicit):
    pass

def JavaScriptViewlet(path):
    """Create a viewlet that can simply insert a javascript link."""
    src = os.path.join(os.path.dirname(__file__), 'javascript_viewlet.pt')

    klass = type('JavaScriptViewlet',
                 (ResourceViewletBase, ViewletBase),
                  {'index': ZopeTwoPageTemplateFile(src),
                   '_path': path})

    return klass


class CSSResourceViewletBase(orig_viewlet.CSSResourceViewletBase):
    pass

def CSSViewlet(path, media="all", rel="stylesheet"):
    """Create a viewlet that can simply insert a javascript link."""
    src = os.path.join(os.path.dirname(__file__), 'css_viewlet.pt')

    klass = type('CSSViewlet',
                 (CSSResourceViewletBase, ViewletBase),
                  {'index': ZopeTwoPageTemplateFile(src),
                   '_path': path,
                   '_media':media,
                   '_rel':rel})

    return klass
