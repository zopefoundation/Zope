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


$Id: DA.py,v 1.4 1997/08/06 18:19:29 jim Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

import string, OFS.Folder, Aqueduct.Aqueduct, Aqueduct.RDB
import DocumentTemplate, marshal, md5, zlib, base64, DateTime, Acquisition
from Aqueduct.Aqueduct import quotedHTML, decodestring, parse, Rotor
from Aqueduct.Aqueduct import custom_default_report, default_input_form
from Aqueduct.Aqueduct import default_report_src
from Globals import Persistent, ManageHTMLFile, MessageDialog
from cStringIO import StringIO
log_file=None
import sys, traceback

class Folder(OFS.Folder.Folder):    
    icon       ='AqueductDA/DBAdapterFolder_icon.gif'
    meta_type='Aqueduct Database Adapter Folder'

    manage_options=OFS.Folder.Folder.manage_options+(
	{'icon':'App/arrow.jpg', 'label':'Database Connection',
	'action':'manage_connectionForm',   'target':'manage_main'},
	)

    manage_main          =ManageHTMLFile('AqueductDA/main')

    manage_connectionForm=ManageHTMLFile('AqueductDA/connection')
    manage_addDAForm=ManageHTMLFile('AqueductDA/daAdd')
    start_time=DateTime.now()

    def manage_connection(self,value=None,check=None,REQUEST=None):
	'change database connection data'
	if value is None: return self.database_connection_string()
	if check: self.database_connect(value)
	self.database_connection_string(value)
	return self.manage_main(self,REQUEST)

    def database_connect(self,s=''):
	try: self._v_database_connection.close()
	except: pass
	self.bad_connection_string=(
	    """<strong>Warning</strong>: The database is not connected.
	    """)
	if not s: s=self.folder_database_connection_string()
	if not s: return 
	DB=self.database_connection_factory()
	try:
	    self._v_database_connection=DB(s)
	    self.connect_time=DateTime.now()
	except:
	    raise 'BadRequest', (
	    '<strong>Invalid connection string:</strong><br>'
	    + s)
	self.bad_connection_string=''
	
    def __setstate__(self, v):
	Folder.inheritedAttribute('__setstate__')(self, v)
	try:
	    if self._v_database_connection is not None:
		return
	except: pass
	try: self.database_connect()
	except: pass

    def manage_addDA(self,id,key,arguments,template,REQUEST):
	'Add a query'

	q=Query(id,key,arguments,template)
	self._setObject(id,q)
	return self.manage_main(self,REQUEST)

    test_url___allow_groups__=None
    def test_url_(self):
	'Method for testing server connection information'
	return 'PING'

class Query(Aqueduct.Aqueduct.BaseQuery,Persistent,Acquisition.Implicit):

    'Database query object'

    icon       ='AqueductDA/DBAdapter_icon.gif'
    meta_type='Aqueduct Database Adapter'
    hasAqueductClientInterface=1

    manage=ManageHTMLFile('AqueductDA/edit')

    def __init__(self,id='',key='',arguments='',template='',title=''):
	if not id: return
	self.id=id
	self.report_src=default_report_src
	self.manage_edit(key,title,arguments,template)

    def quoted_src(self): return quotedHTML(self.src)

    def manage_edit(self,key,title,arguments,template,URL2=''):
	'change query properties'
	self.title=title
	self.key=key
	self.rotor=Rotor(key)
	self.arguments_src=arguments
	self.arguments=parse(arguments)
	self.src=template
	self.template=DocumentTemplate.HTML(template)
	self.manage_testForm=DocumentTemplate.HTML(
	    default_input_form(self.id,self.arguments,
			       action='manage_test'),
	    __name__='test input form')
	if URL2:
	    return MessageDialog(
		title=self.id+' changed',
		message=self.id+' has been changed sucessfully.',
		action=URL2+'/manage_main',
		)

    def query_data(self,REQUEST):
	try: DB__=self.database_connection()
	except: raise 'Database Error', (
	    '%s is not connected to a database' % self.id)
	
	argdata=self._argdata(REQUEST,1)
	query_string=self._query_string(argdata,'manage_test')
	query=self.template(self,REQUEST)
	result=DB__.query(query)
	result=Aqueduct.RDB.RDB(StringIO(result))
	return result

    def manage_test(self,REQUEST):
	'Provide a simple interface for testing a query'
	try: DB__=self.database_connection()
	except: raise 'Database Error', (
	    '%s is not connected to a database' % self.id)
	
	argdata=self._argdata(REQUEST,1)
	query_string=self._query_string(argdata,'manage_test')
	query=self.template(self,REQUEST)
	result=DB__.query(query)
	result=Aqueduct.RDB.RDB(StringIO(result))
	self.result_names=result.names()
	self.report_src=custom_default_report(result,action='/manage_testForm')
	report=DocumentTemplate.HTML(self.report_src)
	return report(self,REQUEST,
		      query_results=result,
		      query_string=query_string,
		      )

	
    def query(self,DB__,REQUEST,RESPONSE):
	' '
	if DB__ is None: raise 'Database Error', (
	    'No database connection defined')
	try:
	    argdata=REQUEST.form.value
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
