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


""" Zope Page Template module (wrapper for the Zope 3 ZPT implementation) """

__version__='$Revision: 1.48 $'[11:-2]

from urllib import quote
import os, AccessControl, Acquisition 
from Globals import ImageFile, package_home, InitializeClass
from OFS.SimpleItem import SimpleItem
from OFS.content_types import guess_content_type
from DateTime.DateTime import DateTime
from Shared.DC.Scripts.Script import Script 
from Shared.DC.Scripts.Signature import FuncCode
from AccessControl import getSecurityManager

from OFS.History import Historical, html_diff
from OFS.Cache import Cacheable
from OFS.Traversable import Traversable
from OFS.PropertyManager import PropertyManager

from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from AccessControl import Unauthorized
from AccessControl.Permissions import view, ftp_access, change_page_templates, view_management_screens

from webdav.Lockable import ResourceLockedError
from webdav.WriteLockInterface import WriteLockInterface

from zope.pagetemplate.pagetemplate import PageTemplate

class Src(Acquisition.Explicit):
    """ I am scary code """

    index_html = None
    PUT = document_src = Acquisition.Acquired

    def __before_publishing_traverse__(self, ob, request):
        if getattr(request, '_hacked_path', 0):
            request._hacked_path = 0

    def __call__(self, REQUEST, RESPONSE):
        " "
        return self.document_src(REQUEST)


