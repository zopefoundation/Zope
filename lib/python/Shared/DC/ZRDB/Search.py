#!/bin/env python
########################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
########################################################################## 
__doc__='''Aqueduct Search Interface Wizard

$Id: Search.py,v 1.1 1997/12/17 21:01:20 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

from Globals import HTMLFile
from Aqueduct.Aqueduct import custom_default_report, nicify
from string import join

addForm=HTMLFile('AqueductReport/searchAdd')
def add(self, report_id, report_title, input_id, input_title, queries=[],
	acl_type='A',acl_roles=[], REQUEST=None):
    'add a report'

    if not queries: raise ValueError, (
	'No <em>searchable objects</em> were selected')

    if not report_id: raise ValueError, (
	'No <em>report id</em> were specified')

    if input_title and not input_id: raise ValueError, (
	'No <em>input id</em> were specified')

    qs=map(lambda q, self=self: _getquery(self, q), queries)
    for q in qs:
	id=q.id
	arguments={}
	for name, arg in q._searchable_arguments().items():
	    arguments["%s/%s" % (id,name)]=arg
	if q._searchable_result_columns() is None:
	    raise 'Unusable Searchable Error',(
		"""The input searchable object, <em>%s</em>,
		has not been tested.  Until it has been tested,
		it\'s outpuit schema is unknown, and a report
		cannot be generated.  Before creating a report
		from this query, you must try out the query.  To
		try out the query, <a href="%s">click hear</a>.
		""" % (q.title_and_id(), q.id))

    if input_id:
	self.manage_addDocument(
	    input_id,input_title,
	    default_input_form(arguments, report_id),
	    acl_type,acl_roles)

    self.manage_addDocument(
	report_id,report_title,
	('<!--#var standard_html_header-->\n%s\n'
	 '<!--#var standard_html_footer-->' % 
	 join(map(lambda q: custom_default_report(q.id, q), qs),
	      '\n<hr>\n')),
	acl_type,acl_roles)

    if REQUEST: return self.manage_main(self,REQUEST)

def aqueductQueryIds(self):
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
	items.sort()
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
			('<tr>\t<th>%s</th>\n'
		         '\t<td><input name="%s" width=30 value="%s">'
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


############################################################################## 
#
# $Log: Search.py,v $
# Revision 1.1  1997/12/17 21:01:20  jim
# *** empty log message ***
#
# Revision 1.14  1997/10/28 22:21:44  brian
# Fixed bug in report
#
# Revision 1.13  1997/09/26 22:18:52  jim
# more
#
# Revision 1.12  1997/09/25 21:14:11  jim
# Change to use new searchable interface.
#
# Revision 1.11  1997/09/22 19:11:05  jim
# updated role support
#
# Revision 1.10  1997/09/22 18:47:32  jim
# Got rid of ManageHTML
# Fixed bug in query that caused extra database updates.
#
# Revision 1.9  1997/08/16 00:58:20  jim
# Added machinery to add automatic execution in input helper.
#
# Revision 1.8  1997/08/15 22:30:51  jim
# Added machinery to get argument values from instance attributes.
# And added machinery to readopt web ancenstors rather than
# normal acquisition ancestors.
#
# Revision 1.7  1997/08/08 22:56:55  jim
# Redid bodify to hopefully get around win32 limitations.
#
# Revision 1.6  1997/08/08 18:30:01  jim
# Rerouted "return".
#
# Revision 1.5  1997/08/08 16:58:12  jim
# Added access control support
#
# Revision 1.4  1997/08/06 21:27:20  jim
# *** empty log message ***
#
# Revision 1.3  1997/08/06 18:25:14  jim
# Renamed description->title and name->id and other changes
#
# Revision 1.2  1997/08/06 14:03:40  jim
# *** empty log message ***
#
# Revision 1.1  1997/07/25 18:13:06  jim
# initial
#
#
