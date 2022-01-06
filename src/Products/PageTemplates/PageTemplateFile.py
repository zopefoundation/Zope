##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os
from logging import getLogger

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_get
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.Common import package_home
from App.config import getConfiguration
from ComputedAttribute import ComputedAttribute
from OFS.SimpleItem import SimpleItem
from OFS.Traversable import Traversable
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.utils import encodingFromXMLPreamble
from Shared.DC.Scripts.Script import Script
from Shared.DC.Scripts.Signature import FuncCode
from zope.contenttype import guess_content_type
from zope.pagetemplate.pagetemplatefile import DEFAULT_ENCODING
from zope.pagetemplate.pagetemplatefile import XML_PREFIX_MAX_LENGTH
from zope.pagetemplate.pagetemplatefile import meta_pattern
from zope.pagetemplate.pagetemplatefile import sniff_type


LOG = getLogger('PageTemplateFile')


def guess_type(filename, body):
    # check for XML ourself since guess_content_type can't
    # detect text/xml  if 'filename' won't end with .xml
    # XXX: fix this in zope.contenttype

    if body.startswith(b'<?xml') or filename.lower().endswith('.xml'):
        return 'text/xml'

    content_type, ignored_encoding = guess_content_type(filename, body)
    if content_type in ('text/html', 'text/xml'):
        return content_type
    return sniff_type(body) or 'text/html'


# REFACT: Make this a subclass of
# zope.pagetemplate.pagetemplatefile.PageTemplateFile
# That class has been forked off of this code and now we have duplication.
# They already share a common superclass
# zope.pagetemplate.pagetemplate.PageTemplate
class PageTemplateFile(SimpleItem, Script, PageTemplate, Traversable):
    """Zope 2 implementation of a PageTemplate loaded from a file."""

    meta_type = 'Page Template (File)'

    __code__ = FuncCode((), 0)
    __defaults__ = None
    _v_last_read = 0

    # needed by AccessControl.class_init.InitializeClass
    _need__name__ = 1

    _default_bindings = {'name_subpath': 'traverse_subpath'}

    security = ClassSecurityInfo()
    security.declareProtected(  # NOQA: D001
        'View management screens', 'read', 'document_src')

    def __init__(
        self, filename, _prefix=None, encoding=DEFAULT_ENCODING, **kw
    ):
        name = kw.pop('__name__', None)
        self.encoding = encoding
        basepath, ext = os.path.splitext(filename)

        if name:
            self.id = self.__name__ = name
            self._need__name__ = 0
        else:
            self.id = self.__name__ = os.path.basename(basepath)

        if _prefix:
            if isinstance(_prefix, str):
                filename = os.path.join(_prefix, filename)
            else:
                filename = os.path.join(package_home(_prefix), filename)

        if not ext:
            filename = filename + '.zpt'

        self.filename = filename

    def pt_getContext(self):
        root = None
        meth = aq_get(self, 'getPhysicalRoot', None)
        if callable(meth):
            root = meth()
        context = self._getContext()
        c = {'template': self,
             'here': context,
             'context': context,
             'container': self._getContainer(),
             'nothing': None,
             'options': {},
             'root': root,
             'request': aq_get(root, 'REQUEST', None),
             'modules': SecureModuleImporter,
             }
        return c

    def _exec(self, bound_names, args, kw):
        """Call a Page Template"""
        self._cook_check()
        if 'args' not in kw:
            kw['args'] = args
        bound_names['options'] = kw

        request = aq_get(self, 'REQUEST', None)
        if request is not None:
            response = request.response
            if 'content-type' not in response.headers:
                response.setHeader('content-type', self.content_type)

        # Execute the template in a new security context.
        security = getSecurityManager()
        bound_names['user'] = security.getUser()
        security.addContext(self)

        try:
            context = self.pt_getContext()
            context.update(bound_names)
            return self.pt_render(extra_context=bound_names)
        finally:
            security.removeContext(self)

    def pt_macros(self):
        self._cook_check()
        return PageTemplate.pt_macros(self)

    def pt_source_file(self):
        """Returns a file name to be compiled into the TAL code."""
        return self.__name__  # Don't reveal filesystem paths

    def _cook_check(self):
        if self._v_last_read and not getConfiguration().debug_mode:
            return
        __traceback_info__ = self.filename
        try:
            mtime = os.path.getmtime(self.filename)
        except OSError:
            mtime = 0
        if self._v_program is not None and mtime == self._v_last_read:
            return
        text, type_ = self._read_file()
        self.pt_edit(text, type_)
        self._cook()
        if self._v_errors:
            LOG.error('Error in template %s' % '\n'.join(self._v_errors))
            return
        self._v_last_read = mtime

    def _prepare_html(self, text):
        match = meta_pattern.search(text)
        if match is not None:
            type_, encoding = (x.decode(self.encoding) for x in match.groups())
            # TODO: Shouldn't <meta>/<?xml?> stripping
            # be in PageTemplate.__call__()?
            text = meta_pattern.sub(b"", text)
        else:
            type_ = None
            encoding = self.encoding
        text = text.decode(encoding)
        return text, type_

    def _prepare_xml(self, text):
        if not isinstance(text, str):
            encoding = encodingFromXMLPreamble(text, default=self.encoding)
            text = text.decode(encoding)
        return text, 'text/xml'

    def _read_file(self):
        __traceback_info__ = self.filename
        with open(self.filename, "rb") as f:
            text = f.read(XML_PREFIX_MAX_LENGTH)
            type_ = sniff_type(text)
            text += f.read()
        if type_ != "text/xml":
            text, type_ = self._prepare_html(text)
        else:
            text, type_ = self._prepare_xml(text)
        f.close()
        return text, type_

    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return expanded document source."""

        if RESPONSE is not None:
            # Since _cook_check() can cause self.content_type to change,
            # we have to make sure we call it before setting the
            # Content-Type header.
            self._cook_check()
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    def _get__roles__(self):
        imp = getattr(aq_parent(aq_inner(self)),
                      '%s__roles__' % self.__name__)
        if hasattr(imp, '__of__'):
            return imp.__of__(self)
        return imp

    __roles__ = ComputedAttribute(_get__roles__, 1)

    def getOwner(self, info=0):
        """Gets the owner of the executable object.

        This method is required of all objects that go into
        the security context stack.  Since this object came from the
        filesystem, it is owned by no one managed by Zope.
        """
        return None

    def __getstate__(self):
        from ZODB.POSException import StorageError
        raise StorageError("Instance of AntiPersistent class %s "
                           "cannot be stored." % self.__class__.__name__)


InitializeClass(PageTemplateFile)
