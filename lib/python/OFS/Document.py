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
"""Document object"""

__version__='$Revision: 1.71 $'[11:-2]

from Globals import HTML, HTMLFile, MessageDialog
from string import join,split,strip,rfind,atoi,lower
from AccessControl.Role import RoleManager
from SimpleItem import Item_w__name__, pretty_tb
from Acquisition import Explicit
import regex, Globals, sys
from DocumentTemplate.DT_Util import cDocument

class Document(cDocument, HTML, Explicit,
               RoleManager, Item_w__name__):
    """Document object. Basically a DocumentTemplate.HTML object
    which operates as a Principia object."""
    meta_type='Document'
    icon     ='p_/doc'
    _proxy_roles=()



    # Documents masquerade as functions:
    class func_code: pass
    func_code=func_code()
    func_code.co_varnames='self','REQUEST','RESPONSE'
    func_code.co_argcount=3

    manage_options=({'label':'Edit', 'action':'manage_main',
                     'target':'manage_main',
                    },
                    {'label':'Upload', 'action':'manage_uploadForm',
                     'target':'manage_main',
                    },
                    {'label':'View', 'action':'',
                     'target':'manage_main',
                    },
                    {'label':'Proxy', 'action':'manage_proxyForm',
                     'target':'manage_main',
                    },
                    {'label':'Security', 'action':'manage_access',
                     'target':'manage_main',
                    },
                   )

    __ac_permissions__=(
    ('View management screens',
     ['manage', 'manage_main','manage_editForm', 'manage_tabs',
      'manage_uploadForm']),
    ('Change permissions', ['manage_access']),
    ('Change Documents', ['manage_edit','manage_upload','PUT']),
    ('Change proxy roles', ['manage_proxyForm','manage_proxy']),
    ('View', ['__call__', '']),
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
        return decapitate(r, RESPONSE)

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
        self.munge(data)
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def manage_upload(self,file='', REQUEST=None):
        """
        replace the contents of the document with the text in file.
        """
        self._validateProxy(REQUEST)
        self.munge(file.read())
        if REQUEST: return MessageDialog(
                    title  ='Success!',
                    message='Your changes have been saved',
                    action ='manage_main')

    def PUT(self, BODY, REQUEST):
        """
    replaces the contents of the document with the BODY of an HTTP PUT request.
        """
        self._validateProxy(REQUEST)
        self.munge(BODY)
        return 'OK'

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


    def manage_FTPget(self):
        "Get source for FTP download"
        return self.read()

default_html="""<!--#var standard_html_header-->
<H2><!--#var title_or_id--> <!--#var document_title--></H2>
<P>This is the <!--#var document_id--> Document in 
the <!--#var title_and_id--> Folder.</P>
<!--#var standard_html_footer-->"""

manage_addDocumentForm=HTMLFile('documentAdd', globals())

def manage_addDocument(self, id, title='',file='', REQUEST=None, submit=None):
    """
    Add a Document object with the contents of file.

    If 'file' is empty or unspecified, the created documents contents are set
    to Principia's preset default.
    """
    if not file: file=default_html
    i=Document(file, __name__=id)
    i.title=title
    self._setObject(id,i)
    if REQUEST is not None:
        u=REQUEST['URL1']
        if submit==" Add and Edit ": u="%s/%s" % (u,id)
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''

class DocumentHandler:
    """Mixin class for objects that can contain Documents."""

    def documentIds(self):
        t=[]
        for i in self.objectMap():
            if i['meta_type']=='Document':
                t.append(i['id'])
        return t

    def documentValues(self):
        t=[]
        for i in self.objectMap():
            if i['meta_type']=='Document':
                t.append(getattr(self,i['id']))
        return t

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
    if header_re.match(html) < 0: return html

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

