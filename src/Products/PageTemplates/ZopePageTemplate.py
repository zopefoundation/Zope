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
"""Zope Page Template module (wrapper for the zope.pagetemplate implementation)
"""

import os
import sys

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import change_page_templates
from AccessControl.Permissions import ftp_access
from AccessControl.Permissions import view
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Acquired
from Acquisition import aq_get
from Acquisition import Explicit
from zExceptions import Redirect
from zExceptions import ResourceLockedError

from App.Common import package_home
from OFS.Cache import Cacheable
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager
from OFS.Traversable import Traversable
from Shared.DC.Scripts.Script import Script
from Shared.DC.Scripts.Signature import FuncCode
from Products.PageTemplates import bbb
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.PageTemplateFile import guess_type
from Products.PageTemplates.utils import encodingFromXMLPreamble
from Products.PageTemplates.utils import charsetFromMetaEquiv
from Products.PageTemplates.utils import convertToUnicode

if sys.version_info >= (3, ):
    unicode = str

preferred_encodings = ['utf-8', 'iso-8859-15']
if 'ZPT_PREFERRED_ENCODING' in os.environ:
    preferred_encodings.insert(0, os.environ['ZPT_PREFERRED_ENCODING'])


class Src(Explicit):
    """ I am scary code """
    security = ClassSecurityInfo()
    security.declareObjectProtected(view_management_screens)

    PUT = document_src = Acquired
    index_html = None

    def __before_publishing_traverse__(self, ob, request):
        if getattr(request, '_hacked_path', 0):
            request._hacked_path = 0

    def __call__(self, REQUEST, RESPONSE):
        " "
        return self.document_src(REQUEST)

InitializeClass(Src)


