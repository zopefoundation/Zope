##############################################################################
# 
# Zope Public License (ZPL) Version 0.9.6
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
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
# 3. Any use, including use of the Zope software to operate a website,
#    must either comply with the terms described below under
#    "Attribution" or alternatively secure a separate license from
#    Digital Creations.  Digital Creations will not unreasonably
#    deny such a separate license in the event that the request
#    explains in detail a valid reason for withholding attribution.
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
# Attribution
# 
#   Individuals or organizations using this software as a web
#   site ("the web site") must provide attribution by placing
#   the accompanying "button" on the website's main entry
#   point.  By default, the button links to a "credits page"
#   on the Digital Creations' web site. The "credits page" may
#   be copied to "the web site" in order to add other credits,
#   or keep users "on site". In that case, the "button" link
#   may be updated to point to the "on site" "credits page".
#   In cases where this placement of attribution is not
#   feasible, a separate arrangment must be concluded with
#   Digital Creations.  Those using the software for purposes
#   other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.  Where
#   attribution is not possible, or is considered to be
#   onerous for some other reason, a request should be made to
#   Digital Creations to waive this requirement in writing.
#   As stated above, for valid requests, Digital Creations
#   will not unreasonably deny such requests.
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""DTML Document objects."""

__version__='$Revision: 1.5 $'[11:-2]
from DocumentTemplate.DT_Util import InstanceDict, TemplateDict
from ZPublisher.Converters import type_converters
from Globals import HTML, HTMLFile, MessageDialog
from DTMLMethod import DTMLMethod, decapitate
from PropertyManager import PropertyManager
from sgmllib import SGMLParser
from string import find

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
    ('View management screens', ['manage', 'manage_main', 'manage_editForm',
                                 'manage_tabs', 'manage_uploadForm']),
    ('Change permissions',      ['manage_access']),
    ('Change DTML Documents',   ['manage_edit', 'manage_upload', 'PUT']),
    ('Change proxy roles', ['manage_proxyForm', 'manage_proxy']),
    ('Manage properties',  ['manage_addProperty', 'manage_editProperties',
                            'manage_delProperties','manage_changeProperties']),
    ('View', ['__call__', '']),
    ('FTP access', ['manage_FTPstat','manage_FTPget','manage_FTPlist']),
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

    def on_update(self):
        # This is just experimental!        
        if 1: return
        try:    meta=hp(self.raw)
        except: return
        for key, val in meta.metavars.items():
            if not self.hasProperty(key):
                t=find(key, ':')
                if t > 0:
                    type=key[t+1:]
                    key=key[:t]
                else: type='string'
                if type_converters.has_key(type):
                    val=type_converters[type](val)
                self._setProperty(key, val, type)
        if not self.title:
            self.title=meta.title

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
        self.munge(data)
        self.on_update()
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def manage_upload(self,file='', REQUEST=None):
        """Replace the contents of the document with the text in file."""
        self._validateProxy(REQUEST)
        data=file.read()
        self.munge(data)
        self.on_update()
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def PUT(self, BODY, REQUEST, RESPONSE):
        """Handle HTTP PUT requests."""
        self._validateProxy(REQUEST)
        self.munge(BODY)
        self.on_update()
        RESPONSE.setStatus(204)
        return RESPONSE

    def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
        """Render the document given a client object, REQUEST mapping,
        Response, and key word arguments."""
        kw['document_id']   =self.id
        kw['document_title']=self.title
        if client is None:
            # Called as subtemplate, so don't need error propigation!
            r=apply(HTML.__call__, (self, client, REQUEST), kw)
            if RESPONSE is None: return r
            return decapitate(r, RESPONSE)
        try: r=apply(HTML.__call__, (self, (client, self), REQUEST), kw)
        except:
            if self.id()=='standard_error_message':
                raise sys.exc_type, sys.exc_value, sys.exc_traceback
            return self.raise_standardErrorMessage(client, REQUEST)
        if RESPONSE is None: return r
        return decapitate(r, RESPONSE)



class hp(SGMLParser):

    from htmlentitydefs import entitydefs

    def __init__(self, data):
        SGMLParser.__init__(self, verbose=0)
        self.metavars={}
        self.headers={}
        self.data=None
        self.title=''
        try: self.feed(data)
        except done: pass
        
    def handle_data(self, data):
        if self.data is not None:
            self.data=self.data + data
        else: pass

    def save_bgn(self):
        self.data=''

    def save_end(self):
        data=self.data
        self.data=None
        return data
    
    def start_head(self, attrs):
        pass
    
    def end_head(self):
        # avoid parsing whole file!
        raise done, done

    def start_title(self, attrs):
        self.save_bgn()

    def end_title(self):
        self.title=self.save_end()

    def do_meta(self, attrs):
        dict={}
        for key, val in attrs:
            dict[key]=val
        if dict.has_key('http-equiv'):
            self.headers[dict['http-equiv']]=dict['content']
        elif dict.has_key('name'):
            self.metavars[dict['name']]=dict['content']



default_dd_html="""<!--#var standard_html_header-->
<h2><!--#var title_or_id--></h2>
<p>
This is the <!--#var id--> Document.
</p>
<!--#var standard_html_footer-->"""

addForm=HTMLFile('documentAdd', globals())

def add(self, id, title='', file='', REQUEST=None, submit=None):
    """Add a DTML Document object with the contents of file. If
    'file' is empty, default document text is used.
    """
    if not file: file=default_dd_html
    ob=DTMLDocument(file, __name__=id)
    ob.title=title
    ob.on_update()
    self._setObject(id, ob)
    if REQUEST is not None:
        u=REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,id)
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''
