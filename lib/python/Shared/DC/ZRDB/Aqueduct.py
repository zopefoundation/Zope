##############################################################################
#
# Zope Public License (ZPL) Version 0.9.5
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
#   Individuals or organizations using this software as a web site must
#   provide attribution by placing the accompanying "button" and a link
#   to the accompanying "credits page" on the website's main entry
#   point.  In cases where this placement of attribution is not
#   feasible, a separate arrangment must be concluded with Digital
#   Creations.  Those using the software for purposes other than web
#   sites must provide a corresponding attribution in locations that
#   include a copyright using a manner best suited to the application
#   environment.  Where attribution is not possible, or is considered
#   to be onerous for some other reason, a request should be made to
#   Digital Creations to waive this requirement in writing.  As stated
#   above, for valid requests, Digital Creations will not unreasonably
#   deny such requests.
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__doc__='''Shared classes and functions

$Id: Aqueduct.py,v 1.27 1998/12/16 15:25:48 jim Exp $'''
__version__='$Revision: 1.27 $'[11:-2]

import Globals, os
from Globals import HTMLFile, Persistent
import DocumentTemplate, DateTime, regex, regsub, string, rotor
import binascii, Acquisition
DateTime.now=DateTime.DateTime
from cStringIO import StringIO
from OFS import SimpleItem
from AccessControl.Role import RoleManager
from DocumentTemplate import HTML

from string import strip

dtml_dir=Globals.package_home(globals())

InvalidParameter='Invalid Parameter'

class BaseQuery(Persistent, SimpleItem.Item, Acquisition.Implicit, RoleManager):

    def query_year(self): return self.query_date.year()
    def query_month(self): return self.query_date.month()
    def query_day(self): return self.query_date.day()
    query_date=DateTime.now()
    manage_options=()

    def quoted_input(self): return quotedHTML(self.input_src)
    def quoted_report(self): return quotedHTML(self.report_src)

    MissingArgumentError='Bad Request'

    def _convert(self): self._arg=parse(self.arguments_src)

    def _argdata(self, REQUEST):

        r={}

        try: args=self._arg
        except:
            self._convert()
            args=self._arg

        id=self.id
        missing=[]

        for name in args.keys():
            idname="%s/%s" % (id, name)
            try:
                r[name]=REQUEST[idname]
            except:
                try: r[name]=REQUEST[name]
                except:
                    arg=args[name]
                    try: r[name]=arg['default']
                    except:
                        try:
                            if not arg['optional']: missing.append(name)
                        except: missing.append(name)
                    
        if missing:
            raise self.MissingArgumentError, missing

        return r

    _col=None
    _arg={}

class Searchable(BaseQuery):

    def _searchable_arguments(self):

        try: return self._arg
        except:
            self._convert()
            return self._arg

    def _searchable_result_columns(self): return self._col

    def manage_testForm(self, REQUEST):
        """Provide testing interface"""
        input_src=default_input_form(self.title_or_id(),
                                     self._searchable_arguments(),
                                     'manage_test')
        return HTML(input_src)(self, REQUEST)

    def manage_test(self, REQUEST):
        'Perform an actual query'
        
        result=self(REQUEST)
        report=HTML(custom_default_report(self.id, result))
        return apply(report,(self,REQUEST),{self.id:result})

    def index_html(self, PARENT_URL):
        " "
        raise 'Redirect', ("%s/manage_testForm" % PARENT_URL)

class Composite:    

    def _getquery(self,id):

        o=self
        i=0
        while 1:
            __traceback_info__=o
            q=getattr(o,id)
            try:
                if hasattr(q,'_searchable_arguments'):
                    try: q=q.__of__(self.aq_parent)
                    except: pass
                    return q
            except: pass
            if i > 100: raise AttributeError, id
            i=i+1
            o=o.aq_parent
            
    def myQueryIds(self):
        return map(
            lambda k, queries=self.queries:
            {'id': k, 'selected': k in queries},
            self.ZQueryIds())

