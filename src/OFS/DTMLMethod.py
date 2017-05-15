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
import sys

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import change_proxy_roles
from AccessControl.Permissions import view as View  # NOQA
from AccessControl.Permissions import ftp_access
from AccessControl.requestmethod import requestmethod
from AccessControl.tainted import TaintedString
from Acquisition import Implicit
from DocumentTemplate.permissions import change_dtml_methods
from DocumentTemplate.security import RestrictedDTML
from six import binary_type
from six.moves.urllib.parse import quote
from zExceptions import Forbidden
from zExceptions import ResourceLockedError
from zExceptions.TracebackSupplement import PathTracebackSupplement
from zope.contenttype import guess_content_type

from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from OFS import bbb
from OFS.Cache import Cacheable
from OFS.role import RoleManager
from OFS.SimpleItem import Item_w__name__
from ZPublisher.Iterators import IStreamIterator

if sys.version_info >= (3, ):
    basestring = str

_marker = []  # Create a new marker object.


class Code(object):
    # Documents masquerade as functions:
    pass


class DTMLMethod(RestrictedDTML,
                 HTML,
                 Implicit,
                 RoleManager,
                 Item_w__name__,
                 Cacheable):
    """ DocumentTemplate.HTML objects that act as methods of their containers.
    """
    meta_type = 'DTML Method'
    _proxy_roles = ()
    index_html = None  # Prevent accidental acquisition
    _cache_namespace_keys = ()

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    __code__ = Code()
    __code__.co_varnames = 'self', 'REQUEST', 'RESPONSE'
    __code__.co_argcount = 3
    __defaults__ = None

    manage_options = ((
        {'label': 'Edit', 'action': 'manage_main'},
        {'label': 'Proxy', 'action': 'manage_proxyForm'},
    ) +
        RoleManager.manage_options +
        Item_w__name__.manage_options +
        Cacheable.manage_options
    )

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
                if (IStreamIterator.isImplementedBy(data) and
                        RESPONSE is not None):
                    # This is a stream iterator and we need to set some
                    # headers now before giving it to medusa
                    headers_get = RESPONSE.headers.get

                    if headers_get('content-length', None) is None:
                        RESPONSE.setHeader('content-length', len(data))

                    if (headers_get('content-type', None) is None and
                            headers_get('Content-type', None) is None):
                        ct = (self.__dict__.get('content_type') or
                              self.default_content_type)
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
                c, e = guess_content_type(self.getId(), r.encode('utf-8'))
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
        # Return the cacheNamespaceKeys.
        return self._cache_namespace_keys

    security.declareProtected(change_dtml_methods, 'setCacheNamespaceKeys')
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

    security.declareProtected(change_dtml_methods, 'manage_edit')
    def manage_edit(self, data, title, SUBMIT='Change', REQUEST=None):
        """ Replace contents with 'data', title with 'title'.
        """
        self._validateProxy(REQUEST)
        if self.wl_isLocked():
            raise ResourceLockedError('This item is locked.')

        self.title = str(title)
        if isinstance(data, TaintedString):
            data = data.quoted()

        if hasattr(data, 'read'):
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
            raise ResourceLockedError('This DTML Method is locked.')

        if not isinstance(file, binary_type):
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
            'do not have proxy roles.\n<!--%s, %s-->' % (
                self.__name__, u, roles))

    security.declareProtected(change_proxy_roles, 'manage_proxy')
    @requestmethod('POST')
    def manage_proxy(self, roles=(), REQUEST=None):
        "Change Proxy Roles"
        self._validateProxy(REQUEST, roles)
        self._validateProxy(REQUEST)
        self._proxy_roles = tuple(roles)
        if REQUEST:
            message = "Saved changes."
            return self.manage_proxyForm(self, REQUEST,
                                         manage_tabs_message=message)

    security.declareProtected(view_management_screens, 'PrincipiaSearchSource')
    def PrincipiaSearchSource(self):
        # Support for searching - the document's contents are searched.
        return self.read()

    security.declareProtected(view_management_screens, 'document_src')
    def document_src(self, REQUEST=None, RESPONSE=None):
        # Return unprocessed document source.
        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    if bbb.HAS_ZSERVER:
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

InitializeClass(DTMLMethod)

token = "[a-zA-Z0-9!#$%&'*+\-.\\\\^_`|~]+"
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
    if hasattr(file, 'read'):
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
        except Exception:
            u = REQUEST['URL1']
        if submit == " Add and Edit ":
            u = "%s/%s" % (u, quote(id))
        REQUEST.RESPONSE.redirect(u + '/manage_main')
    return ''