class ZPT(Script, PageTemplate, Historical, Cacheable,
                       Traversable, PropertyManager):
    """ Z2 wrapper class for Zope 3 page templates """

    __implements__ = (WriteLockInterface,)

    meta_type = 'ZPT'
    management_page_charset = 'utf-8'

    func_defaults = None
    func_code = FuncCode((), 0)

    _default_bindings = {'name_subpath': 'traverse_subpath'}
    _default_content_fn = os.path.join(package_home(globals()),
                                       'pt', 'default.html')

    manage_options = (
        {'label':'Edit', 'action':'pt_editForm',
         'help': ('PageTemplates', 'PageTemplate_Edit.stx')},
        {'label':'Test', 'action':'ZScriptHTML_tryForm'},
        ) + PropertyManager.manage_options \
        + Historical.manage_options \
        + SimpleItem.manage_options \
        + Cacheable.manage_options


    _properties=({'id':'title', 'type': 'ustring', 'mode': 'w'},
                 {'id':'content_type', 'type':'string', 'mode': 'w'},
                 {'id':'expand', 'type':'boolean', 'mode': 'w'},
                 )

    security = AccessControl.ClassSecurityInfo()
    security.declareObjectProtected(view)
    security.declareProtected(view, '__call__')

    def __init__(self, id, text=None, content_type=None, encoding='utf-8'):
        self.id = str(id)
        self.ZBindings_edit(self._default_bindings)
        if text is None:
            text = open(self._default_content_fn).read()
        self.pt_edit(text, content_type, encoding)

    def _setPropValue(self, id, value):
        PropertyManager._setPropValue(self, id, value)
        self.ZCacheable_invalidate()



    security.declareProtected(change_page_templates, 'pt_edit')
    def pt_edit(self, text, content_type, encoding='utf-8'):
        if not isinstance(text, unicode):
            text = unicode(text, encoding, 'strict')
        assert isinstance(text, unicode)
        self.ZCacheable_invalidate()
        PageTemplate.pt_edit(self, text, content_type)

    security.declareProtected(change_page_templates, 'pt_editAction')
    def pt_editAction(self, REQUEST, title, text, content_type, expand):
        """Change the title and document."""
        if self.wl_isLocked():
            raise ResourceLockedError("File is locked via WebDAV")
        self.expand=expand
        self.pt_setTitle(title)
        self.pt_edit(text, content_type)
        REQUEST.set('text', self.read()) # May not equal 'text'!
        REQUEST.set('title', self.title)
        message = "Saved changes."
        if getattr(self, '_v_warnings', None):
            message = ("<strong>Warning:</strong> <i>%s</i>"
                       % '<br>'.join(self._v_warnings))
        return self.pt_editForm(manage_tabs_message=message)


    security.declareProtected(change_page_templates, 'pt_setTitle')
    def pt_setTitle(self, title):
        charset = getattr(self, 'management_page_charset', None)
        if isinstance(title, str) and charset:
            try:
                title.decode('us-ascii')
                title = str(title)
            except UnicodeError:
                title = unicode(title, charset)
        elif not isinstance(title, unicode):
            title = str(title)
        self._setPropValue('title', title)

    security.declareProtected(change_page_templates, 'pt_upload')
    def pt_upload(self, REQUEST, file='', charset=None):
        """Replace the document with the text in file."""
        if self.wl_isLocked():
            raise ResourceLockedError("File is locked via WebDAV")

        filename = None
        if not isinstance(file, str):
            if not file: raise ValueError('File not specified')
            filename = file.filename
            file = file.read()

        ct, dummy = guess_content_type(filename, file)   
        if not ct in ('text/html', 'text/xml'):
            raise ValueError('Unsupported mimetype: %s' % ct)

        if not isinstance(file, unicode):
            if not charset:
                raise ValueError('No encoding specified for non-unicode content')
            file = unicode(file, charset)

        self.pt_edit(file, ct)
        message = 'Saved changes.'
        return self.pt_editForm(manage_tabs_message=message)

    security.declareProtected(change_page_templates, 'pt_changePrefs')
    def pt_changePrefs(self, REQUEST, height=None, width=None,
                       dtpref_cols="100%", dtpref_rows="20"):
        """Change editing preferences."""
        dr = {"Taller":5, "Shorter":-5}.get(height, 0)
        dc = {"Wider":5, "Narrower":-5}.get(width, 0)
        if isinstance(height, int): dtpref_rows = height
        if isinstance(width, int) or \
           isinstance(width, str) and width.endswith('%'):
            dtpref_cols = width
        rows = str(max(1, int(dtpref_rows) + dr))
        cols = str(dtpref_cols)
        if cols.endswith('%'):
           cols = str(min(100, max(25, int(cols[:-1]) + dc))) + '%'
        else:
           cols = str(max(35, int(cols) + dc))
        e = (DateTime("GMT") + 365).rfc822()
        setCookie = REQUEST["RESPONSE"].setCookie
        setCookie("dtpref_rows", rows, path='/', expires=e)
        setCookie("dtpref_cols", cols, path='/', expires=e)
        REQUEST.other.update({"dtpref_cols":cols, "dtpref_rows":rows})
        return self.manage_main()

    def ZScriptHTML_tryParams(self):
        """Parameters to test the script with."""
        return []

#    def manage_historyCompare(self, rev1, rev2, REQUEST,
#                              historyComparisonResults=''):
#        return ZopePageTemplate.inheritedAttribute(
#            'manage_historyCompare')(
#            self, rev1, rev2, REQUEST,
#            historyComparisonResults=html_diff(rev1._text, rev2._text) )

    def pt_getContext(self, **kw):
        root = self.getPhysicalRoot()
        context = self._getContext()
        c = {'template': self,
             'here': context,
             'context': context,
             'container': self._getContainer(),
             'nothing': None,
             'options': {},
             'root': root,
             'request': getattr(root, 'REQUEST', None),
             'modules': SecureModuleImporter,
             }
        return c

#    security.declareProtected(change_page_templates, 'write')
#    def write(self, text):
#        PageTemplate.write(self, text)

    security.declareProtected(view_management_screens, 'manage_main', 'read',
      'ZScriptHTML_tryForm')



    def _exec(self, bound_names, args, kw):
        """Call a Page Template"""
        if not kw.has_key('args'):
            kw['args'] = args
        bound_names['options'] = kw

        try:
            response = self.REQUEST.RESPONSE
            if not response.headers.has_key('content-type'):
                response.setHeader('content-type', self.content_type)
        except AttributeError:
            pass

        security=getSecurityManager()
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
            # XXX: check the parameters for pt_render()! (aj)
            result = self.pt_render(self.pt_getContext())
            assert isinstance(result, unicode)

