##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""DTML Method objects."""

__version__='$Revision: 1.70 $'[11:-2]

import History
from Globals import HTML, DTMLFile, MessageDialog
from string import join,split,strip,rfind,atoi,lower
from SimpleItem import Item_w__name__, pretty_tb
from OFS.content_types import guess_content_type
from PropertyManager import PropertyManager
from AccessControl.Role import RoleManager
from webdav.common import rfc1123_date
from webdav.Lockable import ResourceLockedError
from webdav.WriteLockInterface import WriteLockInterface
from ZDOM import ElementWithTitle
from DateTime.DateTime import DateTime
from urllib import quote
import  Globals, sys, Acquisition
from AccessControl import getSecurityManager
from AccessControl.DTML import RestrictedDTML
from Cache import Cacheable

_marker = []  # Create a new marker object.

class DTMLMethod(RestrictedDTML, HTML, Acquisition.Implicit, RoleManager,
                 ElementWithTitle, Item_w__name__,
                 History.Historical,
                 Cacheable,
                 ):
    """DTML Method objects are DocumentTemplate.HTML objects that act
       as methods of their containers."""
    meta_type='DTML Method'
    _proxy_roles=()
    index_html=None # Prevent accidental acquisition
    _cache_namespace_keys=()

    __implements__ = (WriteLockInterface,)

    # Documents masquerade as functions:
    class func_code: pass
    func_code=func_code()
    func_code.co_varnames='self','REQUEST','RESPONSE'
    func_code.co_argcount=3

    manage_options=(
        (
            {'label':'Edit', 'action':'manage_main',
             'help':('OFSP','DTML-DocumentOrMethod_Edit.stx')},
            #upload is deprecated
            #{'label':'Upload', 'action':'manage_uploadForm',
            # 'help':('OFSP','DTML-DocumentOrMethod_Upload.stx')},
            {'label':'View', 'action':'',
             'help':('OFSP','DTML-DocumentOrMethod_View.stx')},
            {'label':'Proxy', 'action':'manage_proxyForm',
             'help':('OFSP','DTML-DocumentOrMethod_Proxy.stx')},
            )
        +History.Historical.manage_options
        +RoleManager.manage_options
        +Item_w__name__.manage_options
        +Cacheable.manage_options
        )

    __ac_permissions__=(
    ('View management screens',
     ('document_src', 'PrincipiaSearchSource')),
    ('Change DTML Methods',
     ('manage_editForm', 'manage', 'manage_main',
      'manage_edit', 'manage_upload', 'PUT',
      'manage_historyCopy',
      'manage_beforeHistoryCopy', 'manage_afterHistoryCopy',
      'ZCacheable_configHTML', 'getCacheNamespaceKeys',
      'setCacheNamespaceKeys',
      )
     ),
    ('Change proxy roles', ('manage_proxyForm', 'manage_proxy')),
    ('View', ('__call__', 'get_size', '')),
    ('FTP access', ('manage_FTPstat','manage_FTPget','manage_FTPlist')),
    )

    # support a more reasonable default for content-type
    # for http HEAD requests.
    default_content_type='text/html'

    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """Render the document given a client object, REQUEST mapping,
        Response, and key word arguments."""

        if not self._cache_namespace_keys:
            data = self.ZCacheable_get(default=_marker)
            if data is not _marker:
                # Return cached results.
                return data
        
        kw['document_id']   =self.getId()
        kw['document_title']=self.title

        security=getSecurityManager()
        security.addContext(self)
        self.__dict__['validate'] = security.DTMLValidate
        try:
        
            if client is None:
                # Called as subtemplate, so don't need error propagation!
                r=apply(HTML.__call__, (self, client, REQUEST), kw)
                if RESPONSE is None: result = r
                else: result = decapitate(r, RESPONSE)
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(result)
                return result

            r=apply(HTML.__call__, (self, client, REQUEST), kw)
            if type(r) is not type('') or RESPONSE is None:
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(r)
                return r

        finally:
            security.removeContext(self)
            try: del self.__dict__['validate']
            except: pass

        have_key=RESPONSE.headers.has_key
        if not (have_key('content-type') or have_key('Content-Type')):
            if self.__dict__.has_key('content_type'):
                c=self.content_type
            else:
                c, e=guess_content_type(self.getId(), r)
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
                try: val = md[key]
                except: val = None
                kw[key] = val
            return self.ZCacheable_get(keywords=kw, default=default)
        return default

    def ZDocumentTemplate_afterRender(self, md, result):
        # Tries to set a cache value.
        if self._cache_namespace_keys:
            kw = {}
            for key in self._cache_namespace_keys:
                try: val = md[key]
                except: val = None
                kw[key] = val
            self.ZCacheable_set(result, keywords=kw)

    ZCacheable_configHTML = DTMLFile('dtml/cacheNamespaceKeys', globals())

    def getCacheNamespaceKeys(self):
        '''
        Returns the cacheNamespaceKeys.
        '''
        return self._cache_namespace_keys
        
    def setCacheNamespaceKeys(self, keys, REQUEST=None):
        '''
        Sets the list of names that should be looked up in the
        namespace to provide a cache key.
        '''
        ks = []
        for key in keys:
            key = strip(str(key))
            if key:
                ks.append(key)
        self._cache_namespace_keys = tuple(ks)
        if REQUEST is not None:
            return self.ZCacheable_manage(self, REQUEST)

    def get_size(self):
        return len(self.raw)

    # deprecated; use get_size!
    getSize=get_size

    manage_editForm=DTMLFile('dtml/documentEdit', globals())
    manage_editForm._setName('manage_editForm')

    # deprecated!
    manage_uploadForm=manage_editForm

    manage=manage_main=manage_editDocument=manage_editForm
    manage_proxyForm=DTMLFile('dtml/documentProxy', globals())

    _size_changes={
        'Bigger': (5,5),
        'Smaller': (-5,-5),
        'Narrower': (0,-5),
        'Wider': (0,5),
        'Taller': (5,0),
        'Shorter': (-5,0),
        }

    def _er(self,data,title,SUBMIT,dtpref_cols,dtpref_rows,REQUEST):
        dr,dc = self._size_changes[SUBMIT]
        
        rows=max(1,atoi(dtpref_rows)+dr)
        cols=max(40,atoi(dtpref_cols)+dc)
        e=(DateTime('GMT') + 365).rfc822()
        resp=REQUEST['RESPONSE']
        resp.setCookie('dtpref_rows',str(rows),path='/',expires=e)
        resp.setCookie('dtpref_cols',str(cols),path='/',expires=e)
        return self.manage_main(
            self,REQUEST,title=title,__str__=self.quotedHTML(data),
            dtpref_cols=cols,dtpref_rows=rows)

    def manage_edit(self,data,title,SUBMIT='Change',dtpref_cols='50',
                    dtpref_rows='20',REQUEST=None):
        """
        Replaces a Documents contents with Data, Title with Title.

        The SUBMIT parameter is also used to change the size of the editing
        area on the default Document edit screen.  If the value is "Smaller",
        the rows and columns decrease by 5.  If the value is "Bigger", the
        rows and columns increase by 5.  If any other or no value is supplied,
        the data gets checked for DTML errors and is saved.
        """
        self._validateProxy(REQUEST)
        if self._size_changes.has_key(SUBMIT):
            return self._er(data,title,SUBMIT,dtpref_cols,dtpref_rows,REQUEST)
        if self.wl_isLocked():
            raise ResourceLockedError, 'This DTML Method is locked via WebDAV'

        self.title=str(title)
        if type(data) is not type(''): data=data.read()
        self.munge(data)
        self.ZCacheable_invalidate()
        if REQUEST:
            message="Saved changes."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)

    def manage_upload(self,file='', REQUEST=None):
        """Replace the contents of the document with the text in file."""
        self._validateProxy(REQUEST)
        if self.wl_isLocked():
            raise ResourceLockedError, 'This DTML Method is locked via WebDAV'

        if type(file) is not type(''): file=file.read()
        self.munge(file)
        self.ZCacheable_invalidate()
        if REQUEST:
            message="Saved changes."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)



    def manage_haveProxy(self,r): return r in self._proxy_roles

    def _validateProxy(self, request, roles=None):
        if roles is None: roles=self._proxy_roles
        if not roles: return
        user=u=getSecurityManager().getUser()
        user=user.hasRole
        for r in roles:
            if r and not user(self, (r,)):
                user=None
                break

        if user is not None: return

        raise 'Forbidden', (
            'You are not authorized to change <em>%s</em> because you '
            'do not have proxy roles.\n<!--%s, %s-->' % (self.__name__, u, roles))
            

    def manage_proxy(self, roles=(), REQUEST=None):
        "Change Proxy Roles"
        self._validateProxy(REQUEST, roles)
        self._validateProxy(REQUEST)
        self._proxy_roles=tuple(roles)
        self.ZCacheable_invalidate()
        if REQUEST:
            message="Saved changes."
            return self.manage_proxyForm(self,REQUEST,manage_tabs_message=message)

    def PrincipiaSearchSource(self):
        "Support for searching - the document's contents are searched."
        return self.read()

    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return unprocessed document source."""
        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    ## Protocol handlers

    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests."""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        body=REQUEST.get('BODY', '')
        self._validateProxy(REQUEST)
        self.munge(body)
        self.ZCacheable_invalidate()
        RESPONSE.setStatus(204)
        return RESPONSE

    def manage_FTPget(self):
        "Get source for FTP download"
        return self.read()


    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        return DTMLMethod.inheritedAttribute('manage_historyCompare')(
            self, rev1, rev2, REQUEST,
            historyComparisonResults=History.html_diff(
                rev1.read(), rev2.read()
                ))

