
'''$Id: db.py,v 1.2 1998/05/21 15:33:56 jim Exp $'''
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
# 
__version__='$Revision: 1.2 $'[11:-2]

import string, sys, os
from string import strip, split, find, join
from gadfly import gadfly
import Globals

data_dir=os.path.join(Globals.data_dir,'gadfly')

def manage_DataSources():
    
    if not os.path.exists(data_dir):
        try:
            os.mkdir(data_dir)
            os.mkdir(os.path.join(data_dir,'demo'))
        except:
            raise 'Gadfly Error', (
                """
                The Aqueduct Gadfly Database Adapter requires the
                existence of the directory, <code>%s</code>.  An error
                occurred  while trying to create this directory.
                """ % data_dir)
    if not os.path.isdir(data_dir):
        raise 'Gadfly Error', (
            """
            The Aqueduct Gadfly Database Adapter requires the
            existence of the directory, <code>%s</code>.  This
            exists, but is not a directory.
            """ % data_dir)
    
    return map(
	lambda d: (d,''),
	filter(lambda f, i=os.path.isdir, d=data_dir, j=os.path.join:
	       i(j(d,f)),
	       os.listdir(data_dir))
	)

class DB:

    database_error=gadfly.error

    def tables(self,*args,**kw):
	return map(lambda name: {
	    'TABLE_NAME': name,
	    'TABLE_TYPE': 'TABLE',
	    }, self.db.table_names())

    def columns(self, table_name):
	return map(lambda col: {
	    'Name': col.colid, 'Type': col.datatype, 'Precision': 0,
	    'Scale': 0, 'Nullable': 'with Null'
	    }, self.db.database.datadefs[table_name].colelts)

    def __init__(self,connection):
	path=os.path
	dir=path.join(data_dir,connection)
	if not path.isdir(dir):
	    raise self.database_error, 'invalid database error, ' + connection

	if not path.exists(path.join(dir,connection+".gfd")):
	    db=gadfly.gadfly()
	    db.startup(connection,dir)
	else: db=gadfly.gadfly(connection,dir)

	self.connection=connection
	self.db=db
	self.cursor=db.cursor()

    def query(self,query_string, max_rows=9999999):
	self._register()
	c=self.db.cursor()
	queries=filter(None, map(strip,split(query_string, '\0')))
	if not queries: raise 'Query Error', 'empty query'
	names=None
	result='cool\ns\n'
	for qs in queries:
	    c.execute(qs)
	    d=c.description
	    if d is None: continue
	    if names is not None:
		raise 'Query Error', (
		    'select in multiple sql-statement query'
		    )
	    names=map(lambda d: d[0], d)
	    results=c.fetchmany(max_rows)
	    nv=len(names)
	    indexes=range(nv)
	    row=['']*nv
	    defs=[maybe_int]*nv
	    j=join
	    rdb=[j(names,'\t'),None]
	    append=rdb.append
	    for result in results:
		for i in indexes:
		    try: row[i]=defs[i](result[i])
		    except NewType, v: row[i], defs[i] = v
		append(j(row,'\t'))
	    rdb[1]=j(map(lambda d, Defs=Defs: Defs[d], defs),'\t')
	    rdb.append('')
	    result=j(rdb,'\n')

	return result

    class _p_jar:
	# This is place holder for new transaction machinery 2pc
	def __init__(self, db=None): self.db=db
	def begin_commit(self, *args): pass
	def finish_commit(self, *args): pass

    _p_jar=_p_jar(_p_jar())

    _p_oid=_p_changed=_registered=None
    def _register(self):
	if not self._registered:
	    try:
		get_transaction().register(self)
		self._registered=1
	    except: pass

    def __inform_commit__(self, *ignored):
	self.db.commit()
	self._registered=0

    def __inform_abort__(self, *ignored):
	self.db.rollback()
	self.db.checkpoint()
	self._registered=0


NewType="Excecption to raise when sniffing types, blech"
def maybe_int(v, int_type=type(0), float_type=type(0.0), t=type):
    t=t(v)
    if t is int_type: return str(v)
    if v is None or v=='': return ''
    if t is float_type: raise NewType, (maybe_float(v), maybe_float)

    raise NewType, (maybe_string(v), maybe_string)

def maybe_float(v, int_type=type(0), float_type=type(0.0), t=type):
    t=t(v)
    if t is int_type or t is float_type: return str(v)
    if v is None or v=='': return ''

    raise NewType, (maybe_string(v), maybe_string)

def maybe_string(v):
    v=str(v)
    if find(v,'\t') >= 0 or find(v,'\t'):
	raise NewType, (must_be_text(v), must_be_text)
    return v

def must_be_text(v, f=find, j=join, s=split):
    if f(v,'\\'):
	v=j(s(v,'\\'),'\\\\')
	v=j(s(v,'\t'),'\\t')
	v=j(s(v,'\n'),'\\n')
    return v

Defs={maybe_int: 'i', maybe_float:'n', maybe_string:'s', must_be_text:'t'}


##########################################################################
#
# $Log: db.py,v $
# Revision 1.2  1998/05/21 15:33:56  jim
# Added logic to set up gadfly area on first use.
#
# Revision 1.1  1998/04/15 15:10:41  jim
# initial
#
# Revision 1.3  1997/08/06 18:21:27  jim
# Renamed description->title and name->id and other changes
#
# Revision 1.2  1997/08/06 14:29:35  jim
# Changed to use abstract dbi base.
#
