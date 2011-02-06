##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os
from logging import getLogger

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from App.class_init import InitializeClass
from App.Common import package_home
from App.special_dtml import DTMLFile
from App.config import getConfiguration
from Acquisition import aq_parent, aq_inner, aq_get
from ComputedAttribute import ComputedAttribute
from OFS.SimpleItem import SimpleItem
from OFS.Traversable import Traversable
from Shared.DC.Scripts.Script import Script
from Shared.DC.Scripts.Signature import FuncCode
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.PageTemplate import PageTemplate

from zope.contenttype import guess_content_type
from zope.pagetemplate.pagetemplatefile import sniff_type

LOG = getLogger('PageTemplateFile')

def guess_type(filename, text):

    # check for XML ourself since guess_content_type can't
    # detect text/xml  if 'filename' won't end with .xml
    # XXX: fix this in zope.contenttype

    if text.startswith('<?xml'):
        return 'text/xml'

    content_type, dummy = guess_content_type(filename, text)
    if content_type in ('text/html', 'text/xml'):
        return content_type
    return sniff_type(text) or 'text/html'

class PageTemplateFile(SimpleItem, Script, PageTemplate, Traversable):
    """Zope 2 implementation of a PageTemplate loaded from a file."""

    meta_type = 'Page Template (File)'

    func_defaults = None
    func_code = FuncCode((), 0)
    _v_last_read = 0

    # needed by App.class_init.InitializeClass
    _need__name__ = 1

    _default_bindings = {'name_subpath': 'traverse_subpath'}

    security = ClassSecurityInfo()
    security.declareProtected('View management screens',
      'read', 'document_src')

    def __init__(self, filename, _prefix=None, **kw):
        name = kw.pop('__name__', None)

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
        if meth is not None:
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
        if not kw.has_key('args'):
            kw['args'] = args
        bound_names['options'] = kw

        request = aq_get(self, 'REQUEST', None)
        if request is not None:
            response = request.response
            if not response.headers.has_key('content-type'):
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
        import Globals  # for data
        if self._v_last_read and not Globals.DevelopmentMode:
            return
        __traceback_info__ = self.filename
        try:
            mtime = os.path.getmtime(self.filename)
        except OSError:
            mtime = 0
        if self._v_program is not None and mtime == self._v_last_read:
            return
        f = open(self.filename, "rb")
        try:
            text = f.read(XML_PREFIX_MAX_LENGTH)
        except:
            f.close()
            raise
        t = sniff_type(text)
        if t != "text/xml":
            # For HTML, we really want the file read in text mode:
            f.close()
            f = open(self.filename, 'U')
            text = ''
        text += f.read()
        f.close()
        self.pt_edit(text, t)
        self._cook()
        if self._v_errors:
            LOG.error('Error in template %s' % '\n'.join(self._v_errors))
            return
        self._v_last_read = mtime

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
        raise StorageError, ("Instance of AntiPersistent class %s "
                             "cannot be stored." % self.__class__.__name__)

InitializeClass(PageTemplateFile)

XML_PREFIXES = [
    "<?xml",                      # ascii, utf-8
    "\xef\xbb\xbf<?xml",          # utf-8 w/ byte order mark
    "\0<\0?\0x\0m\0l",            # utf-16 big endian
    "<\0?\0x\0m\0l\0",            # utf-16 little endian
    "\xfe\xff\0<\0?\0x\0m\0l",    # utf-16 big endian w/ byte order mark
    "\xff\xfe<\0?\0x\0m\0l\0",    # utf-16 little endian w/ byte order mark
    ]

XML_PREFIX_MAX_LENGTH = max(map(len, XML_PREFIXES))

def sniff_type(text):
    for prefix in XML_PREFIXES:
        if text.startswith(prefix):
            return "text/xml"
    return None
