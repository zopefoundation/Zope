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
import re
from urllib.parse import quote

from AccessControl import getSecurityManager
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import change_proxy_roles  # NOQA
from AccessControl.Permissions import view as View
from AccessControl.Permissions import view_management_screens
from AccessControl.requestmethod import requestmethod
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.tainted import TaintedString
from Acquisition import Implicit
from App.special_dtml import HTML
from App.special_dtml import DTMLFile
from DocumentTemplate.DT_Util import ParseError
from DocumentTemplate.permissions import change_dtml_methods
from DocumentTemplate.security import RestrictedDTML
from OFS.Cache import Cacheable
from OFS.History import Historical
from OFS.History import html_diff
from OFS.role import RoleManager
from OFS.SimpleItem import Item_w__name__
from OFS.SimpleItem import PathReprProvider
from zExceptions import Forbidden
from zExceptions import ResourceLockedError
from zExceptions.TracebackSupplement import PathTracebackSupplement
from zope.contenttype import guess_content_type
from ZPublisher.HTTPRequest import default_encoding
from ZPublisher.Iterators import IStreamIterator


_marker = []  # Create a new marker object.


class Code:
    # Documents masquerade as functions:
    pass


class DTMLMethod(
    PathReprProvider,
    RestrictedDTML,
    HTML,
    Implicit,
    RoleManager,
    Item_w__name__,
    Historical,
    Cacheable
):
    """ DocumentTemplate.HTML objects that act as methods of their containers.
    """
    meta_type = 'DTML Method'
    zmi_icon = 'far fa-file-alt'
    _proxy_roles = ()
    index_html = None  # Prevent accidental acquisition
    _cache_namespace_keys = ()
    _locked_error_text = 'This DTML Method is locked.'

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    __code__ = Code()
    __code__.co_varnames = 'self', 'REQUEST', 'RESPONSE'
    __code__.co_argcount = 3
    __defaults__ = None

    manage_options = ((
        {
            'label': 'Edit',
            'action': 'manage_main',
        },
        {
            'label': 'View',
            'action': '',
        },
        {
            'label': 'Proxy',
            'action': 'manage_proxyForm',
        },
    ) + Historical.manage_options
      + RoleManager.manage_options
      + Item_w__name__.manage_options
      + Cacheable.manage_options
    )

    # Careful in permission changes--used by DTMLDocument!
    security.declareProtected(change_dtml_methods,  # NOQA: D001
                              'manage_historyCopy')
    security.declareProtected(change_dtml_methods,  # NOQA: D001
                              'manage_beforeHistoryCopy')
    security.declareProtected(change_dtml_methods,  # NOQA: D001
                              'manage_afterHistoryCopy')

    # More reasonable default for content-type for http HEAD requests.
    default_content_type = 'text/html'

    def errQuote(self, s):
        # Quoting is done when rendering the error in the template.
        return s

    @security.protected(View)
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
                if IStreamIterator.isImplementedBy(data) and \
                   RESPONSE is not None:
                    # This is a stream iterator and we need to set some
                    # headers now before giving it to medusa
                    headers_get = RESPONSE.headers.get

                    if headers_get('content-length', None) is None:
                        RESPONSE.setHeader('content-length', len(data))

                    if headers_get('content-type', None) is None and \
                       headers_get('Content-type', None) is None:
                        ct = (self.__dict__.get('content_type')
                              or self.default_content_type)
                        RESPONSE.setHeader('content-type', ct)

                # Return cached results.
                return data

        __traceback_supplement__ = (PathTracebackSupplement, self)
        kw['document_id'] = self.getId()
        kw['document_title'] = self.title

        security = getSecurityManager()
        security.addContext(self)
        if 'validate' in self.__dict__:
            first_time_through = 0
        else:
            self.__dict__['validate'] = security.DTMLValidate
            first_time_through = 1
        try:

            if client is None:
                # Called as subtemplate, so don't need error propagation!
                r = HTML.__call__(self, client, REQUEST, **kw)
                if RESPONSE is None:
                    result = r
                else:
                    result = decapitate(r, RESPONSE)
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(result)
                return result

            r = HTML.__call__(self, client, REQUEST, **kw)

            if RESPONSE is None or not isinstance(r, str):
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(r)
                return r

        finally:
            security.removeContext(self)
            if first_time_through:
                del self.__dict__['validate']

        have_key = RESPONSE.headers.__contains__
        if not (have_key('content-type') or have_key('Content-Type')):
            if 'content_type' in self.__dict__:
                c = self.content_type
            else:
                encoding = getattr(self, 'encoding', default_encoding)
                c, e = guess_content_type(self.getId(), r.encode(encoding))
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
                except Exception:
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
                except Exception:
                    val = None
                kw[key] = val
            self.ZCacheable_set(result, keywords=kw)

    security.declareProtected(change_dtml_methods, 'ZCacheable_configHTML')  # NOQA: D001,E501
    ZCacheable_configHTML = DTMLFile('dtml/cacheNamespaceKeys', globals())

    @security.protected(change_dtml_methods)
    def getCacheNamespaceKeys(self):
        # Return the cacheNamespaceKeys.
        return self._cache_namespace_keys

    @security.protected(change_dtml_methods)
    def setCacheNamespaceKeys(self, keys, REQUEST=None):
        # Set the list of names looked up to provide a cache key.
        ks = []
        for key in keys:
            key = str(key).strip()
            if key:
                ks.append(key)
        self._cache_namespace_keys = tuple(ks)

        if REQUEST is not None:
            return self.ZCacheable_manage(self, REQUEST)

    @security.protected(View)
    def get_size(self):
        return len(self.raw)

    # deprecated; use get_size!
    getSize = get_size

    security.declareProtected(change_dtml_methods, 'manage')  # NOQA: D001

    security.declareProtected(change_dtml_methods, 'manage_editForm')  # NOQA: D001,E501
    manage_editForm = DTMLFile('dtml/documentEdit', globals())
    manage_editForm._setName('manage_editForm')

    # deprecated!
    manage_uploadForm = manage_editForm

    security.declareProtected(change_dtml_methods, 'manage_main')  # NOQA: D001
    manage = manage_main = manage_editDocument = manage_editForm

    security.declareProtected(change_proxy_roles, 'manage_proxyForm')  # NOQA: D001,E501
    manage_proxyForm = DTMLFile('dtml/documentProxy', globals())

    @security.protected(change_dtml_methods)
    def manage_edit(self, data, title, SUBMIT='Change', REQUEST=None):
        """ Replace contents with 'data', title with 'title'.
        """
        self._validateProxy()
        if self.wl_isLocked():
            raise ResourceLockedError(self._locked_error_text)

        self.title = str(title)
        if isinstance(data, TaintedString):
            data = data.quoted()

        if hasattr(data, 'read'):
            data = data.read()
        try:
            self.munge(data)
        except ParseError as e:
            if REQUEST:
                return self.manage_main(
                    self, REQUEST, manage_tabs_message=e,
                    manage_tabs_type='warning')
            else:
                raise
        self.ZCacheable_invalidate()
        if REQUEST:
            message = "Saved changes."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)

    @security.protected(change_dtml_methods)
    def manage_upload(self, file='', REQUEST=None):
        """ Replace the contents of the document with the text in 'file'.

        Store `file` as a native `str`.
        """
        self._validateProxy()
        if self.wl_isLocked():
            if REQUEST is not None:
                return self.manage_main(
                    self, REQUEST,
                    manage_tabs_message=self._locked_error_text,
                    manage_tabs_type='warning')
            raise ResourceLockedError(self._locked_error_text)

        if REQUEST is not None and not file:
            return self.manage_main(
                self, REQUEST,
                manage_tabs_message='No file specified',
                manage_tabs_type='warning')

        self.munge(safe_file_data(file))
        self.ZCacheable_invalidate()
        if REQUEST is not None:
            message = "Content uploaded."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)

    def manage_haveProxy(self, r):
        return r in self._proxy_roles

    def _validateProxy(self, roles=None):
        if roles is None:
            roles = self._proxy_roles
        if not roles:
            return
        user = getSecurityManager().getUser()
        if user is not None and user.allowed(self, roles):
            return
        raise Forbidden(
            'You are not authorized to change <em>%s</em> because you '
            'do not have proxy roles.\n<!--%s, %s-->' % (
                self.__name__, user, roles))

    @security.protected(change_proxy_roles)
    @requestmethod('POST')
    def manage_proxy(self, roles=(), REQUEST=None):
        """Change Proxy Roles"""
        user = getSecurityManager().getUser()
        if 'Manager' not in user.getRolesInContext(self):
            self._validateProxy(roles)
            self._validateProxy()
        self.ZCacheable_invalidate()
        self._proxy_roles = tuple(roles)
        if REQUEST:
            message = "Saved changes."
            return self.manage_proxyForm(self, REQUEST,
                                         manage_tabs_message=message)

    @security.protected(view_management_screens)
    def PrincipiaSearchSource(self):
        # Support for searching - the document's contents are searched.
        return self.read()

    @security.protected(view_management_screens)
    def document_src(self, REQUEST=None, RESPONSE=None):
        # Return unprocessed document source.
        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    @security.protected(change_dtml_methods)
    def PUT(self, REQUEST, RESPONSE):
        """ Handle HTTP PUT requests.
        """
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        body = safe_file_data(REQUEST.get('BODY', ''))
        self._validateProxy()
        self.munge(body)
        self.ZCacheable_invalidate()
        RESPONSE.setStatus(204)
        return RESPONSE

    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        return DTMLMethod.inheritedAttribute('manage_historyCompare')(
            self, rev1, rev2, REQUEST,
            historyComparisonResults=html_diff(rev1.read(), rev2.read()))


