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
__doc__='''Generic Database adapter


$Id: DA.py,v 1.15 1997/11/26 20:06:03 jim Exp $'''
__version__='$Revision: 1.15 $'[11:-2]

import string, OFS.SimpleItem, Aqueduct.Aqueduct, Aqueduct.RDB
import DocumentTemplate, marshal, md5, zlib, base64, DateTime, Acquisition
from Aqueduct.Aqueduct import quotedHTML, decodestring, parse, Rotor
from Aqueduct.Aqueduct import custom_default_report, default_input_form
from Globals import HTMLFile, MessageDialog
from cStringIO import StringIO
log_file=None
import sys, traceback
from DocumentTemplate import HTML
import Globals, OFS.SimpleItem, AccessControl.Role, Persistence

addForm=HTMLFile('AqueductDA/daAdd')

def add(self,klass,id,title,key,arguments,template,REQUEST=None):
    'Add a query'
    q=klass()
    q.id=id
    q.manage_edit(key,title,arguments,template)
    self._setObject(id,q)
    if REQUEST: return self.manage_main(self,REQUEST)

class DA(
    Aqueduct.Aqueduct.BaseQuery,Acquisition.Implicit,
    Persistence.Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    ):
    'Database Adapter'

    icon       ='AqueductDA/DBAdapter_icon.gif'
    hasAqueductClientInterface=1
    _col=None
    sql_delimiter='\0'
    
    manage=HTMLFile('AqueductDA/edit')

    test_url___roles__=None
    def test_url_(self):
	'Method for testing server connection information'
	return 'PING'

    def quoted_src(self): return quotedHTML(self.src)

    def manage_edit(self,key,title,arguments,template,REQUEST=None):
	'change query properties'
	self.title=title
	self.key=key
	self.rotor=Rotor(key)
	self.arguments_src=arguments
	self._arg=parse(arguments)
	self.src=template
	self.template=DocumentTemplate.HTML(template)
	if REQUEST:
	    return MessageDialog(
		title=self.id+' changed',
		message=self.id+' has been changed sucessfully.',
		action=REQUEST['URL2']+'/manage_main',
		)

    
    def manage_testForm(self, REQUEST):
	"""Provide testing interface"""
	input_src=default_input_form(self.title_or_id(),
				     self._arg, 'manage_test')
	return HTML(input_src)(self, REQUEST)

    def manage_test(self, REQUEST):
	'Perform an actual query'
	
	result=self(REQUEST)
	report=HTML(custom_default_report(self.id, result))
	return apply(report,(self,REQUEST),{self.id:result})

    def index_html(self, PARENT_URL):
	" "
	raise 'Redirect', ("%s/manage_testForm" % PARENT_URL)

    def _searchable_arguments(self): return self._arg

    def _searchable_result_columns(self): return self._col

    def __call__(self,REQUEST):
	try: DB__=getattr(self, self.connection_id)()
	except: raise 'Database Error', (
	    '%s is not connected to a database' % self.id)
	
	argdata=self._argdata(REQUEST)
	query=self.template(self,argdata)
	result=DB__.query(query)
	result=Aqueduct.RDB.File(StringIO(result))
	columns=result._searchable_result_columns()
	if columns != self._col: self._col=columns
	return result
	
    def query(self,REQUEST,RESPONSE):
	' '
	try: DB__=getattr(self, self.connection_id)()
	except: raise 'Database Error', (
	    '%s is not connected to a database' % self.id)

	try:
	    argdata=REQUEST['BODY']
	    argdata=decodestring(argdata)
	    argdata=self.rotor.decrypt(argdata)
	    digest,argdata=argdata[:16],argdata[16:]
	    if md5.new(argdata).digest() != digest:
		raise 'Bad Request', 'Corrupted Data'
	    argdata=marshal.loads(argdata)
	    query=apply(self.template,(self,),argdata)
	    result=DB__.query(query)
	    result=zlib.compress(result,1)
	    result=md5.new(result).digest()+result
	    result=self.rotor.encrypt(result)
	    result=base64.encodestring(result)
	    RESPONSE['content-type']='text/X-PyDB'
	    RESPONSE['Content-Length']=len(result)
	    RESPONSE.write(result)
	except:
	    t,v,tb=sys.exc_type, sys.exc_value, sys.exc_traceback
	    result=str(RESPONSE.exception())
	    serial=str(DateTime.now())
	    if log_file:
		l=string.find(result,"Traceback (innermost last):")
		if l >= 0: l=result[l:]
		else: l=v
		log_file.write("%s\n%s %s, %s:\n%s\n" % (
		    '-'*30, serial, self.id, t, l))
		log_file.flush()
	    serial="Error number: %s\n" % serial
	    serial=zlib.compress(serial,1)
	    serial=md5.new(serial).digest()+serial
	    serial=self.rotor.encrypt(serial)
	    serial=base64.encodestring(serial)
	    RESPONSE.setBody(serial)
	
############################################################################## 
#
# $Log: DA.py,v $
# Revision 1.15  1997/11/26 20:06:03  jim
# New Architecture, note that backward compatibility tools are needed
#
# Revision 1.12  1997/09/26 22:17:45  jim
# more
#
# Revision 1.11  1997/09/25 21:11:52  jim
# got rid of constructor
#
# Revision 1.10  1997/09/25 18:47:53  jim
# made index_html public
#
# Revision 1.9  1997/09/25 18:41:20  jim
# new interfaces
#
# Revision 1.8  1997/09/25 17:35:30  jim
# Made some corrections for network behavior.
#
# Revision 1.7  1997/09/22 18:44:38  jim
# Got rid of ManageHTML
# Fixed bug in manage_test that caused extra database updates.
#
# Revision 1.6  1997/08/15 22:29:12  jim
# Fixed bug in passing query arguments.
#
# Revision 1.5  1997/08/08 22:55:32  jim
# Improved connection status management and added database close method.
#
# Revision 1.4  1997/08/06 18:19:29  jim
# Renamed description->title and name->id and other changes
#
# Revision 1.3  1997/07/28 21:31:04  jim
# Get rid of add method here and test scaffolding.
#
# Revision 1.2  1997/07/25 16:49:31  jim
# Added manage_addDAFolder, which can be shared by various DAs.
#
# Revision 1.1  1997/07/25 16:43:05  jim
# initial
#
#