import re
from string import find, strip
token = "[a-zA-Z0-9!#$%&'*+\-.\\\\^_`|~]+"
hdr_start = re.compile(r'(%s):(.*)' % token).match

def decapitate(html, RESPONSE=None):
    headers = []
    spos = 0
    while 1:
        m = hdr_start(html, spos)
        if not m:
            if html[spos:spos+1] == '\n':
                break
            return html
        header = list(m.groups())
        headers.append(header)
        spos = m.end() + 1
        while spos < len(html) and html[spos] in ' \t':
            eol = find(html, '\n', spos)
            if eol < 0: return html
            header.append(strip(html[spos:eol]))
            spos = eol + 1
    if RESPONSE is not None:
        for header in headers:
            hkey = header.pop(0)
            RESPONSE.setHeader(hkey, ' '.join(header).strip())
    return html[spos + 1:]

default_dm_html="""<dtml-var standard_html_header>
<h2><dtml-var title_or_id> <dtml-var document_title></h2>
<p>
This is the <dtml-var document_id> Document 
in the <dtml-var title_and_id> Folder.
</p>
<dtml-var standard_html_footer>"""

addForm=DTMLFile('dtml/methodAdd', globals())

def addDTMLMethod(self, id, title='', file='', REQUEST=None, submit=None):
    """Add a DTML Method object with the contents of file. If
    'file' is empty, default document text is used.
    """
    if type(file) is not type(''): file=file.read()
    if not file: file=default_dm_html
    id=str(id)
    title=str(title)
    ob=DTMLMethod(file, __name__=id)
    ob.title=title
    id=self._setObject(id, ob)
    if REQUEST is not None:
        try: u=self.DestinationURL()
        except: u=REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''

