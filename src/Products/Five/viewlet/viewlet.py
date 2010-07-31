##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""

import os
import zope.viewlet.viewlet
from Products.Five.bbb import AcquisitionBBB
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class ViewletBase(zope.viewlet.viewlet.ViewletBase, AcquisitionBBB):
    pass

class SimpleAttributeViewlet(zope.viewlet.viewlet.SimpleAttributeViewlet,
                             AcquisitionBBB):
    pass

class simple(zope.viewlet.viewlet.simple):
    # We need to ensure that the proper __init__ is called.
    __init__ = ViewletBase.__init__.im_func

def SimpleViewletClass(template, bases=(), attributes=None,
                       name=u''):
    """A function that can be used to generate a viewlet from a set of
    information.
    """

    # Create the base class hierarchy
    bases += (simple, ViewletBase)

    attrs = {'index' : ViewPageTemplateFile(template),
             '__name__' : name}
    if attributes:
        attrs.update(attributes)

    # Generate a derived view class.
    class_ = type("SimpleViewletClass from %s" % template, bases, attrs)

    return class_


class ResourceViewletBase(zope.viewlet.viewlet.ResourceViewletBase):
    pass

def JavaScriptViewlet(path):
    """Create a viewlet that can simply insert a javascript link."""
    src = os.path.join(os.path.dirname(__file__), 'javascript_viewlet.pt')

    klass = type('JavaScriptViewlet',
                 (ResourceViewletBase, ViewletBase),
                  {'index': ViewPageTemplateFile(src),
                   '_path': path})

    return klass


class CSSResourceViewletBase(zope.viewlet.viewlet.CSSResourceViewletBase):
    pass

def CSSViewlet(path, media="all", rel="stylesheet"):
    """Create a viewlet that can simply insert a javascript link."""
    src = os.path.join(os.path.dirname(__file__), 'css_viewlet.pt')

    klass = type('CSSViewlet',
                 (CSSResourceViewletBase, ViewletBase),
                  {'index': ViewPageTemplateFile(src),
                   '_path': path,
                   '_media':media,
                   '_rel':rel})

    return klass
