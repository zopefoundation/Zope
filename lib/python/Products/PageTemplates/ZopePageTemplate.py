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
"""Zope Page Template module

Zope object encapsulating a Page Template.
"""

__version__='$Revision: 1.13 $'[11:-2]

import os, AccessControl, Acquisition, sys
from Globals import DTMLFile, MessageDialog, package_home
from zLOG import LOG, ERROR, INFO
from OFS.SimpleItem import SimpleItem
from DateTime.DateTime import DateTime
from string import join, strip, rstrip, split, replace, lower
from Shared.DC.Scripts.Script import Script, BindingsUI
from Shared.DC.Scripts.Signature import FuncCode
from AccessControl import getSecurityManager
from OFS.History import Historical, html_diff
from OFS.Cache import Cacheable
from OFS.Traversable import Traversable
from OFS.PropertyManager import PropertyManager
from PageTemplate import PageTemplate

try:
    from webdav.Lockable import ResourceLockedError
    from webdav.WriteLockInterface import WriteLockInterface
    SUPPORTS_WEBDAV_LOCKS = 1
except ImportError:
    SUPPORTS_WEBDAV_LOCKS = 0

class ZopePageTemplate(Script, PageTemplate, Historical, Cacheable,
                       Traversable, PropertyManager):
    "Zope wrapper for Page Template using TAL, TALES, and METAL"
     
    if SUPPORTS_WEBDAV_LOCKS:
        __implements__ = (WriteLockInterface,)

    meta_type = 'Page Template'

    func_defaults = None
    func_code = FuncCode((), 0)

    _default_bindings = {'name_subpath': 'traverse_subpath'}
    _default_content_fn = os.path.join(package_home(globals()),
                                       'www', 'default.html')

    manage_options = (
        {'label':'Edit', 'action':'pt_editForm'},
        {'label':'Test', 'action':'ZScriptHTML_tryForm'},
        ) + PropertyManager.manage_options \
        + Historical.manage_options \
        + SimpleItem.manage_options \
        + Cacheable.manage_options

    _properties=({'id':'title', 'type': 'string'},
                 {'id':'content_type', 'type':'string'},
                 {'id':'expand', 'type':'boolean'},
                 )

    def __init__(self, id, text=None, content_type=None):
        self.id = str(id)
        self.ZBindings_edit(self._default_bindings)
        if text is None:
            text = open(self._default_content_fn).read()
        self.pt_edit(text, content_type)

    def _setPropValue(self, id, value):
        Cache._setPropValue(self, id, value)
        self.ZCacheable_invalidate()

    security = AccessControl.ClassSecurityInfo()

    security.declareObjectProtected('View')
    security.declareProtected('View', '__call__')

    security.declareProtected('View management screens',
      'pt_editForm', 'manage_main', 'read',
      'ZScriptHTML_tryForm', 'PrincipiaSearchSource',
      'document_src')

    security.declareProtected('Change Page Templates',
      'pt_editAction', 'pt_setTitle', 'pt_edit',
      'pt_upload', 'pt_changePrefs')
    def pt_editAction(self, REQUEST, title, text, content_type, expand):
        """Change the title and document."""
        if SUPPORTS_WEBDAV_LOCKS and self.wl_isLocked():
            raise ResourceLockedError, "File is locked via WebDAV"
        self.expand=expand
        self.pt_setTitle(title)
        self.pt_edit(text, content_type)
        REQUEST.set('text', self.read()) # May not equal 'text'!
        message = "Saved changes."
        if getattr(self, '_v_warnings', None):
            message = ("<strong>Warning:</strong> <i>%s</i>" 
                       % join(self._v_warnings, '<br>'))
        return self.pt_editForm(manage_tabs_message=message)

    def pt_setTitle(self, title):
        self._setPropValue('title', str(title))

    def pt_upload(self, REQUEST, file=''):
        """Replace the document with the text in file."""
        if SUPPORTS_WEBDAV_LOCKS and self.wl_isLocked():
            raise ResourceLockedError, "File is locked via WebDAV"
        if type(file) is not type(''): file = file.read()
        self.write(file)
        message = 'Saved changes.'
        return self.pt_editForm(manage_tabs_message=message)

    def pt_changePrefs(self, REQUEST, height=None, width=None,
                       dtpref_cols='50', dtpref_rows='20'):
        """Change editing preferences."""
        szchh = {'Taller': 1, 'Shorter': -1, None: 0}
        szchw = {'Wider': 5, 'Narrower': -5, None: 0}
        try: rows = int(height)
        except: rows = max(1, int(dtpref_rows) + szchh.get(height, 0))
        try: cols = int(width)
        except: cols = max(40, int(dtpref_cols) + szchw.get(width, 0))
        e = (DateTime('GMT') + 365).rfc822()
        setc = REQUEST['RESPONSE'].setCookie
        setc('dtpref_rows', str(rows), path='/', expires=e)
        setc('dtpref_cols', str(cols), path='/', expires=e)
        REQUEST.form.update({'dtpref_cols': cols, 'dtpref_rows': rows})
        return self.manage_main()

    def ZScriptHTML_tryParams(self):
        """Parameters to test the script with."""
        return []

    def manage_historyCompare(self, rev1, rev2, REQUEST,
                              historyComparisonResults=''):
        return ZopePageTemplate.inheritedAttribute(
            'manage_historyCompare')(
            self, rev1, rev2, REQUEST,
            historyComparisonResults=html_diff(rev1.read(), rev2.read()) )

    def pt_getContext(self):
        root = self.getPhysicalRoot()
        c = {'template': self,
             'here': self._getContext(),
             'container': self._getContainer(),
             'nothing': None,
             'options': {},
             'root': root,
             'request': getattr(root, 'REQUEST', None),
             'modules': SecureModuleImporter,
             }
        return c

    def write(self, text):
        self.ZCacheable_invalidate()
        ZopePageTemplate.inheritedAttribute('write')(self, text)

    def _exec(self, bound_names, args, kw):
        """Call a Page Template"""
        if not kw.has_key('args'):
            kw['args'] = args
        bound_names['options'] = kw

        try:
            self.REQUEST.RESPONSE.setHeader('content-type',
                                            self.content_type)
        except AttributeError: pass

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
            result = self.pt_render(extra_context=bound_names)
            if keyset is not None:
                # Store the result in the cache.
                self.ZCacheable_set(result, keywords=keyset)
            return result
        finally:
            security.removeContext(self)

    security.declareProtected('Change Page Templates',
      'PUT', 'manage_FTPput', 'write',
      'manage_historyCopy',
      'manage_beforeHistoryCopy', 'manage_afterHistoryCopy')

    def PUT(self, REQUEST, RESPONSE):
        """ Handle HTTP PUT requests """
        self.dav__init(REQUEST, RESPONSE)
        if SUPPORTS_WEBDAV_LOCKS:
            self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        self.write(REQUEST.get('BODY', ''))
        RESPONSE.setStatus(204)
        return RESPONSE        

    manage_FTPput = PUT

    def manage_FTPget(self):
        "Get source for FTP download"
        self.REQUEST.RESPONSE.setHeader('Content-Type', self.content_type)
        return self.read()

    def get_size(self):
        return len(self.read())
    getSize = get_size

    def PrincipiaSearchSource(self):
        "Support for searching - the document's contents are searched."
        return self.read()

    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return expanded document source."""

        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', self.content_type)
        return self.read()

    def __setstate__(self, state):
        ZopePageTemplate.inheritedAttribute('__setstate__')(self, state)
        self._cook()

    if not SUPPORTS_WEBDAV_LOCKS:
        def wl_isLocked(self):
            return 0

class Src(Acquisition.Explicit):
    " "

    PUT = document_src = Acquisition.Acquired
    index_html = None
    
    def __call__(self, REQUEST, RESPONSE):
        " "
        return self.document_src(REQUEST, RESPONSE)

d = ZopePageTemplate.__dict__
d['source.xml'] = d['source.html'] = Src()

from Expressions import _SecureModuleImporter
SecureModuleImporter = _SecureModuleImporter()

# Product registration and Add support
from urllib import quote

def manage_addPageTemplate(self, id, title=None, text=None,
                           REQUEST=None, submit=None):
    "Add a Page Template with optional file content."

    id = str(id)
    if REQUEST is None:
        self._setObject(id, ZopePageTemplate(id, text))
        ob = getattr(self, id)
        if title:
            ob.pt_setTitle(title)
        return ob
    else:
        file = REQUEST.form.get('file')
        headers = getattr(file, 'headers', None)
        if headers is None or not file.filename:
            zpt = ZopePageTemplate(id)
        else:
            zpt = ZopePageTemplate(id, file, headers.get('content_type'))
            
        self._setObject(id, zpt)

        try: u = self.DestinationURL()
        except: u = REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''

#manage_addPageTemplateForm = DTMLFile('dtml/ptAdd', globals())

def initialize(context):
    from PageTemplateFile import PageTemplateFile
    manage_addPageTemplateForm = PageTemplateFile('www/ptAdd', globals())
    _editForm = PageTemplateFile('www/ptEdit', globals())
    ZopePageTemplate.manage = _editForm
    ZopePageTemplate.manage_main = _editForm
    ZopePageTemplate.pt_editForm = _editForm
    context.registerClass(
        ZopePageTemplate,
        permission='Add Page Templates',
        constructors=(manage_addPageTemplateForm,
                      manage_addPageTemplate),
        icon='www/zpt.gif',
        )
    context.registerHelp()
    context.registerHelpTitle('Zope Help')