#            result = self.pt_render(extra_context=bound_names)
            if keyset is not None:
                # Store the result in the cache.
                self.ZCacheable_set(result, keywords=keyset)
            return result
        finally:
            security.removeContext(self)

    security.declareProtected(change_page_templates,
      'manage_historyCopy',
      'manage_beforeHistoryCopy', 'manage_afterHistoryCopy')

    security.declareProtected(change_page_templates, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """ Handle HTTP PUT requests """
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        ## XXX:this should be unicode or we must pass an encoding
        self.pt_edit(REQUEST.get('BODY', ''))
        RESPONSE.setStatus(204)
        return RESPONSE

    security.declareProtected(change_page_templates, 'manage_FTPput')
    manage_FTPput = PUT

    security.declareProtected(ftp_access, 'manage_FTPstat','manage_FTPlist')

    security.declareProtected(ftp_access, 'manage_FTPget')
    def manage_FTPget(self):
        "Get source for FTP download"
        self.REQUEST.RESPONSE.setHeader('Content-Type', self.content_type)
        return self.read()

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

    def om_icons(self):
        """Return a list of icon URLs to be displayed by an ObjectManager"""
        icons = ({'path': 'misc_/PageTemplates/zpt.gif',
                  'alt': self.meta_type, 'title': self.meta_type},)
        if not self._v_cooked:
            self._cook()
        if self._v_errors:
            icons = icons + ({'path': 'misc_/PageTemplates/exclamation.gif',
                              'alt': 'Error',
                              'title': 'This template has an error'},)
        return icons

    security.declareProtected(view, 'pt_source_file')
    def pt_source_file(self):
        """Returns a file name to be compiled into the TAL code."""
        try:
            return '/'.join(self.getPhysicalPath())
        except:
            # This page template is being compiled without an
            # acquisition context, so we don't know where it is. :-(
            return None

    def wl_isLocked(self):
        return 0

    security.declareProtected(view_management_screens, 'source_dot_xml')
    source_dot_xml = Src()

    security.declareProtected(view_management_screens, 'pt_editForm')
    pt_editForm = PageTemplateFile('pt/ptEdit', globals(),
                                   __name__='pt_editForm')
    pt_editForm._owner = None
    manage = manage_main = pt_editForm


InitializeClass(ZPT)


setattr(ZPT, 'source.xml',  ZPT.source_dot_xml)
setattr(ZPT, 'source.html', ZPT.source_dot_xml)

# Product registration and Add support
manage_addZPTForm= PageTemplateFile(
    'pt/ptAdd', globals(), __name__='manage_addPageTemplateForm')


def manage_addZPT(self, id, title=None, text=None,
                           REQUEST=None, submit=None):
    "Add a Page Template with optional file content."

    id = str(id)
    if REQUEST is None:
        self._setObject(id, ZPT(id, text))
        ob = getattr(self, id)
        if title:
            ob.pt_setTitle(title)
        return ob
    else:
        file = REQUEST.form.get('file')
        headers = getattr(file, 'headers', None)
        if headers is None or not file.filename:
            zpt = ZPT(id, text) # collector 596
        else:
            zpt = ZPT(id, file, headers.get('content_type'))

        self._setObject(id, zpt)

        # collector 596
        if title:
            ob = getattr(self, id)
            ob.pt_setTitle(title)

        try:
            u = self.DestinationURL()
        except AttributeError:
            u = REQUEST['URL1']

        if submit == " Add and Edit ":
            u = "%s/%s" % (u, quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''

from Products.PageTemplates import misc_
misc_['exclamation.gif'] = ImageFile('pt/exclamation.gif', globals())

def initialize(context):
    context.registerClass(
        ZPT,
        permission='Add Page Templates',
        constructors=(manage_addZPTForm,
                      manage_addZPT),
        icon='pt/zpt.gif',
        )
    context.registerHelp()
    context.registerHelpTitle('Zope Help')

