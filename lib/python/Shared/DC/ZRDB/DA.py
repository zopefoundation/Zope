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


$Id: DA.py,v 1.50 1998/07/12 23:15:09 jim Exp $'''
__version__='$Revision: 1.50 $'[11:-2]

import OFS.SimpleItem, Aqueduct.Aqueduct, Aqueduct.RDB
import DocumentTemplate, marshal, md5, base64, DateTime, Acquisition, os
from Aqueduct.Aqueduct import decodestring, parse, Rotor
from Aqueduct.Aqueduct import custom_default_report, default_input_form
from Globals import HTMLFile, MessageDialog
from cStringIO import StringIO
import sys, Globals, OFS.SimpleItem, AccessControl.Role, Persistence
from string import atoi, find, join, split
import IOBTree, DocumentTemplate, sqlvar, sqltest, sqlgroup
from time import time
from zlib import compress, decompress
md5new=md5.new
import ExtensionClass
import DocumentTemplate.DT_Util
from cPickle import dumps, loads
from Aqueduct.Results import Results

class SQL(DocumentTemplate.HTML):
    commands={}
    for k, v in DocumentTemplate.HTML.commands.items(): commands[k]=v
    commands['sqlvar' ]=sqlvar.SQLVar
    commands['sqltest']=sqltest.SQLTest
    commands['sqlgroup' ]=sqlgroup.SQLGroup


class DA(
    Aqueduct.Aqueduct.BaseQuery,Acquisition.Implicit,
    Persistence.Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    ):
    'Database Adapter'

    _col=None
    max_rows_=1000
    cache_time_=0
    max_cache_=100
    rotor=None
    key=''
    class_name_=class_file_=''
    
    manage_options=(
	{'label':'Edit', 'action':'manage_main'},
	{'label':'Test', 'action':'manage_testForm'},
	{'label':'Advanced', 'action':'manage_advancedForm'},
	{'label':'Security', 'action':'manage_access'},
	)
 
    # Specify how individual operations add up to "permissions":
    __ac_permissions__=(
	('View management screens', ('manage_tabs','manage_main', 'index_html',
				     'manage_advancedForm',
				     )),
	('Change permissions',      ('manage_access',)            ),
	('Change Database Methods',
	 ('manage_edit','manage_advanced',
	  'manage_testForm','manage_test')),
	('Use Database Methods', ('__call__',''), ('Anonymous','Manager')),
	)
   

    def __init__(self, id, title, connection_id, arguments, template):
	self.id=id
	self.manage_edit(title, connection_id, arguments, template)
    
    manage_advancedForm=HTMLFile('AqueductDA/advanced')

    test_url___roles__=None
    def test_url_(self):
	'Method for testing server connection information'
	return 'PING'

    def _setKey(self, key):
	if key:
	    self.key=key
	    self.rotor=Rotor(key)
	elif self.__dict__.has_key('key'):
	    del self.key
	    del self.rotor

    _size_changes={
        'Bigger': (5,5),
        'Smaller': (-5,-5),
        'Narrower': (0,-5),
        'Wider': (0,5),
        'Taller': (5,0),
        'Shorter': (-5,0),
        }

    def _er(self,title,connection_id,arguments,template,
            SUBMIT,sql_pref__cols,sql_pref__rows,REQUEST):
        dr,dc = self._size_changes[SUBMIT]
        
        rows=max(1,atoi(sql_pref__rows)+dr)
        cols=max(40,atoi(sql_pref__cols)+dc)
        e='Friday, 31-Dec-99 23:59:59 GMT'
        resp=REQUEST['RESPONSE']
        resp.setCookie('sql_pref__rows',str(rows),path='/',expires=e)
        resp.setCookie('sql_pref__cols',str(cols),path='/',expires=e)
        return self.manage_main(
	    self,REQUEST,
            title=title,
            arguments_src=arguments,
            connection_id=connection_id,
            src=template,
	    sql_pref__cols=cols,sql_pref__rows=rows)

    def manage_edit(self,title,connection_id,arguments,template,
                    SUBMIT='Change',sql_pref__cols='50', sql_pref__rows='20',
                    REQUEST=None):
	"""Change database method  properties

	The 'connection_id' argument is the id of a database connection
	that resides in the current folder or in a folder above the
	current folder.  The database should understand SQL.

	The 'arguments' argument is a string containing an arguments
	specification, as would be given in the SQL method cration form.

	The 'template' argument is a string containing the source for the
	SQL Template.
	"""

        if self._size_changes.has_key(SUBMIT):
            return self._er(title,connection_id,arguments,template,
                            SUBMIT,sql_pref__cols,sql_pref__rows,REQUEST)

	self.title=title
	self.connection_id=connection_id
	self.arguments_src=arguments
	self._arg=parse(arguments)
	self.src=template
	self.template=t=SQL(template)
	t.cook()
	self._v_cache={}, IOBTree.Bucket()
	if REQUEST: return self.manage_editedDialog(REQUEST)

    def manage_advanced(self, key, max_rows, max_cache, cache_time,
			class_name, class_file,
			REQUEST):
	"""Change advanced properties

	The arguments are:

	key -- The encryption key used for communication with Principia
	       network clients.

	max_rows -- The maximum number of rows to be returned from a query.

	max_cache -- The maximum number of results to cache

	cache_time -- The maximum amound of time to use a cached result.

	class_name -- The name of a class that provides additional
	  attributes for result record objects. This class will be a
	  base class of the result record class.

	class_file -- The name of the file containing the class
	  definition.

	The class file normally resides in the 'Extensions'
	directory, however, the file name may have a prefix of
	'product.', indicating that it should be found in a product
	directory.

	For example, if the class file is: 'ACMEWidgets.foo', then an
	attempt will first be made to use the file
	'lib/python/Products/ACMEWidgets/Extensions/foo.py'. If this
	failes, then the file 'Extensions/ACMEWidgets.foo.py' will be
	used.
  
	"""
	self._setKey(key)
	self.max_rows_ = max_rows
	self.max_cache_, self.cache_time_ = max_cache, cache_time
	self._v_cache={}, IOBTree.Bucket()
	self.class_name_, self.class_file_ = class_name, class_file
	if modules.has_key(class_file): del modules[class_file]
	getBrain(self)
	if REQUEST: return self.manage_editedDialog(REQUEST)
    
    def manage_testForm(self, REQUEST):
	" "
	input_src=default_input_form(self.title_or_id(),
				     self._arg, 'manage_test',
				     '<!--#var manage_tabs-->')
	return DocumentTemplate.HTML(input_src)(self, REQUEST, HTTP_REFERER='')

    def manage_test(self, REQUEST):
	' '

	src="Could not render the query template!"
	result=()
	try:
	    src=self(REQUEST, src__=1)
            if find(src,'\0'): src=join(split(src,'\0'),'\n'+'-'*60+'\n')
	    result=self(REQUEST)
            if result._searchable_result_columns():
                r=custom_default_report(self.id, result)
            else:
                r='This was not a query.'
	except:
	    r=(
		'<strong>Error, <em>%s</em>:</strong> %s'
		% (sys.exc_type, sys.exc_value))

	report=DocumentTemplate.HTML(
	    '<html><BODY BGCOLOR="#FFFFFF" LINK="#000099" VLINK="#555555">\n'
	    '<!--#var manage_tabs-->\n<hr>\n%s\n\n'
	    '<hr><strong>SQL used:</strong><br>\n<pre>\n%s\n</pre>\n<hr>\n'
	    '</body></html>'
	    % (r,src))

	return apply(report,(self,REQUEST),{self.id:result})

    def index_html(self, PARENT_URL):
	" "
	raise 'Redirect', ("%s/manage_testForm" % PARENT_URL)

    def _searchable_arguments(self): return self._arg

    def _searchable_result_columns(self): return self._col

    def _cached_result(self, DB__, query):

	# Try to fetch from cache
	if hasattr(self,'_v_cache'): cache=self._v_cache
	else: cache=self._v_cache={}, IOBTree.Bucket()
	cache, tcache = cache
	max_cache=self.max_cache_
	now=time()
	t=now-self.cache_time_
	if len(cache) > max_cache / 2:
	    keys=tcache.keys()
	    keys.reverse()
	    while keys and (len(keys) > max_cache or keys[-1] < t):
		key=keys[-1]
		q=tcache[key]
		del tcache[key]
		del cache[q]
		del keys[-1]
		
	if cache.has_key(query):
	    k, r = cache[query]
	    if k > t: return r

	result=apply(DB__.query, query)
	if self.cache_time_ > 0:
            tcache[int(now)]=query
            cache[query]= now, result

	return result

    def __call__(self, REQUEST=None, __ick__=None, src__=0, **kw):
	"""Call the database method

	The arguments to the method should be passed via keyword
	arguments, or in a single mapping object. If no arguments are
	given, and if the method was invoked through the Web, then the
	method will try to acquire and use the Web REQUEST object as
	the argument mapping.

	The returned value is a sequence of record objects.
	"""

	if REQUEST is None:
	    if kw: REQUEST=kw
	    else:
		if hasattr(self, 'REQUEST'): REQUEST=self.REQUEST
		else: REQUEST={}

	try: dbc=getattr(self, self.connection_id)
	except AttributeError:
	    raise AttributeError, (
		"The database connection, <em>%s</em>, cannot be found.")

	try: DB__=dbc()
	except: raise 'Database Error', (
	    '%s is not connected to a database' % self.id)
	
	if hasattr(self, 'aq_parent'):
	    p=self.aq_parent
	else: p=None

	argdata=self._argdata(REQUEST)
	argdata['sql_delimiter']='\0'
	argdata['sql_quote__']=dbc.sql_quote__
	query=apply(self.template, (p,), argdata)

	if src__: return query

	if self.cache_time_ > 0 and self.self.max_cache_ > 0:
	    result=self._cached_result(DB__, (query, self.max_rows_))
	else: result=DB__.query(query, self.max_rows_)

	if hasattr(self, '_v_brain'): brain=self._v_brain
	else: brain=getBrain(self)
        if type(result) is type(''): 
            result=Aqueduct.RDB.File(StringIO(result),brain,self)
        else:
            result=Results(result, brain, self)
	columns=result._searchable_result_columns()
	if columns != self._col: self._col=columns
	return result
	
    def query(self,REQUEST,RESPONSE):
	' '
	try: dbc=getattr(self, self.connection_id)
	except AttributeError:
	    raise AttributeError, (
		"The database connection, <em>%s</em>, cannot be found.")

	try: DB__=dbc()
	except: raise 'Database Error', (
	    '%s is not connected to a database' % self.id)

	try:
	    argdata=REQUEST['BODY']
	    argdata=decodestring(argdata)
	    argdata=self.rotor.decrypt(argdata)
	    digest,argdata=argdata[:16],argdata[16:]
	    if md5new(argdata).digest() != digest:
		raise 'Bad Request', 'Corrupted Data'
	    argdata=marshal.loads(argdata)

            if hasattr(self, 'aq_parent'): p=self.aq_parent
            else: p=None

	    argdata['sql_delimiter']='\0'
	    argdata['sql_quote__']=dbc.sql_quote__
	    query=apply(self.template,(p,),argdata)

	    if self.cache_time_:
		result=self._cached_result(DB__, query)
	    else:
		result=DB__.query(query, self.max_rows_)

            if type(result) is not type(''):
                result=Results(result).asRDB()

	except:
	    RESPONSE.setStatus(500)
	    result="%s:\n%s\n" % (sys.exc_type, sys.exc_value)

        result=compress(result,1)
	result=md5new(result).digest()+result
	result=self.rotor.encrypt(result)
	result=base64.encodestring(result)
	#RESPONSE['content-type']='application/x-principia-network'
	RESPONSE['content-type']='text/x-pydb'
	RESPONSE['Content-Length']=len(result)
	RESPONSE.setBody(result)

    def __getitem__(self, key):
	self._arg[key] # raise KeyError if not an arg
	return Traverse(self,{},key)

    def connectionIsValid(self):
	return (hasattr(self, self.connection_id) and
		hasattr(getattr(self, self.connection_id), 'connected'))

    def connected(self):
	return getattr(getattr(self, self.connection_id), 'connected')()

ListType=type([])
class Traverse(ExtensionClass.Base):
    """Helper class for 'traversing' searches during URL traversal
    """
    _r=None
    _da=None

    def __init__(self, da, args, name=None):
	self._da=da
	self._args=args
	self._name=name

    def __bobo_traverse__(self, REQUEST, key):
	name=self._name
	da=self.__dict__['_da']
	args=self._args
	if name:
	    if args.has_key(name):
		v=args[name]
		if type(v) is not ListType: v=[v]
		v.append(key)
		key=v

	    args[name]=key

	    if len(args) < len(da._arg): 	    
		return self.__class__(da, args)
	    key=self # "consume" key

	elif da._arg.has_key(key): return self.__class__(da, args, key)

	results=da(args)
	if results:
	    if len(results) > 1:
		try: return results[atoi(key)].__of__(da)
		except: raise KeyError, key
	else: raise KeyError, key
	r=self._r=results[0].__of__(da)
	if key is self: return r

	if hasattr(r,'__bobo_traverse__'):
	    try: return r.__bobo_traverse__(REQUEST, key)
	    except: pass

	try: return getattr(r,key)
	except AttributeError, v:
	    if v!=key: raise AttributeError, v

	return r[key]

    def __getattr__(self, name):
	r=self.__dict__['_r']
	if hasattr(r, name): return getattr(r,name)
	return getattr(self.__dict__['_da'], name)


braindir=SOFTWARE_HOME+'/Extensions'    

modules={}

def getBrain(self,
	     ):
    'Check/load a class'
    
    module=self.class_file_
    class_name=self.class_name_

    if not module and not class_name:
	c=Aqueduct.RDB.NoBrains
	self._v_brain=c
	return c
	
    if modules.has_key(module):
	m=modules[module]
    else:
	d,n = os.path.split(module)
	if d: raise ValueError, (
	    'The file name, %s, should be a simple file name' % module)
	m={}
	exec open("%s/%s.py" % (braindir, module)) in m
	modules[module]=m

    if not m.has_key(class_name): raise ValueError, (
	'The class, %s, is not defined in file, %s' % (class_name, module))

    c=m[class_name]
    if not hasattr(c,'__bases__'):raise ValueError, (
	'%s, is not a class' % class_name)

    self._v_brain=c
    
    return c

############################################################################## 
#
# $Log: DA.py,v $
# Revision 1.50  1998/07/12 23:15:09  jim
# Changed editing screen:
#   - size prefs now separate from Document prefs
#   - Fized bug that caused src changes to be lost
#
# Revision 1.49  1998/07/12 21:01:20  jim
# Added support for DA's that return data directly as list of item descriptions
# (i.e. schema) and list of rows.
#
# Began adding support for pickle-based network protocol that, alas, may
# fall by the wayside. Waaaa.
#
# Revision 1.48  1998/06/26 21:51:28  jim
# Added resize buttons.
#
# Revision 1.47  1998/05/11 15:00:13  jim
# Updated permissions.
#
# Revision 1.46  1998/05/08 15:00:27  jim
# Changed permission settings to be in line with new machinery.
#
# Revision 1.45  1998/04/29 21:17:51  jim
# Changed to use acquired parent.
#
# Revision 1.44  1998/04/27 18:59:56  jim
# Now use exported sql_quote__ function to quote strings.
#
# Revision 1.43  1998/04/27 18:56:13  jim
# Now export an sql_quote function that is used by sqlvar and sqltest
# to quote strings.
#
# Revision 1.42  1998/04/27 18:31:32  jim
# Changed the way quoting was exported.
#
# Revision 1.41  1998/04/27 16:11:11  jim
# Stuff DA into template dict so that sqlvar and sqltest can use it.
#
# Revision 1.40  1998/03/18 13:45:04  jim
# Added doc strings.
#
# Revision 1.39  1998/03/17 21:16:08  brian
# Changed __call__ to detect whether it is being called via the
# web, or via dtml, and bind itself accordingly.
#
# Revision 1.38  1998/03/17 19:29:05  jim
# Added support for sqlvar, sqltest, and sqlgroup tags.
#
# Changed the way template is invoked, so that the 'self' is the
# folder containing the method.
#
# Revision 1.37  1998/03/10 21:18:03  jim
# Traversal not stops when all arguments have been given.
#
# Revision 1.36  1998/02/23 14:41:26  jim
# Added code to remove module from cache on reload.
#
# Revision 1.35  1998/02/20 22:25:35  jim
# Fixed up traversal machinery to work correctly with acquisition,
# especially method acquisition.
#
# Revision 1.34  1998/02/18 23:46:53  jim
# Added reparenting magic for NE interface.
#
# Revision 1.33  1998/01/28 18:14:40  jim
# Added logic to clear cache on edit.
#
# Revision 1.32  1998/01/28 18:13:48  jim
# Fixed bug in clearing cache.
#
# Revision 1.31  1998/01/28 16:04:40  jim
# Removed Cancel button from test input form.
#
# Revision 1.30  1998/01/27 20:08:19  jim
# Fixed bugs in caching logic.
#
# Revision 1.29  1998/01/27 18:37:39  jim
# Changed the way that errors are reported.
#
# Revision 1.28  1998/01/26 21:40:41  jim
# Fixed bug in caching code.
#
# Revision 1.27  1998/01/22 20:50:53  jim
# Fixed stupid typo in text output form.
#
# Revision 1.26  1998/01/22 20:32:50  jim
# Fixed bug in testing code and added output of SQL query.
#
# Revision 1.25  1998/01/21 22:59:34  jim
# Updated for latest security model.
#
# Revision 1.24  1998/01/21 20:56:55  brian
# Changed Access Control tab to Security
#
# Revision 1.23  1998/01/16 21:33:48  jim
# Now pass self to RDB.File so record constructors can acquire.
#
# Revision 1.22  1998/01/12 20:02:23  jim
# Added support for keyword arguments to methods.
#
# Revision 1.21  1998/01/09 21:58:25  jim
# Fixed bug in handling of arguments.
#
# Revision 1.20  1998/01/09 20:37:40  jim
# Fixed stupid bug in manage_test.
#
# Revision 1.19  1998/01/08 21:28:21  jim
# Fixed to show errors when run in testing mode.
#
# Revision 1.18  1998/01/07 16:27:16  jim
# Brought up to date with latest Principia models.
#
# Revision 1.17  1997/12/18 13:35:31  jim
# Added ImageFile usage.
#
# Revision 1.16  1997/12/05 21:33:13  jim
# major overhall to add record addressing, brains, and support for new interface
#
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
