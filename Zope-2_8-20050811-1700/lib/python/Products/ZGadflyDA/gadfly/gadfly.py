
"""main entry point for gadfly sql."""

import sqlgen, sqlbind
sql = sqlgen.getSQL()
sql = sqlbind.BindRules(sql)

error = "gadfly_error"
verbosity = 0

class gadfly:
   """as per the DBAPI spec "gadfly" is the connection object."""
   closed = 0
   verbose = verbosity # debug!
   
   def __init__(self, databasename=None, directory=None, 
         forscratch=0, autocheckpoint=1, verbose=0):
       verbose = self.verbose = self.verbose or verbose
       # checkpoint on each commit if set
       self.autocheckpoint = autocheckpoint
       if verbose:
           print "initializing gadfly instance", (\
              databasename, directory, forscratch, verbose)
       self.is_scratch = forscratch
       self.databasename=databasename
       self.directory = directory
       self.fs = None
       self.database = None
       # db global transaction id
       self.transid = 0
       if databasename is not None:
          self.open()
          
   def transaction_log(self):
       from gfdb0 import Transaction_Logger
       if self.verbose:
          print "new transaction log for", self.transid
       return Transaction_Logger(self.database.log, self.transid, self.is_scratch)
          
   # causes problems in 1.5?
   #def __del__(self):
   #    """clear database on deletion, just in case of circularities"""
   #    # implicit checkpoint
   #    if self.verbose:
   #        print "deleting gadfly instance", self.databasename
   #    if not self.closed:
   #        self.close()
       
   def checkpoint(self):
       """permanently record committed updates"""
       # note: No transactions should be active at checkpoint for this implementation!
       # implicit abort of active transactions!
       verbose = self.verbose
       if verbose:
           print "checkpointing gadfly instance", self.databasename
       db = self.database
       log = db.log
       # dump committed db to fs
       fs = self.fs
       if fs and db and not db.is_scratch:
           # flush the log
           if log: 
               if verbose: print "gadfly: committing log"
               log.commit()
           elif verbose:
               print "gadfly: no log to commit"
           if verbose: print "gadfly: dumping mutated db structures"
           fs.dump(db)
       elif verbose:
           print "gadfly: no checkpoint required"
       if verbose:
           print "gadfly: new transid, reshadowing"
       self.transid = self.transid+1
       self.working_db.reshadow(db, self.transaction_log())
          
   def startup(self, databasename, directory, scratch=0, verbose=0):
       from gfdb0 import Database0, File_Storage0
       verbose = self.verbose
       if verbose:
           print "gadfly: starting up new ", databasename
       if self.database:
           raise error, "cannot startup, database bound"
       self.databasename=databasename
       self.directory = directory
       db = self.database = Database0()
       db.is_scratch = scratch or self.is_scratch
       self.fs = File_Storage0(databasename, directory)
       self.working_db = Database0(db, self.transaction_log())
       # commit initializes database files and log structure
       self.commit()
       # for now: all transactions serialized
       #  working db shared among all transactions/cursors
       self.transid = self.transid+1
       self.working_db = Database0(db, self.transaction_log())
       
   def restart(self):
       """reload and rerun committed updates from log, discard uncommitted"""
       # mainly for testing recovery.
       if self.verbose:
           print "gadfly: restarting database", self.databasename
       self.database.clear()
       self.working_db.clear()
       self.working_db = None
       self.database = None
       self.open()
          
   def open(self):
       """(re)load existing database"""
       if self.verbose:
           print "gadfly: loading database", self.databasename
       from gfdb0 import File_Storage0, Database0
       if self.directory:
           directory = self.directory
       else:
           directory = "."
       fs = self.fs = File_Storage0(self.databasename, directory)
       db = self.database = fs.load(sql)
       self.transid = self.transid+1
       self.working_db = Database0(db, self.transaction_log())
       
   def add_remote_view(self, name, definition):
       """add a remote view to self.
          Must be redone on each reinitialization!
          Must not recursively reenter the query evaluation process for
          this database!
          "Tables" added in this manner cannot be update via SQL.
       """
       self.database[name] = definition
       self.working_db[name] = definition
       
   def close(self):
       """checkpoint and clear the database"""
       if self.closed: return
       if self.verbose:
           print "gadfly: closing database", self.databasename
       db = self.database
       if not db.is_scratch:
           self.checkpoint()
       if db: db.clear()
       wdb = self.working_db
       if wdb:
           wdb.clear()
       self.working_db = None
       self.closed = 1
       
   def commit(self):
       """commit the working database+transaction, flush log, new transid"""
       verbose = self.verbose
       autocheckpoint = self.autocheckpoint
       if self.verbose:
           print "gadfly: committing", self.transid, self.databasename
       self.transid = self.transid+1
       fs = self.fs
       db = self.database
       wdb = self.working_db
       wdblog = wdb.log
       if wdblog: wdblog.commit()
       wdb.commit()
       if fs and db and not db.is_scratch:
          if autocheckpoint:
              if verbose:
                  print "gadfly: autocheckpoint"
              # skips a transid?
              self.checkpoint()
          else:
              if verbose:
                  print "gadfly: no autocheckpoint"
              wdb.reshadow(db, self.transaction_log())
       else:
          if verbose:
              print "gadfly: scratch db, no logging, just reshadow"
          wdb.reshadow(db, self.transaction_log())
          
   def rollback(self):
       """discard the working db, new transid, recreate working db"""
       verbose = self.verbose
       if verbose:
           print "gadfly: rolling back", self.transid, self.databasename
       if not (self.fs or self.database):
          raise error, "unbound, cannot rollback"
       # discard updates in working database
       self.working_db.clear()
       self.transid = self.transid+1
       self.working_db.reshadow(self.database, self.transaction_log())
       #self.open()
       
   def cursor(self):
       if self.verbose:
           print "gadfly: new cursor", self.databasename
       db = self.database
       if db is None:
          raise error, "not bound to database"
       return GF_Cursor(self)
       
   def dumplog(self):
       log = self.database.log
       if log:
           log.dump()
       else:
           print "no log to dump"
           
   def table_names(self):
       return self.working_db.relations()
       
   def DUMP_ALL(self):
       print "DUMPING ALL CONNECTION DATA", self.databasename, self.directory
       print
       print "***** BASE DATA"
       print
       print self.database
       print
       print "***** WORKING DATA"
       print
       print self.working_db
       

