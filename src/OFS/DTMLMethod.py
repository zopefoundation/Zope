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
from urllib import quote

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import view as View  # NOQA
from AccessControl.Permissions import ftp_access
from AccessControl.tainted import TaintedString
from Acquisition import Implicit
from DocumentTemplate.permissions import change_dtml_methods
from DocumentTemplate.security import RestrictedDTML
from zExceptions import Redirect
from zExceptions import ResourceLockedError
from zExceptions.TracebackSupplement import PathTracebackSupplement
from zope.contenttype import guess_content_type

from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from OFS import bbb
from OFS.Cache import Cacheable
from OFS.role import RoleManager
from OFS.SimpleItem import Item_w__name__

if sys.version_info >= (3, ):
    basestring = str

_marker = []  # Create a new marker object.


class DTMLMethod(RestrictedDTML,
                 HTML,
                 Implicit,
                 RoleManager,
                 Cacheable,
                 Item_w__name__):
    """ DocumentTemplate.HTML objects that act as methods of their containers.
    """
    meta_type = 'DTML Method'
    index_html = None  # Prevent accidental acquisition

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    class func_code(object):
        # Documents masquerade as functions:
        pass

    func_code = __code__ = func_code()
    func_code.co_varnames = 'self', 'REQUEST', 'RESPONSE'
    func_code.co_argcount = 3

    manage_options = ((
        {'label': 'Edit', 'action': 'manage_main'},
    ) +
        RoleManager.manage_options +
        Item_w__name__.manage_options
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
                return result

            r = HTML.__call__(self, client, REQUEST, **kw)
            if RESPONSE is None or not isinstance(r, str):
                return r

        finally:
            security.removeContext(self)
            if first_time_through:
                del self.__dict__['validate']

        have_key = RESPONSE.headers.has_key
        if not (have_key('content-type') or have_key('Content-Type')):
            if 'content_type' in self.__dict__:
                c = self.content_type
            else:
                c, e = guess_content_type(self.getId(), r)
            RESPONSE.setHeader('Content-Type', c)
        result = decapitate(r, RESPONSE)
        return result

    def validate(self, inst, parent, name, value, md=None):
        return getSecurityManager().validate(inst, parent, name, value)

    def ZDocumentTemplate_beforeRender(self, md, default):
        return default

    def ZDocumentTemplate_afterRender(self, md, result):
        pass

    security.declareProtected(change_dtml_methods, 'getCacheNamespaceKeys')
    def getCacheNamespaceKeys(self):
        return ()

    security.declareProtected(change_dtml_methods, 'setCacheNamespaceKeys')
    def setCacheNamespaceKeys(self, keys, REQUEST=None):
        pass

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

    security.declareProtected(change_dtml_methods, 'manage_edit')
    def manage_edit(self, data, title, SUBMIT='Change', REQUEST=None):
        """ Replace contents with 'data', title with 'title'.
        """
        if self.wl_isLocked():
            raise ResourceLockedError('This item is locked.')

        self.title = str(title)
        if isinstance(data, TaintedString):
            data = data.quoted()
        if not isinstance(data, basestring):
            data = data.read()
        self.munge(data)
        if REQUEST:
            message = "Saved changes."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)

    security.declareProtected(change_dtml_methods, 'manage_upload')
    def manage_upload(self, file='', REQUEST=None):
        """ Replace the contents of the document with the text in 'file'.
        """
        if self.wl_isLocked():
            raise ResourceLockedError('This DTML Method is locked.')

        if not isinstance(file, str):
            if REQUEST and not file:
                raise ValueError('No file specified')
            file = file.read()

        self.munge(file)
        if REQUEST:
            message = "Saved changes."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)

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
            self.munge(body)
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
    if not isinstance(file, str):
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
        raise Redirect(u + '/manage_main')
    return ''
