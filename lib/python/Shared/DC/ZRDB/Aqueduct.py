#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''Shared Aqueduct classes and functions

$Id: Aqueduct.py,v 1.23 1998/04/15 14:55:26 jim Exp $'''
__version__='$Revision: 1.23 $'[11:-2]

from Globals import HTMLFile, Persistent
import DocumentTemplate, DateTime, regex, regsub, string, urllib, rotor
import binascii, Acquisition
DateTime.now=DateTime.DateTime
from cStringIO import StringIO
from OFS import SimpleItem
from AccessControl.Role import RoleManager
from DocumentTemplate import HTML

from string import strip

dtml_dir="%s/lib/python/Aqueduct/" % SOFTWARE_HOME

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
	    self.aqueductQueryIds())

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
    dtml_dir+'customDefaultReport.dtml')

def custom_default_report(id, result, action='', no_table=0):
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

    row=('%s\n%s\t%s' %
	 (tr,string.joinfields(
	     map(lambda c, td=td, _td=_td:
		 '\t%s<!--#var %s%s-->%s\n'
		 % (td,urllib.quote(c['name']),
		    c['type']!='s' and ' null=""' or '',_td),
		 columns),
	     delim), _tr))

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


############################################################################## 
#
# $Log: Aqueduct.py,v $
# Revision 1.23  1998/04/15 14:55:26  jim
# Fixed InvalidParameter NameError
#
# Revision 1.22  1998/04/15 14:23:36  jim
# Changed parse to return a mapping object that keeps its
# items sorted in original order.
#
# Revision 1.21  1998/04/14 15:20:39  jim
# No longer sort items in input form.
#
# Revision 1.20  1998/01/12 20:36:26  jim
# Fixed bug in report generation.
#
# Revision 1.19  1998/01/12 19:19:48  jim
# *** empty log message ***
#
# Revision 1.18  1998/01/12 19:18:34  jim
# *** empty log message ***
#
# Revision 1.17  1998/01/09 13:58:14  jim
# added option for tabular vs record reports
#
# Revision 1.16  1997/12/12 23:38:04  jim
# Added debugging info.
#
# Revision 1.15  1997/12/05 21:26:54  jim
# Minor change to help out testing DAs.
#
# Revision 1.14  1997/12/05 21:23:55  jim
# Minor change to help out testing DAs.
#
# Revision 1.13  1997/10/09 15:10:37  jim
# Added some attempts to provide backward compatibility with earlier
# Principia version.
#
# Added support for empty string as default.
#
# Revision 1.12  1997/09/26 22:17:36  jim
# more
#
# Revision 1.11  1997/09/25 22:33:01  jim
# fixed argument handling bugs
#
# Revision 1.10  1997/09/25 21:45:08  jim
# Fixed argument parse bug
#
# Revision 1.9  1997/09/25 21:11:13  jim
# cleanup and other work
#
# Revision 1.8  1997/09/25 18:40:57  jim
# new interfaces and RDB
#
# Revision 1.7  1997/09/22 18:43:46  jim
# Got rid of ManageHTML
#
# Revision 1.6  1997/08/15 22:28:18  jim
# Added machinery to get argument values from instance attributes.
#
# Revision 1.5  1997/08/06 18:19:14  jim
# Renamed description->title and name->id and other changes
#
# Revision 1.4  1997/07/29 00:38:39  jim
# Changed to use get due to odbc lamosity.
#
# Revision 1.3  1997/07/28 22:32:20  jim
# *** empty log message ***
#
# Revision 1.2  1997/07/28 21:27:17  jim
# Changed generated input forms to use post.
#
# Revision 1.1  1997/07/25 16:07:18  jim
# initial
#
#
