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
"""DTML Document objects."""

__version__='$Revision: 1.22 $'[11:-2]
from DocumentTemplate.DT_Util import InstanceDict, TemplateDict
from ZPublisher.Converters import type_converters
from Globals import HTML, HTMLFile, MessageDialog
from OFS.content_types import guess_content_type
from DTMLMethod import DTMLMethod, decapitate
from PropertyManager import PropertyManager
from webdav.common import rfc1123_date
from sgmllib import SGMLParser
from string import find
from urllib import quote

done='done'


class DTMLDocument(DTMLMethod, PropertyManager):
    """DTML Document objects are DocumentTemplate.HTML objects that act
       as methods whose 'self' is the DTML Document itself."""

    meta_type='DTML Document'
    icon     ='p_/dtmldoc'

    manage_options=({'label':'Edit', 'action':'manage_main'},
                    {'label':'Upload', 'action':'manage_uploadForm'},
                    {'label':'Properties', 'action':'manage_propertiesForm'},
                    {'label':'View', 'action':''},
                    {'label':'Proxy', 'action':'manage_proxyForm'},
                    {'label':'Security', 'action':'manage_access'},
                   )

    __ac_permissions__=(
        ('Change DTML Documents',   ('manage_edit', 'manage_upload', 'PUT')),
    )

    def __getstate__(self):
        state={}
        props={}
        for id in self.propertyIds():
            props[id]=1
        prop_id=props.has_key
        state_name=self._state_name
        for k, v in self.__dict__.items():
            if state_name(k) or prop_id(k) or k[-11:]=='_Permission' \
               or k[-9:]=="__roles__" or k=='_properties':
                state[k]=v
        return state

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
        self.title=title
        if type(data) is not type(''): data=data.read()
        self.munge(data)
        if REQUEST:
            message="Content changed."
            return self.manage_main(self,REQUEST,manage_tabs_message=message)

    def manage_upload(self,file='', REQUEST=None):
        """Replace the contents of the document with the text in file."""
        self._validateProxy(REQUEST)
        if type(file) is not type(''): file=file.read()
        self.munge(file)
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """Render the document given a client object, REQUEST mapping,
        Response, and key word arguments."""
        kw['document_id']   =self.id
        kw['document_title']=self.title
        if hasattr(self, 'aq_explicit'): bself=self.aq_explicit
        else: bself=self
        if client is None:
            # Called as subtemplate, so don't need error propigation!
            r=apply(HTML.__call__, (self, bself, REQUEST), kw)
            if RESPONSE is None: return r
            return decapitate(r, RESPONSE)
        try: r=apply(HTML.__call__, (self, (client, bself), REQUEST), kw)
        except:
            if self.id()=='standard_error_message':
                raise sys.exc_type, sys.exc_value, sys.exc_traceback
            return self.raise_standardErrorMessage(client, REQUEST)
        if RESPONSE is None: return r
        RESPONSE.setHeader('Last-Modified', rfc1123_date(self._p_mtime))
        # Try to handle content types intelligently...
        c, e=guess_content_type(self.__name__, r)
        RESPONSE.setHeader('Content-Type', c)
        return decapitate(r, RESPONSE)





default_dd_html="""<!--#var standard_html_header-->
<h2><!--#var title_or_id--></h2>
<p>
This is the <!--#var id--> Document.
</p>
<!--#var standard_html_footer-->"""

addForm=HTMLFile('documentAdd', globals())

def addDTMLDocument(self, id, title='', file='', REQUEST=None, submit=None):
    """Add a DTML Document object with the contents of file. If
    'file' is empty, default document text is used.
    """
    if type(file) is not type(''): file=file.read()
    if not file: file=default_dd_html
    ob=DTMLDocument(file, __name__=id)
    ob.title=title
    id=self._setObject(id, ob)
    if REQUEST is not None:
        try: u=self.DestinationURL()
        except: u=REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''


