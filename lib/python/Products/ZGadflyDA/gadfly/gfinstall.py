#!/usr/local/bin/python

"""Gadfly installation script.

Build the sql grammar.

usage
  python <thismodule>
for a simple install or
  python <thismodule> force
for a full rebuild (with grammar regeneration).

In the current directory find or create sql.mar and sqlwhere.py
where sql.mar has the marshalled grammar data structures
for parsing sql and sqlwhere.py is a module that indicates
where the grammar file is as value of sqlwhere.filename.
"""

marfile = "sql.mar"
modfile = "sqlwhere.py"

print __doc__

from os import getcwd, path
cwd = getcwd()

modtemplate ="""
'''this module indicates where the sql datastructures are marshalled
   Auto generated on install: better not touch!
'''

filename = %s
"""

#wheremod = cwd + "/" + modfile
#where = cwd + "/" + marfile
wheremod = path.join(cwd, modfile)
where = path.join(cwd, marfile)
print
print "now creating", wheremod
f = open(wheremod, "w")
f.write( modtemplate % (`where`,) )
f.close()

from sqlgen import BuildSQL, getSQL
import sys
argv = sys.argv
force = 0
#print argv
if len(argv)>1 and argv[1]=="force":
   force = 1
if not force:
   try:
       sql = getSQL()
   except:
       print "exception", sys.exc_type, sys.exc_value
       print "during load of SQL grammar structures."
       print "Apparently the SQL grammar requires regeneration"
       force = 1
if force:
   print "now generating parser structures (this might take a while)..."
   #where = cwd + "/" + marfile
   print "building in", where
   sql = BuildSQL(where)
print
print "done."

