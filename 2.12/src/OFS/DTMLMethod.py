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
"""DTML Method objects.
"""
from urllib import quote

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.Role import RoleManager
from Acquisition import Implicit
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from DateTime.DateTime import DateTime
from AccessControl import getSecurityManager
from AccessControl.Permissions import change_dtml_methods
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import change_proxy_roles
from AccessControl.Permissions import view as View
from AccessControl.Permissions import ftp_access
from AccessControl.DTML import RestrictedDTML
from AccessControl.requestmethod import requestmethod
from OFS.Cache import Cacheable
from OFS.History import Historical
from OFS.History import html_diff
from OFS.SimpleItem import Item_w__name__
from OFS.ZDOM import ElementWithTitle
from webdav.Lockable import ResourceLockedError
from zExceptions import Forbidden
from zExceptions.TracebackSupplement import PathTracebackSupplement
from ZPublisher.Iterators import IStreamIterator
from ZPublisher.TaintedString import TaintedString
from zope.contenttype import guess_content_type


_marker = []  # Create a new marker object.

class DTMLMethod(RestrictedDTML,
                 HTML,
                 Implicit,
                 RoleManager,
                 ElementWithTitle,
                 Item_w__name__,
                 Historical,
                 Cacheable,
                ):
    """ DocumentTemplate.HTML objects that act as methods of their containers.
    """
    meta_type = 'DTML Method'
    _proxy_roles = ()
    index_html = None # Prevent accidental acquisition
    _cache_namespace_keys = ()

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    # Documents masquerade as functions:
    class func_code:
        pass
    func_code = func_code()
    func_code.co_varnames = 'self', 'REQUEST', 'RESPONSE'
    func_code.co_argcount = 3

    manage_options = (
        (
            {'label': 'Edit', 'action': 'manage_main',
             'help': ('OFSP', 'DTML-DocumentOrMethod_Edit.stx')},
            {'label': 'View', 'action': '',
             'help': ('OFSP', 'DTML-DocumentOrMethod_View.stx')},
            {'label': 'Proxy', 'action': 'manage_proxyForm',
             'help': ('OFSP', 'DTML-DocumentOrMethod_Proxy.stx')},
            )
        + Historical.manage_options
        + RoleManager.manage_options
        + Item_w__name__.manage_options
        + Cacheable.manage_options
        )

    # Careful in permission changes--used by DTMLDocument!

    security.declareProtected(change_dtml_methods, 'manage_historyCopy')
    security.declareProtected(change_dtml_methods, 'manage_beforeHistoryCopy')
    security.declareProtected(change_dtml_methods, 'manage_afterHistoryCopy')

    # More reasonable default for content-type for http HEAD requests.
    default_content_type = 'text/html'

    security.declareProtected(View, '__call__')
    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """Render using the given client object
        
        o If client is not passed, we are being called as a sub-template:
          don't do any error propagation.

        o If supplied, use the REQUEST mapping, Response, and key word
        arguments.
        """
        if not self._cache_namespace_keys:
            data = self.ZCacheable_get(default=_marker)
            if data is not _marker:
                if ( IStreamIterator.isImplementedBy(data) and
                     RESPONSE is not None ):
                    # This is a stream iterator and we need to set some
                    # headers now before giving it to medusa
                    if RESPONSE.headers.get('content-length', None) is None:
                        RESPONSE.setHeader('content-length', len(data))

                    if ( RESPONSE.headers.get('content-type', None) is None and
                         RESPONSE.headers.get('Content-type', None) is None ):
                        ct = ( self.__dict__.get('content_type') or
                               self.default_content_type )
                        RESPONSE.setHeader('content-type', ct)

                # Return cached results.
                return data

        __traceback_supplement__ = (PathTracebackSupplement, self)
        kw['document_id'] = self.getId()
        kw['document_title'] = self.title

        security = getSecurityManager()
        security.addContext(self)
        if self.__dict__.has_key('validate'):
            first_time_through = 0
        else:
            self.__dict__['validate'] = security.DTMLValidate
            first_time_through = 1
        try:

            if client is None:
                # Called as subtemplate, so don't need error propagation!
                r = apply(HTML.__call__, (self, client, REQUEST), kw)
                if RESPONSE is None:
                    result = r
                else:
                    result = decapitate(r, RESPONSE)
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(result)
                return result

            r = apply(HTML.__call__, (self, client, REQUEST), kw)
            if type(r) is not type('') or RESPONSE is None:
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(r)
                return r

        finally:
            security.removeContext(self)
            if first_time_through:
                del self.__dict__['validate']

        have_key = RESPONSE.headers.has_key
        if not (have_key('content-type') or have_key('Content-Type')):
            if self.__dict__.has_key('content_type'):
                c = self.content_type
            else:
                c, e = guess_content_type(self.getId(), r)
            RESPONSE.setHeader('Content-Type', c)
        result = decapitate(r, RESPONSE)
        if not self._cache_namespace_keys:
            self.ZCacheable_set(result)
        return result

    def validate(self, inst, parent, name, value, md=None):
        return getSecurityManager().validate(inst, parent, name, value)

    def ZDocumentTemplate_beforeRender(self, md, default):
        # Tries to get a cached value.
        if self._cache_namespace_keys:
            # Use the specified keys from the namespace to identify a
            # cache entry.
            kw = {}
            for key in self._cache_namespace_keys:
                try:
                    val = md[key]
                except:
                    val = None
                kw[key] = val
            return self.ZCacheable_get(keywords=kw, default=default)
        return default

    def ZDocumentTemplate_afterRender(self, md, result):
        # Tries to set a cache value.
        if self._cache_namespace_keys:
            kw = {}
            for key in self._cache_namespace_keys:
                try:
                    val = md[key]
                except:
                    val = None
                kw[key] = val
            self.ZCacheable_set(result, keywords=kw)

    security.declareProtected(change_dtml_methods, 'ZCacheable_configHTML')
    ZCacheable_configHTML = DTMLFile('dtml/cacheNamespaceKeys', globals())

    security.declareProtected(change_dtml_methods, 'getCacheNamespaceKeys')
    def getCacheNamespaceKeys(self):
        """ Return the cacheNamespaceKeys.
        """
        return self._cache_namespace_keys

    security.declareProtected(change_dtml_methods, 'setCacheNamespaceKeys')
    def setCacheNamespaceKeys(self, keys, REQUEST=None):
        """ Set the list of names looked up to provide a cache key.
        """
        ks = []
        for key in keys:
            key = str(key).strip()
            if key:
                ks.append(key)
        self._cache_namespace_keys = tuple(ks)
        if REQUEST is not None:
            return self.ZCacheable_manage(self, REQUEST)

    security.declareProtected(View, 'get_size')
    def get_size(self):
        return len(self.raw)

    # deprecated; use get_size!
    getSize = get_size

    security.declareProtected(change_dtml_methods, 'manage')

    security.declareProtected(change_dtml_methods, 'manage_editForm')
    manage_editForm = DTMLFile('dtml/documentEdit', globals())
    manage_editForm._setName('manage_editForm')

    # deprecated!
    manage_uploadForm = manage_editForm

    security.declareProtected(change_dtml_methods, 'manage_main')
    manage = manage_main = manage_editDocument = manage_editForm

    security.declareProtected(change_proxy_roles, 'manage_proxyForm')
    manage_proxyForm = DTMLFile('dtml/documentProxy', globals())

    _size_changes = {
        'Bigger': (5, 5),
        'Smaller': (-5, -5),
        'Narrower': (0, -5),
        'Wider': (0, 5),
        'Taller': (5, 0),
        'Shorter': (-5, 0),
        }

    def _er(self, data, title, SUBMIT, dtpref_cols, dtpref_rows, REQUEST):
        dr, dc = self._size_changes[SUBMIT]
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
        REQUEST.other.update({"dtpref_cols": cols, "dtpref_rows": rows})
        return self.manage_main(self, REQUEST, title=title,
                                __str__=self.quotedHTML(data))

    security.declareProtected(change_dtml_methods, 'manage_edit')
    def manage_edit(self, data, title,
                    SUBMIT='Change',
                    dtpref_cols='100%',
                    dtpref_rows='20',
                    REQUEST=None):
        """ Replace contents with 'data', title with 'title'.

        The SUBMIT parameter is also used to change the size of the editing
        area on the default Document edit screen.  If the value is "Smaller",
        the rows and columns decrease by 5.  If the value is "Bigger", the
        rows and columns increase by 5.  If any other or no value is supplied,
        the data gets checked for DTML errors and is saved.
        """
        self._validateProxy(REQUEST)
        if self._size_changes.has_key(SUBMIT):
            return self._er(data, title,
                            SUBMIT, dtpref_cols, dtpref_rows, REQUEST)
        if self.wl_isLocked():
            raise ResourceLockedError('This item is locked via WebDAV')

        self.title = str(title)
        if isinstance(data, TaintedString):
            data = data.quoted()
        if not isinstance(data, basestring):
            data = data.read()
        self.munge(data)
        self.ZCacheable_invalidate()
        if REQUEST:
            message = "Saved changes."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)

    security.declareProtected(change_dtml_methods, 'manage_upload')
    def manage_upload(self, file='', REQUEST=None):
        """ Replace the contents of the document with the text in 'file'.
        """
        self._validateProxy(REQUEST)
        if self.wl_isLocked():
            raise ResourceLockedError('This DTML Method is locked via WebDAV')

        if type(file) is not type(''):
            if REQUEST and not file:
                raise ValueError('No file specified')
            file = file.read()

        self.munge(file)
        self.ZCacheable_invalidate()
        if REQUEST:
            message = "Saved changes."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)



    def manage_haveProxy(self, r):
        return r in self._proxy_roles

    def _validateProxy(self, request, roles=None):
        if roles is None:
            roles = self._proxy_roles
        if not roles:
            return
        user = u = getSecurityManager().getUser()
        user = user.allowed
        for r in roles:
            if r and not user(self, (r,)):
                user = None
                break

        if user is not None:
            return

        raise Forbidden(
            'You are not authorized to change <em>%s</em> because you '
            'do not have proxy roles.\n<!--%s, %s-->'
                % (self.__name__, u, roles))

    security.declareProtected(change_proxy_roles, 'manage_proxy')
    @requestmethod('POST')
    def manage_proxy(self, roles=(), REQUEST=None):
        "Change Proxy Roles"
        self._validateProxy(REQUEST, roles)
        self._validateProxy(REQUEST)
        self._proxy_roles = tuple(roles)
        self.ZCacheable_invalidate()
        if REQUEST:
            message = "Saved changes."
            return self.manage_proxyForm(self, REQUEST,
                                         manage_tabs_message=message)

    security.declareProtected(view_management_screens, 'PrincipiaSearchSource')
    def PrincipiaSearchSource(self):
        """ Support for searching - the document's contents are searched.
        """
        return self.read()

    security.declareProtected(view_management_screens, 'document_src')
    def document_src(self, REQUEST=None, RESPONSE=None):
        """ Return unprocessed document source.
        """
        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    ## Protocol handlers

    security.declareProtected(change_dtml_methods, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """ Handle FTP / HTTP PUT requests.
        """
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        body = REQUEST.get('BODY', '')
        self._validateProxy(REQUEST)
        self.munge(body)
        self.ZCacheable_invalidate()
        RESPONSE.setStatus(204)
        return RESPONSE

    security.declareProtected(ftp_access, 'manage_FTPstat')
    security.declareProtected(ftp_access, 'manage_FTPlist')

    security.declareProtected(ftp_access, 'manage_FTPget')
    def manage_FTPget(self):
        """ Get source for FTP download.
        """
        return self.read()


    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        return DTMLMethod.inheritedAttribute('manage_historyCompare')(
            self, rev1, rev2, REQUEST,
            historyComparisonResults = html_diff(rev1.read(), rev2.read()))

InitializeClass(DTMLMethod)

import re
token = "[a-zA-Z0-9!#$%&'*+\-.\\\\^_`|~]+"
hdr_start = re.compile(r'(%s):(.*)' % token).match


def decapitate(html, RESPONSE=None):
    headers = []
    spos  = 0
    eolen = 1
    while 1:
        m = hdr_start(html, spos)
        if not m:
            if html[spos:spos+2] == '\r\n':
                eolen = 2
                break
            if html[spos:spos+1] == '\n':
                eolen = 1
                break
            return html
        header = list(m.groups())
        headers.append(header)
        spos = m.end() + 1
        while spos < len(html) and html[spos] in ' \t':
            eol = html.find('\r\n', spos)
            if eol <> -1:
                eolen = 2
            else:
                eol = html.find( '\n', spos)
                if eol < 0:
                    return html
                eolen = 1
            header.append(html[spos:eol].strip())
            spos = eol + eolen
    if RESPONSE is not None:
        for header in headers:
            hkey = header.pop(0)
            RESPONSE.setHeader(hkey, ' '.join(header).strip())
    return html[spos + eolen:]


default_dm_html="""<html>
  <head><title><dtml-var title_or_id></title>
  </head>
  <body bgcolor="#FFFFFF">
<h2><dtml-var title_or_id> <dtml-var document_title></h2>
<p>
This is the <dtml-var document_id> Document
in the <dtml-var title_and_id> Folder.
</p>
  </body>
</html>"""

addForm=DTMLFile('dtml/methodAdd', globals())

def addDTMLMethod(self, id, title='', file='', REQUEST=None, submit=None):
    """Add a DTML Method object with the contents of file. If
    'file' is empty, default document text is used.
    """
    if type(file) is not type(''):
        file = file.read()
    if not file:
        file = default_dm_html
    id = str(id)
    title = str(title)
    ob = DTMLMethod(file, __name__=id)
    ob.title = title
    id = self._setObject(id, ob)
    if REQUEST is not None:
        try:
            u = self.DestinationURL()
        except:
            u = REQUEST['URL1']
        if submit == " Add and Edit ":
            u = "%s/%s" % (u, quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''
