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
"""DTML Document objects.
"""
from urllib import quote

from AccessControl import getSecurityManager
from AccessControl.class_init import InitializeClass
from App.special_dtml import DTMLFile
from App.special_dtml import HTML
from DocumentTemplate.permissions import change_dtml_methods
from DocumentTemplate.permissions import change_dtml_documents
from OFS.DTMLMethod import decapitate
from OFS.DTMLMethod import DTMLMethod
from OFS.PropertyManager import PropertyManager
from webdav.Lockable import ResourceLockedError
from zExceptions.TracebackSupplement import PathTracebackSupplement
from zope.contenttype import guess_content_type


done = 'done'

_marker = []  # Create a new marker object.

class DTMLDocument(PropertyManager, DTMLMethod):
    """ DocumentTemplate.HTML objects whose 'self' is the DTML object.
    """
    meta_type = 'DTML Document'
    icon ='p_/dtmldoc'

    manage_options = (
        DTMLMethod.manage_options[:2] +
        PropertyManager.manage_options +
        DTMLMethod.manage_options[2:]
        )

    # Replace change_dtml_methods by change_dtml_documents
    __ac_permissions__ = tuple([
        (perms[0] == change_dtml_methods)
            and (change_dtml_documents, perms[1])
            or perms
        for perms in DTMLMethod.__ac_permissions__])

    def manage_upload(self, file='', REQUEST=None):
        """ Replace the contents of the document with the text in 'file'.
        """
        self._validateProxy(REQUEST)
        if self.wl_isLocked():
            raise ResourceLockedError(
                'This document has been locked via WebDAV.')

        if type(file) is not str:
            if REQUEST and not file:
                raise ValueError, 'No file specified'
            file = file.read()

        self.munge(file)
        self.ZCacheable_invalidate()
        if REQUEST:
            message = "Content uploaded."
            return self.manage_main(self, REQUEST, manage_tabs_message=message)

    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """Render the document with the given client object.
        
        o If supplied, use REQUEST mapping, Response, and key word arguments.
        """
        if not self._cache_namespace_keys:
            data = self.ZCacheable_get(default=_marker)
            if data is not _marker:
                # Return cached results.
                return data

        __traceback_supplement__ = (PathTracebackSupplement, self)
        kw['document_id'] = self.getId()
        kw['document_title']  =self.title
        if hasattr(self, 'aq_explicit'):
            bself = self.aq_explicit
        else:
            bself = self

        security = getSecurityManager()
        security.addContext(self)

        try:
            if client is None:
                # Called as subtemplate, so don't need error propigation!
                r = apply(HTML.__call__, (self, bself, REQUEST), kw)
                if RESPONSE is None: result = r
                else: result = decapitate(r, RESPONSE)
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(result)
                return result

            r = apply(HTML.__call__, (self, (client, bself), REQUEST), kw)
            if type(r) is not str or RESPONSE is None:
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(r)
                return r

        finally: security.removeContext(self)

        have_key = RESPONSE.headers.has_key
        if not (have_key('content-type') or have_key('Content-Type')):
            if self.__dict__.has_key('content_type'):
                c = self.content_type
            else:
                c, e = guess_content_type(self.__name__, r)
            RESPONSE.setHeader('Content-Type', c)
        result = decapitate(r, RESPONSE)
        if not self._cache_namespace_keys:
            self.ZCacheable_set(result)
        return result


InitializeClass(DTMLDocument)


default_dd_html="""<html>
  <head><title><dtml-var title_or_id></title>
  </head>
  <body bgcolor="#FFFFFF">
    <h2><dtml-var title_or_id></h2>
<p>
This is the <dtml-var id> Document.
</p>
</body>
</html>"""

addForm=DTMLFile('dtml/documentAdd', globals())

def addDTMLDocument(self, id, title='', file='', REQUEST=None, submit=None):
    """Add a DTML Document object with the contents of file. If
    'file' is empty, default document text is used.
    """
    if type(file) is not str:
        file = file.read()
    if not file:
        file = default_dd_html
    id =str(id)
    title = str(title)
    ob = DTMLDocument(file, __name__=id)
    ob.title = title
    id = self._setObject(id, ob)
    if REQUEST is not None:
        try:
            u = self.DestinationURL()
        except:
            u = REQUEST['URL1']
        if submit == " Add and Edit ":
            u = "%s/%s" % (u,quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''