class GF_Cursor:

   verbose = verbosity

   arraysize = None
   
   description = None
   
   EVAL_DUMP = 0 # only for extreme debugging!
   
   def __init__(self, gadfly_instance):
       verbose = self.verbose = self.verbose or gadfly_instance.verbose
       if verbose:
           print "GF_Cursor.__init__", id(self)
       self.connection = gadfly_instance
       self.results = None
       self.resultlist = None
       self.statement = None
       # make a shadow of the shadow db! (in case of errors)
       from gfdb0 import Database0
       self.shadow_db = Database0()
       self.reshadow()
       self.connection = gadfly_instance
       
   def reshadow(self):
       if self.verbose:
          print "GF_Cursor.reshadow", id(self)
       db = self.connection.working_db
       shadow = self.shadow_db
       shadow.reshadow(db, db.log)
       if self.verbose:
          print "rels", shadow.rels.keys()
       
   def close(self):
       if self.verbose:
           print "GF_Cursor.close", id(self)
       self.connection = None
       
   def reset_results(self):
       if self.verbose:
           print "GF_Cursor.reset_results", id(self)
       rs = self.results
       if rs is None:
           raise error, "must execute first"
       if len(rs)!=1:
           raise error, "cannot retrieve multiple results"
       rel = rs[0]
       rows = rel.rows()
       atts = rel.attributes()
       tupatts = tuple(atts)
       resultlist = list(rows)
       if len(tupatts)==1:
           att = tupatts[0]
           for i in xrange(len(resultlist)):
              resultlist[i] = (resultlist[i][att],)
       else:
           for i in xrange(len(resultlist)):
              resultlist[i] = resultlist[i].dump(tupatts)
       self.resultlist = resultlist
       
   def fetchone(self):
       if self.verbose:
           print "GF_Cursor.fetchone", id(self)
       r = self.resultlist
       if r is None:
          self.reset_results()
          r = self.resultlist
       if len(r)<1:
          raise error, "no more results"
       result = r[0]
       del r[0]
       return result
       
   def fetchmany(self, size=None):
       if self.verbose:
           print "GF_Cursor.fetchmany", id(self)
       r = self.resultlist
       if r is None:
           self.reset_results()
           r = self.resultlist
       if size is None:
           size = len(r)
       result = r[:size]
       del r[:size]
       return result
       
   def fetchall(self):
       if self.verbose:
           print "GF_Cursor.fetchall", id(self)
       return self.fetchmany()
       
   def execute(self, statement=None, params=None):
       """execute operations, commit results if no error"""
       success = 0
       verbose = self.verbose
       if verbose:
           print "GF_Cursor.execute", id(self)
       if statement is None and self.statement is None:
           raise error, "cannot execute, statement not bound"
       if statement!=self.statement:
           if verbose: print "GF_cursor: new statement: parsing"
           # only reparse on new statement.
           self.statement=statement
           from sqlsem import Parse_Context
           context = Parse_Context()
           cs = self.commands = sql.DoParse1(statement, context)
       else:
           if verbose: print "GF_cursor: old statment, not parsing"
           cs = self.commands
       # always rebind! (db may have changed)
       if verbose: print "GF_Cursor: binding to temp db"
       # make a new shadow of working db
       # (should optimize?)
       self.reshadow()
       # get shadow of working database
       database = self.shadow_db
       if self.EVAL_DUMP:
           print "***"
           print "*** dumping connection parameters before eval"
           print "***"
           print "*** eval scratch db..."
           print
           print database
           print
           print "*** connection data"
           print
           self.connection.DUMP_ALL()
           print "********** end of eval dump"
       for i in xrange(len(cs)):
           if verbose:
              print "GFCursor binding\n", cs[i]
              print database.rels.keys()
           cs[i] = cs[i].relbind(database)
       cs = self.commands
       self.results = results = list(cs)
       # only unshadow results on no error
       try:
           for i in xrange(len(cs)):
               results[i] = cs[i].eval(params)
           success = 1
       finally:
           #print "in finally", success
           # only on no error...
           if success:
               # commit updates in shadow of working db (not in real db)
               if verbose: print "GFCursor: successful eval, storing results in wdb"
               database.log.flush()
               # database commit does not imply transaction commit.
               database.commit()
           else:
               if verbose:
                   print \
   "GFCursor: UNSUCCESSFUL EVAL, discarding results and log entries"
               self.statement = None
               self.results = None
               self.resultlist = None
               database.log.reset()
       # handle curs.description
       self.description = None
       if len(results)==1:
          result0 = results[0]
          try:
              atts = result0.attributes()
          except:
              pass
          else:
              descriptions = list(atts)
              fluff = (None,) * 6
              for i in xrange(len(atts)):
                  descriptions[i] = (atts[i],) + fluff
              self.description = tuple(descriptions)
       self.resultlist = None
       
   def setoutputsize(self, *args):
       # not implemented
       pass
       
   def setinputsizes(self, *args):
       # not implemented
       pass
           
   def pp(self):
       """return pretty-print string rep of current results"""
       from string import join
       stuff = map(repr, self.results)
       return join(stuff, "\n\n")
       
