##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Page Template module

$Id$
"""
import sys
import ExtensionClass
import zope.pagetemplate.pagetemplate
from zope.pagetemplate.pagetemplate import _error_start, PTRuntimeError
from zope.pagetemplate.pagetemplate import PageTemplateTracebackSupplement
from zope.tales.expressions import SimpleModuleImporter
from Products.PageTemplates.Expressions import getEngine

##############################################################################
# BBB 2005/05/01 -- to be removed after 12 months
_ModuleImporter = SimpleModuleImporter
ModuleImporter = SimpleModuleImporter()
import zope.deprecation
zope.deprecation.deprecated(
    ('ModuleImporter', '_ModuleImporter'),
    "Zope 2 uses the Zope 3 ZPT engine now.  ModuleImporter has moved "
    "to zope.pagetemplate.pagetemplate.SimpleModuleImporter (this is a "
    "class, not an instance)."
    )
zope.deprecation.deprecated(
    ('PTRuntimeError', 'PageTemplateTracebackSupplement'),
    "Zope 2 uses the Zope 3 ZPT engine now.  The object you're importing "
    "has moved to zope.pagetemplate.pagetemplate.  This reference will "
    "be gone in Zope 2.12.",
    )
##############################################################################

class PageTemplate(ExtensionClass.Base,
                   zope.pagetemplate.pagetemplate.PageTemplate):

    def pt_getEngine(self):
        return getEngine()

    def pt_getContext(self):
        c = {'template': self,
             'options': {},
             'nothing': None,
             'request': None,
             'modules': SimpleModuleImporter(),
             }
        parent = getattr(self, 'aq_parent', None)
        if parent is not None:
            c['here'] = parent
            c['context'] = parent
            c['container'] = self.aq_inner.aq_parent
            while parent is not None:
                self = parent
                parent = getattr(self, 'aq_parent', None)
            c['root'] = self
        return c

    @property
    def macros(self):
        return self.pt_macros()

    # sub classes may override this to do additional stuff for macro access
    def pt_macros(self):
        self._cook_check()
        if self._v_errors:
            __traceback_supplement__ = (PageTemplateTracebackSupplement, self, {})
            raise PTRuntimeError, (
                'Page Template %s has errors: %s' % (
                self.id, self._v_errors
                ))
        return self._v_macros

    # these methods are reimplemented or duplicated here because of
    # different call signatures in the Zope 2 world

    def pt_render(self, source=False, extra_context={}):
        c = self.pt_getContext()
        c.update(extra_context)
        return super(PageTemplate, self).pt_render(c, source=source)

    def pt_errors(self, namespace={}):
        self._cook_check()
        err = self._v_errors
        if err:
            return err
        try:
            self.pt_render(source=True, extra_context=namespace)
        except:
            return ('Macro expansion failed', '%s: %s' % sys.exc_info()[:2])

    def __call__(self, *args, **kwargs):
        if not kwargs.has_key('args'):
            kwargs['args'] = args
        return self.pt_render(extra_context={'options': kwargs})

    def read(self):
        self._cook_check()
        if not self._v_errors:
            if not self.expand:
                return self._text
            try:
                return self.pt_render(source=True)
            except:
                return ('%s\n Macro expansion failed\n %s\n-->\n%s' %
                        (_error_start, "%s: %s" % sys.exc_info()[:2],
                         self._text) )

        return ('%s\n %s\n-->\n%s' % (_error_start,
                                      '\n '.join(self._v_errors),
                                      self._text))

    # convenience method for the ZMI which allows to explicitly
    # specify the HTMLness of a template.  The old Zope 2
    # implementation had this as well, but arguably on the wrong class
    # (this should be a ZopePageTemplate thing if at all)
    def html(self):
        if not hasattr(getattr(self, 'aq_base', self), 'is_html'):
            return self.content_type == 'text/html'
        return self.is_html