def default_input_form(id,arguments,action='query',
                       tabs=''):
    if arguments:
        items=arguments.items()
        return (
            "%s\n%s%s" % (
                '<html><head><title>%s Input Data</title></head><body>\n%s\n'
                '<form action="<!--#var URL2-->/<!--#var id-->/%s" '
                'method="get">\n'
                '<h2>%s Input Data</h2>\n'
                'Enter query parameters:<br>'
                '<table>\n'
                % (id,tabs,action,id),
                string.joinfields(
                    map(
                        lambda a:
                        ('<tr>\t<th>%s</th>\n'
                         '\t<td><input name="%s"'
                         '\n\t      width=30 value="%s">'
                         '</td></tr>'
                         % (nicify(a[0]),
                            (
                                a[1].has_key('type') and
                                ("%s:%s" % (a[0],a[1]['type'])) or
                                a[0]
                                ),
                            a[1].has_key('default') and a[1]['default'] or ''
                            ))
                        , items
                        ),
                '\n'),
                '\n<tr><td colspan=2 align=center>\n'
                '<input type="SUBMIT" name="SUBMIT" value="Submit Query">\n'
                '<!--#if HTTP_REFERER-->\n'
                '  <input type="SUBMIT" name="SUBMIT" value="Cancel">\n'
                '  <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"\n'
                '         VALUE="<!--#var HTTP_REFERER-->">\n'
                '<!--#/if HTTP_REFERER-->\n'
                '</td></tr>\n</table>\n</form>\n</body>\n</html>\n'
                )
            )
    else:
        return (
            '<html><head><title>%s Input Data</title></head><body>\n%s\n'
            '<form action="<!--#var URL2-->/<!--#var id-->/%s" '
            'method="get">\n'
            '<h2>%s Input Data</h2>\n'
            'This query requires no input.<p>\n'
            '<input type="SUBMIT" name="SUBMIT" value="Submit Query">\n'
            '<!--#if HTTP_REFERER-->\n'
            '  <input type="SUBMIT" name="SUBMIT" value="Cancel">\n'
            '  <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"\n'
            '         VALUE="<!--#var HTTP_REFERER-->">\n'
            '<!--#/if HTTP_REFERER-->\n'
            '</td></tr>\n</table>\n</form>\n</body>\n</html>\n'
            % (id, tabs, action, id)
            )


custom_default_report_src=DocumentTemplate.File(
    os.path.join(dtml_dir,'customDefaultReport.dtml'))

def custom_default_report(id, result, action='', no_table=0,
                          goofy=regex.compile('[^a-zA-Z0-9_]').search
                          ):
    columns=result._searchable_result_columns()
    __traceback_info__=columns
    heading=('<tr>\n%s\t</tr>' %
                 string.joinfields(
                     map(lambda c:
                         '\t<th>%s</th>\n' % nicify(c['name']),
                         columns),
                     ''
                     )
                 )

    if no_table: tr, _tr, td, _td, delim = '<p>', '</p>', '', '', ', '
    else: tr, _tr, td, _td, delim = '<tr>', '</tr>', '<td>', '</td>', ''

    if no_table: tr='<p>', '</p>'
    else: tr, _tr = '<tr>', '</tr>'

    row=[]
    for c in columns:
        n=c['name']
        if goofy(n) >= 0: n='expr="_vars[\'%s]"' % (`'"'+n`[2:])
        row.append('\t%s<!--#var %s%s-->%s\n'
                   % (td,n,c['type']!='s' and ' null=""' or '',_td))

    row=('%s\n%s\t%s' % (tr,string.joinfields(row,delim), _tr))

    return custom_default_report_src(
        id=id,heading=heading,row=row,action=action,no_table=no_table)

def detypify(arg):
    l=string.find(arg,':')
    if l > 0: arg=arg[:l]
    return arg

def decode(input,output):
    while 1:
        line = input.readline()
        if not line: break
        s = binascii.a2b_base64(line[:-1])
        output.write(s)

