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

$Id: Aqueduct.py,v 1.6 1997/08/15 22:28:18 jim Exp $'''
__version__='$Revision: 1.6 $'[11:-2]

from Globals import ManageHTMLFile
import DocumentTemplate, DateTime, regex, regsub, string, urllib, rotor
DateTime.now=DateTime.DateTime


dtml_dir="%s/lib/python/Aqueduct/" % SOFTWARE_HOME
default_report_src=open(dtml_dir+'defaultReport.dtml').read()

class BaseQuery:
    def query_year(self): return self.query_date.year()
    def query_month(self): return self.query_date.month()
    def query_day(self): return self.query_date.day()
    query_date=DateTime.now()
    manage_options=()

    def quoted_input(self): return quotedHTML(self.input_src)
    def quoted_report(self): return quotedHTML(self.report_src)

    MissingArgumentError='Bad Request'

    def _argdata(self,REQUEST,raw=0,return_missing_keys=0):
	args=self.arguments
	argdata={}
	id=self.id
	missing_keys=[]
	for arg in args.keys():
	    a=arg
	    l=string.find(arg,':')
	    if l > 0: arg=arg[:l]
	    v=REQUEST
	    try:
		try: v=REQUEST[arg]
		except (KeyError, AttributeError): pass
		if v is REQUEST:
		    try: v=REQUEST["%s.%s" % (id,arg)]
		    except (KeyError, AttributeError): pass
		if v is REQUEST:
		    l=string.find(arg,'.')
		    if l > 0 and raw:
			arg=arg[l+1:]
			try: v=REQUEST[arg]
			except (KeyError, AttributeError): pass
			if v is REQUEST:
			    try: v=REQUEST["%s.%s" % (id,arg)]
			    except (KeyError, AttributeError): pass
	    except:
		# Hm, we got another error, must have been an invalid
		# input.
		raise 'Bad Request', (
		    'The value entered for <em>%s</em> was invalid' % arg)
		
	    if v is REQUEST:
		v=args[a]
		if v is None:
		    if hasattr(self,arg): v=getattr(self,arg)
		    else:
			if return_missing_keys:
			    missing_keys.append(arg)
			else:
			    raise self.MissingArgumentError, (
				'''The required value <em>%s</em> was
				ommitted''' % arg)

	    if raw:
		argdata[a]=v
	    else:
		argdata[arg]=v

	if return_missing_keys and missing_keys:
	    raise self.MissingArgumentError, missing_keys

	return argdata

    def _query_string(self,argdata,query_method='query'):
	return "%s?%s" % (
	    query_method,
	    string.joinfields(
		map(lambda k, d=argdata:
		    "%s=%s" % (k, urllib.quote(str(d[k])))
		    , argdata.keys())
		)
	    )


def default_input_form(id,arguments,action='query'):
    id=nicify(id)
    if arguments:
	return (
	    "%s\n%s%s" % (
		'<html><head><title>%s Input Data</title></head><body>\n'
		'<form action="<!--#var URL2-->/<!--#var id-->/%s" '
		'method="get">\n'
		'<h2>%s Input Data</h2>\n'
		'Enter query parameters:<br>'
		'<table>\n'
		% (id,action,id),
		string.joinfields(
		    map(
			lambda a:
			('<tr>\t<td><strong>%s</strong>:</td>\n'
		         '\t<td><input name="%s" width=30></td></tr>'
			 % (nicify(detypify(a)),a))
			, arguments.keys()
			),
		'\n'),
		'\n<tr><td></td><td>\n'
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
	    '<html><head><title>%s Input Data</title></head><body>\n'
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
	    % (id, action, id)
	    )


custom_default_report_src=DocumentTemplate.File(
    dtml_dir+'customDefaultReport.dtml')

def custom_default_report(result, action=''):
    names=result.names()
    heading=('<tr>\n%s</tr>' %
		 string.joinfields(
		     map(lambda name:
			 '\t<th>%s</th>\n' % nicify(name),
			 names),
		     ''
		     )
		 )
    row=('<tr>\n%s</tr>' %
	     string.joinfields(
		 map(lambda name, meta:
		     '\t\t<td><!--#var %s%s--></td>\n'
		     % (urllib.quote(name),
			meta['type']!='s' and ' null=""' or '',
			),
		     names, result.__items__),
		 ''
		 )
	     )
    return custom_default_report_src(heading=heading,row=row,action=action)

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

def parse(text,
	  prefix=None,
	  result=None,
	  unparmre=regex.compile(
	      '\([\0- ]*\([^\0- =\"]+\)\)'),
	  parmre=regex.compile(
	      '\([\0- ]*\([^\0- =\"]+\)=\([^\0- =\"]+\)\)'),
	  qparmre=regex.compile(
	      '\([\0- ]*\([^\0- =\"]+\)="\([^"]+\)\"\)'),
	  ):

    if result is None: result = {}

    __traceback_info__=text

    if parmre.match(text) >= 0:
	name=parmre.group(2)
	value=parmre.group(3)
	l=len(parmre.group(1))
    elif qparmre.match(text) >= 0:
	name=qparmre.group(2)
	value=qparmre.group(3)
	l=len(qparmre.group(1))
    elif unparmre.match(text) >= 0:
	name=unparmre.group(2)
	l=len(unparmre.group(1))
	if prefix: name="%s.%s" % (prefix,name)
	result[name]=None
	return parse(text[l:],prefix,result)
    else:
	if not text or not strip(text): return result
	raise InvalidParameter, text

    if prefix: name="%s.%s" % (prefix,name)
    result[name]=value

    return parse(text[l:],prefix,result)

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
# Test functions:
#

def main():
    # The "main" program for this module
    import sys
    print sys.argv[0]+" is a pure module and doesn't do anything by itself."


if __name__ == "__main__": main()

############################################################################## 
#
# $Log: Aqueduct.py,v $
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