class ZopePageTemplate(Script, PageTemplate, Cacheable,
                       Traversable, PropertyManager):
    "Zope wrapper for Page Template using TAL, TALES, and METAL"

    meta_type = 'Page Template'
    output_encoding = 'utf-8'  # provide default for old instances

    __code__ = func_code = FuncCode((), 0)
    __defaults__ = func_defaults = None

    _default_bindings = {'name_subpath': 'traverse_subpath'}
    _default_content_fn = os.path.join(package_home(globals()),
                                       'www', 'default.html')

    manage_options = (
        {'label': 'Edit', 'action': 'pt_editForm'},
    ) + PropertyManager.manage_options + \
        SimpleItem.manage_options + \
        Cacheable.manage_options

    _properties = (
        {'id': 'title', 'type': 'ustring', 'mode': 'w'},
        {'id': 'content_type', 'type': 'string', 'mode': 'w'},
        {'id': 'output_encoding', 'type': 'string', 'mode': 'w'},
        {'id': 'expand', 'type': 'boolean', 'mode': 'w'},
    )

    security = ClassSecurityInfo()
    security.declareObjectProtected(view)

    # protect methods from base class(es)
    security.declareProtected(view, '__call__')

    def __init__(self, id, text=None, content_type='text/html', strict=True,
                 output_encoding='utf-8'):
        self.id = id
        self.expand = 0
        self.ZBindings_edit(self._default_bindings)
        self.output_encoding = output_encoding
        # default content
        if not text:
            text = open(self._default_content_fn).read()
            content_type = 'text/html'
        self.pt_edit(text, content_type)

    security.declareProtected(change_page_templates, 'pt_edit')
    def pt_edit(self, text, content_type, keep_output_encoding=False):
        text = text.strip()

        is_unicode = isinstance(text, unicode)
        encoding = None
        output_encoding = None

        if content_type.startswith('text/xml'):

            if is_unicode:
                encoding = None
                output_encoding = 'utf-8'
            else:
                encoding = encodingFromXMLPreamble(text)
                output_encoding = 'utf-8'

        elif content_type.startswith('text/html'):

            charset = charsetFromMetaEquiv(text)

            if is_unicode:
                if charset:
                    encoding = None
                    output_encoding = charset
                else:
                    encoding = None
                    output_encoding = 'utf-8'
            else:
                if charset:
                    encoding = charset
                    output_encoding = charset
                else:
                    encoding = 'utf-8'
                    output_encoding = 'utf-8'

        else:
            utext, encoding = convertToUnicode(text,
                                               content_type,
                                               preferred_encodings)
            output_encoding = encoding

        # for content updated through WebDAV, FTP
        if not keep_output_encoding:
            self.output_encoding = output_encoding

        if not is_unicode:
            text = unicode(text, encoding)

        self.ZCacheable_invalidate()
        super(ZopePageTemplate, self).pt_edit(text, content_type)

    pt_editForm = PageTemplateFile('www/ptEdit', globals(),
                                   __name__='pt_editForm')
    pt_editForm._owner = None
    manage = manage_main = pt_editForm

    source_dot_xml = Src()

    security.declareProtected(change_page_templates, 'pt_editAction')
    def pt_editAction(self, REQUEST, title, text, content_type, expand=0):
        """Change the title and document."""

        if self.wl_isLocked():
            raise ResourceLockedError("File is locked.")

        self.expand = expand

        # The ZMI edit view uses utf-8! So we can safely assume
        # that 'title' and 'text' are utf-8 encoded strings - hopefully

        self.pt_setTitle(title, 'utf-8')
        text = unicode(text, 'utf-8')

        self.pt_edit(text, content_type, True)
        REQUEST.set('text', self.read())  # May not equal 'text'!
        REQUEST.set('title', self.title)
        message = "Saved changes."
        if getattr(self, '_v_warnings', None):
            message = ("<strong>Warning:</strong> <i>%s</i>"
                       % '<br>'.join(self._v_warnings))
        return self.pt_editForm(manage_tabs_message=message)

    security.declareProtected(change_page_templates, 'pt_setTitle')
    def pt_setTitle(self, title, encoding='utf-8'):
        if not isinstance(title, unicode):
            title = unicode(title, encoding)
        self._setPropValue('title', title)

    def _setPropValue(self, id, value):
        """ set a property and invalidate the cache """
        PropertyManager._setPropValue(self, id, value)
        self.ZCacheable_invalidate()

    security.declareProtected(change_page_templates, 'pt_upload')
    def pt_upload(self, REQUEST, file='', encoding='utf-8'):
        """Replace the document with the text in file."""

        if self.wl_isLocked():
            raise ResourceLockedError("File is locked.")

        if isinstance(file, str):
            filename = None
            text = file
        else:
            if not file:
                raise ValueError('File not specified')
            filename = file.filename
            text = file.read()

        content_type = guess_type(filename, text)
        self.pt_edit(text, content_type)
        return self.pt_editForm(manage_tabs_message='Saved changes')

    def pt_getContext(self, *args, **kw):
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

    def write(self, text):
        if not isinstance(text, unicode):
            text, encoding = convertToUnicode(text,
                                              self.content_type,
                                              preferred_encodings)
            self.output_encoding = encoding

        self.ZCacheable_invalidate()
        ZopePageTemplate.inheritedAttribute('write')(self, text)

    def _exec(self, bound_names, args, kw):
        """Call a Page Template"""
        if 'args' not in kw:
            kw['args'] = args
        bound_names['options'] = kw

        request = aq_get(self, 'REQUEST', None)
        if request is not None:
            response = request.response
            if 'content-type' not in response.headers:
                response.setHeader('content-type', self.content_type)

        security = getSecurityManager()
        bound_names['user'] = security.getUser()

        # Retrieve the value from the cache.
        keyset = None
        if self.ZCacheable_isCachingEnabled():
            # Prepare a cache key.
            keyset = {'here': self._getContext(),
                      'bound_names': bound_names}
            result = self.ZCacheable_get(keywords=keyset)
            if result is not None:
                # Got a cached value.
                return result

        # Execute the template in a new security context.
        security.addContext(self)

        try:
            result = self.pt_render(extra_context=bound_names)
            if keyset is not None:
                # Store the result in the cache.
                self.ZCacheable_set(result, keywords=keyset)
            return result
        finally:
            security.removeContext(self)

    if bbb.HAS_ZSERVER:
        security.declareProtected(change_page_templates, 'PUT')
        def PUT(self, REQUEST, RESPONSE):
            """ Handle HTTP PUT requests """

            self.dav__init(REQUEST, RESPONSE)
            self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
            text = REQUEST.get('BODY', '')
            content_type = guess_type('', text)
            self.pt_edit(text, content_type)
            RESPONSE.setStatus(204)
            return RESPONSE

        security.declareProtected(change_page_templates, 'manage_FTPput')
        manage_FTPput = PUT

        security.declareProtected(ftp_access, 'manage_FTPstat')
        security.declareProtected(ftp_access, 'manage_FTPlist')
        security.declareProtected(ftp_access, 'manage_FTPget')
        def manage_FTPget(self):
            "Get source for FTP download"
            result = self.read()
            return result.encode(self.output_encoding)

    security.declareProtected(view_management_screens, 'html')
    def html(self):
        return self.content_type == 'text/html'

    security.declareProtected(view_management_screens, 'get_size')
    def get_size(self):
        return len(self.read())

    security.declareProtected(view_management_screens, 'getSize')
    getSize = get_size

    security.declareProtected(view_management_screens, 'PrincipiaSearchSource')
    def PrincipiaSearchSource(self):
        "Support for searching - the document's contents are searched."
        return self.read()

    security.declareProtected(view_management_screens, 'document_src')
    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return expanded document source."""
        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        if REQUEST is not None and REQUEST.get('raw'):
            return self._text
        return self.read()

    security.declareProtected(view, 'pt_source_file')
    def pt_source_file(self):
        """Returns a file name to be compiled into the TAL code."""
        try:
            return '/'.join(self.getPhysicalPath())
        except Exception:
            # This page template is being compiled without an
            # acquisition context, so we don't know where it is. :-(
            return None

    def __setstate__(self, state):
        # Perform on-the-fly migration to unicode.
        # Perhaps it might be better to work with the 'generation' module
        # here?
        _text = state.get('_text')
        if _text is not None and not isinstance(state['_text'], unicode):
            text, encoding = convertToUnicode(
                state['_text'],
                state.get('content_type', 'text/html'),
                preferred_encodings)
            state['_text'] = text
            state['output_encoding'] = encoding
        self.__dict__.update(state)

    def pt_render(self, source=False, extra_context={}):
        result = PageTemplate.pt_render(self, source, extra_context)
        assert isinstance(result, unicode)
        return result

    def wl_isLocked(self):
        return 0


InitializeClass(ZopePageTemplate)

setattr(ZopePageTemplate, 'source.xml', ZopePageTemplate.source_dot_xml)
setattr(ZopePageTemplate, 'source.html', ZopePageTemplate.source_dot_xml)

# Product registration and Add support
manage_addPageTemplateForm = PageTemplateFile(
    'www/ptAdd', globals(), __name__='manage_addPageTemplateForm')


def manage_addPageTemplate(self, id, title='', text='', encoding='utf-8',
                           submit=None, REQUEST=None, RESPONSE=None):
    "Add a Page Template with optional file content."

    filename = ''
    content_type = 'text/html'

    if REQUEST and 'file' in REQUEST:
        file = REQUEST['file']
        filename = file.filename
        text = file.read()
        headers = getattr(file, 'headers', None)
        if headers and 'content_type' in headers:
            content_type = headers['content_type']
        else:
            content_type = guess_type(filename, text)
    else:
        if hasattr(text, 'read'):
            filename = getattr(text, 'filename', '')
            headers = getattr(text, 'headers', None)
            text = text.read()
            if headers and 'content_type' in headers:
                content_type = headers['content_type']
            else:
                content_type = guess_type(filename, text)

    # ensure that we pass unicode to the constructor to
    # avoid further hassles with pt_edit()

    if not isinstance(text, unicode):
        text = unicode(text, encoding)

    zpt = ZopePageTemplate(id, text, content_type, output_encoding=encoding)
    zpt.pt_setTitle(title, encoding)
    self._setObject(id, zpt)
    zpt = getattr(self, id)

    if RESPONSE:
        if submit == " Add and Edit ":
            raise Redirect(zpt.absolute_url() + '/pt_editForm')
        else:
            raise Redirect(self.absolute_url() + '/manage_main')
    else:
        return zpt


def initialize(context):
    context.registerClass(
        ZopePageTemplate,
        permission='Add Page Templates',
        constructors=(manage_addPageTemplateForm,
                      manage_addPageTemplate),
    )