def decodestring(s):
        f = StringIO(s)
        g = StringIO()
        decode(f, g)
        return g.getvalue()

class Args:
    def __init__(self, data, keys):
        self._data=data
        self._keys=keys

    def items(self):
        return map(lambda k, d=self._data: (k,d[k]), self._keys)

    def values(self):
        return map(lambda k, d=self._data: d[k], self._keys)

    def keys(self): return list(self._keys)
    def has_key(self, key): return self._data.has_key(key)
    def __getitem__(self, key): return self._data[key]
    def __setitem__(self, key, v): self._data[key]=v
    def __delitem__(self, key): del self._data[key]
    def __len__(self): return len(self._data)

def parse(text,
          result=None,
          keys=None,
          unparmre=regex.compile(
              '\([\0- ]*\([^\0- =\"]+\)\)'),
          parmre=regex.compile(
              '\([\0- ]*\([^\0- =\"]+\)=\([^\0- =\"]+\)\)'),
          qparmre=regex.compile(
              '\([\0- ]*\([^\0- =\"]+\)="\([^"]*\)\"\)'),
          ):

    if result is None:
        result = {}
        keys=[]

    __traceback_info__=text

    if parmre.match(text) >= 0:
        name=parmre.group(2)
        value={'default':parmre.group(3)}
        l=len(parmre.group(1))
    elif qparmre.match(text) >= 0:
        name=qparmre.group(2)
        value={'default':qparmre.group(3)}
        l=len(qparmre.group(1))
    elif unparmre.match(text) >= 0:
        name=unparmre.group(2)
        l=len(unparmre.group(1))
        value={}
    else:
        if not text or not strip(text): return Args(result,keys)
        raise InvalidParameter, text

    lt=string.find(name,':')
    if lt > 0:
        value['type']=name[lt+1:]
        name=name[:lt]

    result[name]=value
    keys.append(name)

    return parse(text[l:],result,keys)

def quotedHTML(text,
               character_entities=(
                   (regex.compile('&'), '&amp;'),
                   (regex.compile("<"), '&lt;' ),
                   (regex.compile(">"), '&gt;' ),
                   (regex.compile('"'), '&quot;'))): #"
    import regsub
    for re,name in character_entities:
        text=regsub.gsub(re,name,text)
    return text

def nicify(name, under=regex.compile('_')):
    name=regsub.gsub(under,' ',string.strip(name))
    return string.upper(name[:1])+name[1:]

class Rotor:

    def __init__(self, key, numrotors=6):
        self.a=key, numrotors
        r=rotor.newrotor(key, numrotors)
        self.encrypt=r.encrypt
        self.decrypt=r.decrypt
        self.decryptmore=r.decryptmore

    def __getinitargs__(self): return self.a
    def __getstate__(self,v={}): return v
    


def decapitate(html, RESPONSE=None,
               header_re=regex.compile(
                   '\(\('
                          '[^\0- <>:]+:[^\n]*\n'
                      '\|'
                          '[ \t]+[^\0- ][^\n]*\n'
                   '\)+\)[ \t]*\n\([\0-\377]+\)'
                   ),
               space_re=regex.compile('\([ \t]+\)'),
               name_re=regex.compile('\([^\0- <>:]+\):\([^\n]*\)'),
               ):
    if header_re.match(html) < 0: return html

    headers, html = header_re.group(1,3)

    headers=string.split(headers,'\n')

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
            v=string.strip(v)
        else:
            raise ValueError, 'Invalid Header (%d): %s ' % (i,headers[i])
        RESPONSE.setHeader(k,v)

    return html



def delimited_output(results,REQUEST,RESPONSE):
    delim=REQUEST['output-delimiter']
    try: output_type=REQUEST['output-type']
    except: output_type='text/plain'
    RESPONSE.setHeader('content-type', output_type)
    join=string.join
    return "%s\n%s\n" % (
        join(results.names(),delim),
        join(map(lambda row, delim=delim, join=join:
                 join(map(str,row),delim),
                 results),
             '\n')
        )
