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

__version__='$Revision: 1.14 $'[11:-2]

from Globals import HTML, HTMLFile, MessageDialog
from string import join,split,strip,rfind,atoi,lower
from SimpleItem import Item_w__name__, pretty_tb
from DocumentTemplate.DT_Util import cDocument
from PropertyManager import PropertyManager
from AccessControl.Role import RoleManager
from webdav.common import rfc1123_date
from urllib import quote
import regex, Globals, sys, Acquisition


class DTMLMethod(cDocument, HTML, Acquisition.Implicit, RoleManager,
                 Item_w__name__):
    """DTML Method objects are DocumentTemplate.HTML objects that act
       as methods of their containers."""
    meta_type='DTML Method'
    _proxy_roles=()
    index_html=None # Prevent accidental acquisition

    # Documents masquerade as functions:
    class func_code: pass
    func_code=func_code()
    func_code.co_varnames='self','REQUEST','RESPONSE'
    func_code.co_argcount=3

    manage_options=({'label':'Edit', 'action':'manage_main'},
                    {'label':'Upload', 'action':'manage_uploadForm'},
                    {'label':'View', 'action':''},
                    {'label':'Proxy', 'action':'manage_proxyForm'},
                    {'label':'Security', 'action':'manage_access'},
                   )
    __ac_permissions__=(
    ('View management screens',
     ('manage_editForm', 'manage', 'manage_main', 'manage_uploadForm',
      'document_src')),
    ('Change DTML Methods',     ('manage_edit', 'manage_upload', 'PUT')),
    ('Change proxy roles', ('manage_proxyForm', 'manage_proxy')),
    ('View', ('__call__', '')),
    ('FTP access', ('manage_FTPstat','manage_FTPget','manage_FTPlist')),
    )
    _state_name={'raw':1, 'globals':1, '__name__':1, '_vars':1,
                 '_proxy_roles':1, 'title':1}.has_key

    def __getstate__(self):
        r={}
        state_name=self._state_name
        for k, v in self.__dict__.items():
            if state_name(k) or k[-11:]=='_Permission' or k[-9:]=="__roles__":
                r[k]=v
        return r
   

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

        try: r=apply(HTML.__call__, (self, client, REQUEST), kw)
        except:
            if self.id()=='standard_error_message':
                raise sys.exc_type, sys.exc_value, sys.exc_traceback
            return self.raise_standardErrorMessage(client, REQUEST)
                
        if RESPONSE is None: return r
        RESPONSE.setHeader('Last-Modified', rfc1123_date(self._p_mtime))
        return decapitate(r, RESPONSE)

    def get_size(self):
        return len(self.raw)
    getSize=get_size
    
    def oldvalidate(self, inst, parent, name, value, md):
        if hasattr(value, '__roles__'):
            roles=value.__roles__
        elif inst is parent:
            return 1
        else:
            # if str(name)[:6]=='manage': return 0
            if hasattr(parent,'__roles__'):
                roles=parent.__roles__
            elif hasattr(parent, 'aq_acquire'):
                try: roles=parent.aq_acquire('__roles__')
                except AttributeError: return 0
            else: return 0
            value=parent
        if roles is None: return 1

        try: 
            if md.AUTHENTICATED_USER.hasRole(value, roles):
                return 1
        except AttributeError: pass

        for r in self._proxy_roles:
            if r in roles: return 1


        if inst is parent:
            raise 'Unauthorized', (
                'You are not authorized to access <em>%s</em>.' % name)

        return 0

    manage_editForm=HTMLFile('documentEdit', globals())
    manage_uploadForm=HTMLFile('documentUpload', globals())
    manage=manage_main=manage_editDocument=manage_editForm
    manage_proxyForm=HTMLFile('documentProxy', globals())

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
        e='Friday, 31-Dec-99 23:59:59 GMT'
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

        self.title=title
        if type(data) is not type(''): data=data.read()
        self.munge(data)
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def manage_upload(self,file='', REQUEST=None):
        """Replace the contents of the document with the text in file."""
        self._validateProxy(REQUEST)
        if type(file) is not type(''): file=file.read()
        self.munge(file)
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')



    def manage_haveProxy(self,r): return r in self._proxy_roles

    def _validateProxy(self, request, roles=None):
        if roles is None: roles=self._proxy_roles
        if not roles: return
        user=u=request.get('AUTHENTICATED_USER',None)
        if user is not None:
            user=user.hasRole
            for r in roles:
                if r and not user(None, (r,)):
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
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def PrincipiaSearchSource(self):
        "Support for searching - the document's contents are searched."
        return self.read()

    def document_src(self, REQUEST, RESPONSE):
        """Return unprocessed document source."""
        RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    ## Protocol handlers

    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests."""
        self.dav__init(REQUEST, RESPONSE)
        body=REQUEST.get('BODY', '')
        self._validateProxy(REQUEST)
        self.munge(body)
        RESPONSE.setStatus(204)
        return RESPONSE

    def manage_FTPget(self):
        "Get source for FTP download"
        return self.read()






def decapitate(html, RESPONSE=None,
               header_re=regex.compile(
                   '\(\('
                          '[^\n\0\- <>:]+:[^\n]*\n'
                      '\|'
                          '[ \t]+[^\0\- ][^\n]*\n'
                   '\)+\)[ \t]*\n\([\0-\377]+\)'
                   ),
               space_re=regex.compile('\([ \t]+\)'),
               name_re=regex.compile('\([^\0\- <>:]+\):\([^\n]*\)'),
               ):
    if header_re.match(html) < 0:
        return html
    headers, html = header_re.group(1,3)
    headers=split(headers,'\n')

    i=1
    while i < len(headers):
        if not headers[i]:
            del headers[i]
        elif space_re.match(headers[i]) >= 0:
            headers[i-1]="%s %s" % (headers[i-1],
                                    headers[i][len(space_re.group(1)):])
            del headers[i]
        else:
            i=i+1
    for i in range(len(headers)):
        if name_re.match(headers[i]) >= 0:
            k, v = name_re.group(1,2)
            v=strip(v)
        else:
            raise ValueError, 'Invalid Header (%d): %s ' % (i,headers[i])
        RESPONSE.setHeader(k,v)
    return html


default_dm_html="""<!--#var standard_html_header-->
<H2><!--#var title_or_id--> <!--#var document_title--></H2>
<P>This is the <!--#var document_id--> Document in 
the <!--#var title_and_id--> Folder.</P>
<!--#var standard_html_footer-->"""

addForm=HTMLFile('methodAdd', globals())

def addDTMLMethod(self, id, title='', file='', REQUEST=None, submit=None):
    """Add a DTML Method object with the contents of file. If
    'file' is empty, default document text is used.
    """
    if type(file) is not type(''): file=file.read()
    if not file: file=default_dm_html
    ob=DTMLMethod(file, __name__=id)
    ob.title=title
    id=self._setObject(id, ob)
    if REQUEST is not None:
        if hasattr(self, 'DestinationURL'): u=self.DestinationURL()
        else: u=REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''

