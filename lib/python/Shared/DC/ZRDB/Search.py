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
__doc__='''Search Interface Wizard

$Id: Search.py,v 1.11 1999/05/26 15:35:48 brian Exp $'''
__version__='$Revision: 1.11 $'[11:-2]

from Globals import HTMLFile
from Aqueduct import custom_default_report, nicify, Args
from string import join

addForm=HTMLFile('searchAdd', globals())
def manage_addZSearch(self, report_id, report_title, report_style,
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
                it\'s output schema is unknown, and a report
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
            '</td></tr>\n</table>\n</form>\n'
            '<!--#var standard_html_footer-->\n'
            % (tabs, action)
            )
