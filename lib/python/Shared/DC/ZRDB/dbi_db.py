#!/usr/local/bin/python 
# $What$

__doc__='''short description


$Id: dbi_db.py,v 1.3 1997/09/11 23:53:28 jim Exp $'''
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
# $Log: dbi_db.py,v $
# Revision 1.3  1997/09/11 23:53:28  jim
# Made RDB rendered remove 'l' from ends if ints.
#
# Revision 1.2  1997/08/06 14:26:45  jim
# *** empty log message ***
#
# Revision 1.1  1997/08/06 14:24:41  jim
# *** empty log message ***
#
# Revision 1.1  1997/07/25 15:49:42  jim
# initial
#
# Revision 1.1  1997/01/27 22:11:16  jim
# *** empty log message ***
#
#
# 
__version__='$Revision: 1.3 $'[11:-2]

import string, sys

failures=0
calls=0

nonselect_desc=[
    ('Query',  'STRING', 62, 62, 0, 0, 1),
    ('Status', 'STRING', 12, 12, 0, 0, 1),
    ('Calls',  'STRING', 12, 12, 0, 0, 1),
    ]

class DB:

    defs={'STRING':'s', 'NUMBER':'n', 'DATE':'d'}

    def Database_Connection(self, string):
	# Create a dbi-compatible database connection
	raise 'ImplementedBySubclass', (
	    'attempt to create a database connection for an abstract dbi')

    Database_Error='Should be overriden by subclass'

    def __init__(self,connection):
	self.connection=connection
	db=self.db=self.Database_Connection(connection)
	self.cursor=db.cursor()
	
    def str(self,v, StringType=type('')):
	if v is None: return ''
	r=str(v)
	if r[-1:]=='L' and type(v) is not StringType: r=r[:-1]
	return r

    def query(self,query_string):
	global failures, calls
	calls=calls+1
	try:
	    c=self.cursor
	    queries=filter(None,
			   map(string.strip,string.split(query_string, '\0')))
	    if not queries: raise 'Query Error', 'empty query'
	    if len(queries) > 1:
		result=[]
		for qs in queries:
		    r=c.execute(qs)
		    if r is None: raise 'Query Error', (
			'select in multiple sql-statement query'
			)
		    result.append((qs, str(`r`), calls))
		desc=nonselect_desc
	    else:
		query_string=queries[0]
		r=c.execute(query_string)
		if r is None:
		    result=c.fetchall()
		    desc=c.description
		else:
		    result=((query_string, str(`r`), calls),)
		    desc=nonselect_desc
	    failures=0
	    c.close()
	    self.db.commit()
	except self.Database_Error, mess:
	    c.close()
	    self.db.rollback()
	    failures=failures+1
	    if ((string.find(mess,": invalid") < 0 and
		 string.find(mess,"PARSE") < 0) or
		# DBI IS stupid
		string.find(mess,"Error while trying to retrieve text for error") > 0 or
		# If we have a large number of consecutive failures, our connection
		# is probably dead.
		failures > 100
		):
		# Hm. maybe the db is hosed.  Let's try once to restart it.
		failures=0
		c.close()
		self.db.close()
		db=self.db=self.Database_Connection(self.connection)
		self.cursor=db.cursor()
		c=self.cursor
		c.execute(query_string)
		result=c.fetchall()
		desc=c.description
	    else: raise sys.exc_type, sys.exc_value, sys.exc_traceback
	
	if result:
	    result=string.joinfields(
		    map(
			lambda row, self=self:
			string.joinfields(map(self.str,row),'\t'),
			result),
		    '\n')+'\n'
	else:
	    result=''

	return (
	    "%s\n%s\n%s" % (
		string.joinfields(map(lambda d: d[0],desc), '\t'),
		string.joinfields(
		    map(
			lambda d, defs=self.defs: "%d%s" % (d[2],defs[d[1]]),
			desc),
		    '\t'),
		result,
		)
	    )
	    

def main():
    import timing
    db=DB('zedweb/web404t@prod3')
    
    timing.start()
    # print db.query("select * from alt_items where d046d='001346305'")
    print db.query(
	"select * from CONTRACT_DETAILS"
	" where D046D='011302768' AND"
	" (K001='DDS' or K001='DDK' or K001='FTR' or K001='DDM' or K001='DDT')"
	)
    timing.finish()
    print timing.milli()/1000.0

if __name__ == "__main__": main()
