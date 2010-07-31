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
"""A 'PageTemplateFile' without security restrictions.
"""

from os.path import basename
from zope.component import getMultiAdapter
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from zope.pagetemplate.engine import TrustedAppPT

from Acquisition import aq_get
from AccessControl import getSecurityManager
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.Expressions import createTrustedZopeEngine

from Products.Five.bbb import AcquisitionBBB

_engine = createTrustedZopeEngine()
def getEngine():
    return _engine

class ViewPageTemplateFile(TrustedAppPT, PageTemplateFile):
    """Page Template used as class variable of views defined as Python classes.
    """
    def __init__(self, filename, _prefix=None, content_type=None):
        _prefix = self.get_path_from_prefix(_prefix)
        super(ViewPageTemplateFile, self).__init__(filename, _prefix)
        if content_type is not None:
            self.content_type = content_type

    def getId(self):
        return basename(self.filename)

    id = property(getId)

    def __call__(self, __instance, *args, **keywords):
        # Work around BBB foul. Before Zope 2.12 there was no first argument
        # but the zope.pagetemplate version has one called instance. Some
        # people used instance as an additional keyword argument.
        instance = __instance
        namespace = self.pt_getContext(
            request=instance.request,
            instance=instance, args=args, options=keywords)
        debug_flags = instance.request.debug
        s = self.pt_render(
            namespace,
            showtal=getattr(debug_flags, 'showTAL', 0),
            sourceAnnotations=getattr(debug_flags, 'sourceAnnotations', 0),
            )
        response = instance.request.response
        if not response.getHeader("Content-Type"):
            response.setHeader("Content-Type", self.content_type)
        return s

    def pt_getEngine(self):
        return getEngine()

    def pt_getContext(self, instance, request, **kw):
        namespace = super(ViewPageTemplateFile, self).pt_getContext(**kw)
        namespace['request'] = request
        namespace['view'] = instance
        namespace['context'] = context = instance.context
        namespace['views'] = ViewMapper(context, request)

        # get the root
        obj = context
        root = None
        meth = aq_get(obj, 'getPhysicalRoot', None)
        if meth is not None:
            root = meth()

        namespace.update(here=obj,
                         # philiKON thinks container should be the view,
                         # but BBB is more important than aesthetics.
                         container=obj,
                         root=root,
                         modules=SecureModuleImporter,
                         traverse_subpath=[],  # BBB, never really worked
                         user = getSecurityManager().getUser()
                        )
        return namespace

    def __get__(self, instance, type):
        return BoundPageTemplate(self, instance)


class ViewMapper(object):
    def __init__(self, ob, request):
        self.ob = ob
        self.request = request

    def __getitem__(self, name):
        return getMultiAdapter((self.ob, self.request), name=name)

# When a view's template is accessed e.g. as template.view, a
# BoundPageTemplate object is retured.  For BBB reasons, it needs to
# support the aq_* methods and attributes known from Acquisition.  For
# that it also needs to be locatable thru __parent__.

class BoundPageTemplate(AcquisitionBBB):
    def __init__(self, pt, ob):
        object.__setattr__(self, 'im_func', pt)
        object.__setattr__(self, 'im_self', ob)

    macros = property(lambda self: self.im_func.macros)
    filename = property(lambda self: self.im_func.filename)
    __parent__ = property(lambda self: self.im_self)

    def __call__(self, *args, **kw):
        if self.im_self is None:
            im_self, args = args[0], args[1:]
        else:
            im_self = self.im_self
        return self.im_func(im_self, *args, **kw)

    def __setattr__(self, name, v):
        raise AttributeError("Can't set attribute", name)

    def __repr__(self):
        return "<BoundPageTemplateFile of %r>" % self.im_self


# BBB
ZopeTwoPageTemplateFile = ViewPageTemplateFile
