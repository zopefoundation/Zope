##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Search Interface Wizard

$Id$'''
__version__='$Revision: 1.22 $'[11:-2]

from Globals import DTMLFile
from Aqueduct import custom_default_report, custom_default_zpt_report, nicify, Args
from string import join
from cgi import escape
from AccessControl import getSecurityManager

addForm=DTMLFile('dtml/searchAdd', globals())
def manage_addZSearch(self, report_id, report_title, report_style,
        input_id, input_title, object_type, queries=[],
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

    checkPermission=getSecurityManager().checkPermission

    for q in qs:
        url=q.absolute_url()
        if input_id:
            for name, arg in q._searchable_arguments().items():
                if len(qs) > 1: key="%s/%s" % (id,name)
                else: key=name
                arguments[key]=arg
                keys.append(key)
        if q._searchable_result_columns() is None:
            raise ValueError,(
                """The input searchable object, <em>%s</em>,
                has not been tested.  Until it has been tested,
                it\'s output schema is unknown, and a report
                cannot be generated.  Before creating a report
                from this query, you must try out the query.  To
                try out the query, <a href="%s">click here</a>.
                """ % (escape(q.title_and_id()), escape(url, 1)))

    if object_type == 'dtml_methods':

        if not checkPermission('Add DTML Methods', self):
            raise Unauthorized, (
                  'You are not authorized to add DTML Methods.'
                  )

        if input_id:
            arguments=Args(arguments, keys)
            self.manage_addDocument(
                input_id,input_title,
                default_input_form(arguments, report_id))

        self.manage_addDocument(
            report_id,report_title,
            ('<dtml-var standard_html_header>\n%s\n'
             '<dtml-var standard_html_footer>' %
             join(map(lambda q, report_style=report_style:
                      custom_default_report(q.id, q, no_table=report_style), qs),
                  '\n<hr>\n')))

        if REQUEST: return self.manage_main(self,REQUEST)

    elif object_type == 'page_templates':

        if not checkPermission('Add Page Templates', self):
            raise Unauthorized, (
                  'You are not authorized to add Page Templates.'
                  )

        if input_id:
            arguments = Args(arguments, keys)
            self.manage_addProduct['PageTemplates'].manage_addPageTemplate(
                input_id, input_title,
                default_input_zpt_form(arguments, report_id))


        self.manage_addProduct['PageTemplates'].manage_addPageTemplate(
            report_id,report_title,
            ('<html><body>\n%s\n'
             '</body></html>' %
             join(map(lambda q, report_style=report_style:
                      custom_default_zpt_report(q.id, q, no_table=report_style), qs),
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
                '<dtml-var standard_html_header>\n%s\n'
                '<form action="%s" method="get">\n'
                '<h2><dtml-var document_title></h2>\n'
                'Enter query parameters:<br>'
                '<table>\n'
                % (tabs,action),
                join(
                    map(
                        lambda a:
                        ('<tr><th>%s</th>\n'
                         '    <td><input name="%s"\n'
                         '               size="30" value="%s">'
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
                '<dtml-var standard_html_footer>\n'
                )
            )
    else:
        return (
            '<dtml-var standard_html_header>\n%s\n'
            '<form action="%s" method="get">\n'
            '<h2><dtml-var document_title></h2>\n'
            'This query requires no input.<p>\n'
            '<input type="SUBMIT" name="SUBMIT" value="Submit Query">\n'
            '</form>\n'
            '<dtml-var standard_html_footer>\n'
            % (tabs, action)
            )



def default_input_zpt_form(arguments,action='query',
                       tabs=''):
    if arguments:
        items=arguments.items()
        return (
            "%s\n%s%s" % (
                '<html><body>\n%s\n'
                '<form action="%s" method="get">\n'
                '<h2 tal:content="template/title_or_id">Title</h2>\n'
                'Enter query parameters:<br>'
                '<table>\n'
                % (tabs,action),
                join(
                    map(
                        lambda a:
                        ('<tr><th>%s</th>\n'
                         '    <td><input name="%s"\n'
                         '               size="30" value="%s">'
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
                '</body></html>\n'
                )
            )
    else:
        return (
            '<html><body>\n%s\n'
            '<form action="%s" method="get">\n'
            '<h2 tal:content="template/title_or_id">Title</h2>\n'
            '<p>This query requires no input.</p>\n'
            '<input type="SUBMIT" name="SUBMIT" value="Submit Query">\n'
            '</form>\n'
            '</body></html>\n'
            % (tabs, action)
            )
