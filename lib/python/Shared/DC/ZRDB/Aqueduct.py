7##############################################################################
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
__doc__='''Shared classes and functions

$Id: Aqueduct.py,v 1.44 2001/01/15 16:07:39 brian Exp $'''
__version__='$Revision: 1.44 $'[11:-2]

import Globals, os
from Globals import Persistent
import DocumentTemplate, DateTime, ts_regex,  regex, string
import binascii, Acquisition
DateTime.now=DateTime.DateTime
from cStringIO import StringIO
from OFS import SimpleItem
from AccessControl.Role import RoleManager
from DocumentTemplate import HTML

from string import strip, replace

dtml_dir=os.path.join(Globals.package_home(globals()), 'dtml')

InvalidParameter='Invalid Parameter'


class BaseQuery(Persistent, SimpleItem.Item,
                Acquisition.Implicit, RoleManager):

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

    def index_html(self, URL1):
        " "
        raise 'Redirect', ("%s/manage_testForm" % URL1)

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
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n'
                '<html lang="en"><head><title>%s Input Data</title></head>\n'
                '<body bgcolor="#FFFFFF" link="#000099" vlink="#555555">\n%s\n'
                '<form action="<dtml-var URL2>/<dtml-var id>/%s" '
                'method="get">\n'
                '<h2>%s Input Data</h2>\n'
                'Enter query parameters:<br>'
                '<table>\n'
                % (id, tabs, action,id),
                string.joinfields(
                    map(
                        lambda a:
                        ('<tr> <th>%s</th>\n'
                         '     <td><input name="%s"\n'
                         '                width=30 value="%s">'
                         '     </td></tr>'
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
                '<dtml-if HTTP_REFERER>\n'
                '  <input type="SUBMIT" name="SUBMIT" value="Cancel">\n'
                '  <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"\n'
                '         VALUE="<dtml-var HTTP_REFERER>">\n'
                '</dtml-if>\n'
                '</td></tr>\n</table>\n</form>\n</body>\n</html>\n'
                )
            )
    else:
        return (
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">\n'
            '<html lang="en"><head><title>%s Input Data</title></head>\n'
            '<body bgcolor="#FFFFFF" link="#000099" vlink="#555555">\n%s\n'
            '<form action="<dtml-var URL2>/<dtml-var id>/%s" '
            'method="get">\n'
            '<h2>%s Input Data</h2>\n'
            'This query requires no input.<p>\n'
            '<input type="SUBMIT" name="SUBMIT" value="Submit Query">\n'
            '<dtml-if HTTP_REFERER>\n'
            '  <input type="SUBMIT" name="SUBMIT" value="Cancel">\n'
            '  <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"\n'
            '         VALUE="<dtml-var HTTP_REFERER>">\n'
            '</dtml-if>\n'
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
    heading=('<tr>\n%s        </tr>' %
                 string.joinfields(
                     map(lambda c:
                         '          <th>%s</th>\n' % nicify(c['name']),
                         columns),
                     ''
                     )
                 )

    if no_table: tr, _tr, td, _td, delim = '<p>', '</p>', '', '', ',\n'
    else: tr, _tr, td, _td, delim = '<tr>', '</tr>', '<td>', '</td>', '\n'

    row=[]
    for c in columns:
        n=c['name']
        if goofy(n) >= 0: n='expr="_[\'%s]"' % (`'"'+n`[2:])
        row.append('          %s<dtml-var %s%s>%s'
                   % (td,n,c['type']!='s' and ' null=""' or '',_td))

    row=('     %s\n%s\n        %s' % (tr,string.joinfields(row,delim), _tr))

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
          unparmre=ts_regex.compile(
              '\([\0- ]*\([^\0- =\"]+\)\)'),
          parmre=ts_regex.compile(
              '\([\0- ]*\([^\0- =\"]+\)=\([^\0- =\"]+\)\)'),
          qparmre=ts_regex.compile(
              '\([\0- ]*\([^\0- =\"]+\)="\([^"]*\)\"\)'),
          ):

    if result is None:
        result = {}
        keys=[]

    __traceback_info__=text

    ts_results = parmre.match_group(text, (1,2,3))
    if ts_results:
        start, grps = ts_results
        name=grps[1]
        value={'default':grps[2]}
        l=len(grps[0])
    else:
        ts_results = qparmre.match_group(text, (1,2,3))
        if ts_results:
                start, grps = ts_results
                name=grps[1]
                value={'default':grps[2]}
                l=len(grps[0])
        else:
            ts_results = unparmre.match_group(text, (1,2))
            if ts_results:
                start, grps = ts_results
                name=grps[1]
                l=len(grps[0])
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
                   ('&', '&amp;'),
                   ("<", '&lt;' ),
                   (">", '&gt;' ),
                   ('"', '&quot;'))): #"


    for re,name in character_entities:
        text=replace(text,re,name)

    return text

def nicify(name):
    name=replace(string.strip(name), '_',' ')
    return string.upper(name[:1])+name[1:]

def decapitate(html, RESPONSE=None,
               header_re=ts_regex.compile(
                   '\(\('
                          '[^\0- <>:]+:[^\n]*\n'
                      '\|'
                          '[ \t]+[^\0- ][^\n]*\n'
                   '\)+\)[ \t]*\n\([\0-\377]+\)'
                   ),
               space_re=ts_regex.compile('\([ \t]+\)'),
               name_re=ts_regex.compile('\([^\0- <>:]+\):\([^\n]*\)'),
               ):


    ts_results = header_re.match_group(html, (1,3))
    if not ts_results: return html

    headers, html = ts_results[1]

    headers=string.split(headers,'\n')

    i=1
    while i < len(headers):
        if not headers[i]:
            del headers[i]
        else:
            ts_results = space_re.match_group(headers[i], (1,))
            if ts_results:
                headers[i-1]="%s %s" % (headers[i-1],
                                        headers[i][len(ts_reults[1]):])
                del headers[i]
            else:
                i=i+1

    for i in range(len(headers)):
        ts_results = name_re.match_group(headers[i], (1,2))
        if ts_reults:
            k, v = ts_reults[1]
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