InitializeClass(DTMLMethod)


token = r"[a-zA-Z0-9!#$%&'*+\-.\\\\^_`|~]+"
hdr_start = re.compile(r'(%s):(.*)' % token).match


def decapitate(html, RESPONSE=None):
    headers = []
    spos = 0
    eolen = 1
    while 1:
        m = hdr_start(html, spos)
        if not m:
            if html[spos:spos + 2] == '\r\n':
                eolen = 2
                break
            if html[spos:spos + 1] == '\n':
                eolen = 1
                break
            return html
        header = list(m.groups())
        headers.append(header)
        spos = m.end() + 1
        while spos < len(html) and html[spos] in ' \t':
            eol = html.find('\r\n', spos)
            if eol != -1:
                eolen = 2
            else:
                eol = html.find('\n', spos)
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


def safe_file_data(data):
    # Helper to convert upload file content into a safe value for saving
    if hasattr(data, 'read'):
        data = data.read()
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return data


default_dm_html = """\
<!DOCTYPE html>
<html>
  <head>
    <title><dtml-var title_or_id></title>
    <meta charset="utf-8" />
  </head>
  <body>
    <h2><dtml-var title_or_id> <dtml-var document_title></h2>
    <p>
    This is the <dtml-var document_id> Document
    in the <dtml-var title_and_id> Folder.
    </p>
  </body>
</html>"""

addForm = DTMLFile('dtml/methodAdd', globals())


def addDTMLMethod(self, id, title='', file='', REQUEST=None, submit=None):
    """Add a DTML Method object with the contents of file. If
    'file' is empty, default document text is used.
    """
    data = safe_file_data(file)
    if not data:
        data = default_dm_html
    id = str(id)
    title = str(title)
    ob = DTMLMethod(data, __name__=id)
    ob.title = title
    id = self._setObject(id, ob)
    if REQUEST is not None:
        try:
            u = self.DestinationURL()
        except Exception:
            u = REQUEST['URL1']
        if submit == "Add and Edit":
            u = f"{u}/{quote(id)}"
        REQUEST.RESPONSE.redirect(u + '/manage_main')
    return ''
