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
__doc__='''Search Interface Wizard

$Id: Search.py,v 1.8 1998/12/29 17:01:59 jim Exp $'''
__version__='$Revision: 1.8 $'[11:-2]

from Globals import HTMLFile
from Aqueduct import custom_default_report, nicify, Args
from string import join

addForm=HTMLFile('searchAdd', globals())
def add(self, report_id, report_title, report_style,
        input_id, input_title, queries=[],
        REQUEST=None):
    'add a report'

    if not queries: raise ValueError, (
        'No <em>searchable objects</em> were selected')

    if not report_id: raise ValueError, (
        'No <em>report id</em> were specified')

    if input_title and not input_id: raise ValueError, (
        'No <em>input id</em> were specified')

    qs=map(lambda q, self=self: _getquery(self, q), queries)
    arguments={}
    keys=[]
    for q in qs:
        id=q.id
        if input_id:
            for name, arg in q._searchable_arguments().items():
                if len(qs) > 1: key="%s/%s" % (id,name)
                else: key=name 
                arguments[key]=arg
                keys.append(key)
        if q._searchable_result_columns() is None:
            raise 'Unusable Searchable Error',(
                """The input searchable object, <em>%s</em>,
                has not been tested.  Until it has been tested,
                it\'s outpuit schema is unknown, and a report
                cannot be generated.  Before creating a report
                from this query, you must try out the query.  To
                try out the query, <a href="%s">click hear</a>.
                """ % (q.title_and_id(), id))

    if input_id:
        arguments=Args(arguments, keys)
        self.manage_addDocument(
            input_id,input_title,
            default_input_form(arguments, report_id))

    self.manage_addDocument(
        report_id,report_title,
        ('<!--#var standard_html_header-->\n%s\n'
         '<!--#var standard_html_footer-->' % 
         join(map(lambda q, report_style=report_style:
                  custom_default_report(q.id, q, no_table=report_style), qs),
              '\n<hr>\n')))

    if REQUEST: return self.manage_main(self,REQUEST)

def ZQueryIds(self):
    # Note that report server configurations will expend on this
    t=[]
    ids={}
    old=ids.has_key
    o=self
    n=0
    while 1:

        # Look for queries
        try: map=o.objectMap()
        except AttributeError: map=()

        for i in map:
            try:
                id=i['id']
                if (not old(id) and
                    hasattr(getattr(o,id),'_searchable_arguments')
                    ):
                    t.append(i['id'])
                    ids[id]=1
            except: pass

        # Now extend search to parent
        try: o=o.aq_parent
        except: return t
  
        if n > 100: return t # Seat belt
        n=n+1

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


def default_input_form(arguments,action='query',
                       tabs=''):
    if arguments:
        items=arguments.items()
        return (
            "%s\n%s%s" % (
                '<!--#var standard_html_header-->\n%s\n'
                '<form action="%s" method="get">\n'
                '<h2><!--#var document_title--></h2>\n'
                'Enter query parameters:<br>'
                '<table>\n'
                % (tabs,action),
                join(
                    map(
                        lambda a:
                        ('<tr><th>%s</th>\n'
                         '    <td><input name="%s"\n'
                         '               width=30 value="%s">'
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
                '</td></tr>\n</table>\n</form>\n'
                '<!--#var standard_html_footer-->\n'
                )
            )
    else:
        return (
            '<!--#var standard_html_header-->\n%s\n'
            '<form action="%s" method="get">\n'
            '<h2><!--#var document_title--></h2>\n'
            'This query requires no input.<p>\n'
            '<input type="SUBMIT" name="SUBMIT" value="Submit Query">\n'
            '<!--#if HTTP_REFERER-->\n'
            '  <input type="SUBMIT" name="SUBMIT" value="Cancel">\n'
            '  <INPUT NAME="CANCEL_ACTION" TYPE="HIDDEN"\n'
            '         VALUE="<!--#var HTTP_REFERER-->">\n'
            '<!--#/if HTTP_REFERER-->\n'
            '</td></tr>\n</table>\n</form>\n'
            '<!--#var standard_html_footer-->\n'
            % (tabs, action)
            )
