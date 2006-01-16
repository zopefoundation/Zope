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
"""DTML Document objects.

$Id$
"""
from ZPublisher.Converters import type_converters
from Globals import HTML, DTMLFile, MessageDialog
from zope.app.content_types import guess_content_type
from DTMLMethod import DTMLMethod, decapitate
from PropertyManager import PropertyManager
from webdav.common import rfc1123_date
from webdav.Lockable import ResourceLockedError
from webdav.WriteLockInterface import WriteLockInterface
from sgmllib import SGMLParser
from urllib import quote
import Globals
from AccessControl import getSecurityManager
from zExceptions.TracebackSupplement import PathTracebackSupplement

done='done'

_marker = []  # Create a new marker object.

class DTMLDocument(PropertyManager, DTMLMethod):
    """DTML Document objects are DocumentTemplate.HTML objects that act
       as methods whose 'self' is the DTML Document itself."""

    __implements__ = (WriteLockInterface,)
    meta_type='DTML Document'
    icon     ='p_/dtmldoc'

    manage_options=(
        DTMLMethod.manage_options[:2] +
        PropertyManager.manage_options +
        DTMLMethod.manage_options[2:]
        )
    
    ps = DTMLMethod.__ac_permissions__
    __ac_permissions__=(
        ps[0], ('Change DTML Documents', ps[1][1]), ps[2], ps[3], ps[4])
    del ps

    def manage_edit(self,data,title,SUBMIT='Change',dtpref_cols='100%',
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
            raise ResourceLockedError, (
                'This document has been locked via WebDAV.')

        self.title=str(title)
        if type(data) is not type(''): data=data.read()
        self.munge(data)
        self.ZCacheable_invalidate()
        if REQUEST:
            message="Content changed."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)

    def manage_upload(self,file='', REQUEST=None):
        """Replace the contents of the document with the text in file."""
        self._validateProxy(REQUEST)
        if self.wl_isLocked():
            raise ResourceLockedError, (
                'This document has been locked via WebDAV.')

        if type(file) is not type(''):
            if REQUEST and not file:
                raise ValueError, 'No file specified'
            file=file.read()

        self.munge(file)
        self.ZCacheable_invalidate()
        if REQUEST:
            message="Content uploaded."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)

    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """Render the document given a client object, REQUEST mapping,
        Response, and key word arguments."""

        if not self._cache_namespace_keys:
            data = self.ZCacheable_get(default=_marker)
            if data is not _marker:
                # Return cached results.
                return data

        __traceback_supplement__ = (PathTracebackSupplement, self)
        kw['document_id']   =self.getId()
        kw['document_title']=self.title
        if hasattr(self, 'aq_explicit'):
            bself=self.aq_explicit
        else: bself=self

        security=getSecurityManager()
        security.addContext(self)

        try:
            if client is None:
                # Called as subtemplate, so don't need error propigation!
                r=apply(HTML.__call__, (self, bself, REQUEST), kw)
                if RESPONSE is None: result = r
                else: result = decapitate(r, RESPONSE)
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(result)
                return result

            r=apply(HTML.__call__, (self, (client, bself), REQUEST), kw)
            if type(r) is not type('') or RESPONSE is None:
                if not self._cache_namespace_keys:
                    self.ZCacheable_set(r)
                return r

        finally: security.removeContext(self)

        have_key=RESPONSE.headers.has_key
        if not (have_key('content-type') or have_key('Content-Type')):
            if self.__dict__.has_key('content_type'):
                c=self.content_type
            else:
                c, e=guess_content_type(self.__name__, r)
            RESPONSE.setHeader('Content-Type', c)
        result = decapitate(r, RESPONSE)
        if not self._cache_namespace_keys:
            self.ZCacheable_set(result)
        return result


Globals.default__class_init__(DTMLDocument)


default_dd_html="""<dtml-var standard_html_header>
<h2><dtml-var title_or_id></h2>
<p>
This is the <dtml-var id> Document.
</p>
<dtml-var standard_html_footer>"""

addForm=DTMLFile('dtml/documentAdd', globals())

def addDTMLDocument(self, id, title='', file='', REQUEST=None, submit=None):
    """Add a DTML Document object with the contents of file. If
    'file' is empty, default document text is used.
    """
    if type(file) is not type(''): file=file.read()
    if not file: file=default_dd_html
    id=str(id)
    title=str(title)
    ob=DTMLDocument(file, __name__=id)
    ob.title=title
    id=self._setObject(id, ob)
    if REQUEST is not None:
        try: u=self.DestinationURL()
        except: u=REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''
