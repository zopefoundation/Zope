"""storage objects"""

verbosity = 0

import os

# use whatever kjbuckets sqlsem is using
#from sqlsem import kjbuckets, maketuple

# error on checking of data integrity
StorageError = "StorageError"

# use md5 checksum (stub if md5 unavailable?)
def checksum(string):
    from md5 import new
    return new(string).digest()
    
def recursive_dump(data, prefix="["):
    """for debugging"""
    from types import StringType
    if type(data) is StringType: 
       #print prefix, data
       return
    p2 = prefix+"["
    try:
        for x in data:
            recursive_dump(x, p2)
    except:
        print prefix, data
        
def checksum_dump(data, file):
    """checksum and dump marshallable data to file"""
    #print "checksum_dump", file
    #recursive_dump(data)
    from marshal import dumps, dump
    #print "data\n",data
    storage = dumps(data)
    checkpair = (checksum(storage), storage)
    dump(checkpair, file)

def checksum_undump(file):
    """undump marshallable data from file, checksum"""
    from marshal import load, loads
    checkpair = load(file)
    (check, storage) = checkpair
    if checksum(storage)!=check:
       raise StorageError, "data load checksum fails"
    data = loads(storage)
    return data
    
def backup_file(filename, backupname):
    """backup file, if unopenable ignore"""
    try:
        f = open(filename, "rb")
    except:
        return
    data = f.read()
    f.close()
    f = open(backupname, "wb")
    f.write(data)
    f.close()
    
def del_file(filename):
    """delete file, ignore errors"""
    from os import unlink
    try:
        unlink(filename)
    except: 
        pass

class Database0:
   """quick and dirty in core database representation."""
   
   # db.log is not None == use db.log to log modifications
   
   # set for verbose prints
   verbose = verbosity
   
   # set for read only copy
   readonly = 0
   
   # set for temp/scratch db copy semantics
   is_scratch = 0
   
   # set to add introspective tables
   introspect = 1
   
   def __init__(self, shadowing=None, log=None):
       """dictionary of relations."""
       verbose = self.verbose
       self.shadowing = shadowing
       self.log = log
       self.touched = 0
       if log:
           self.is_scratch = log.is_scratch
       if shadowing and not log:
           raise ValueError, "shadowing db requires log"
       if verbose:
           print "Database0 init"
           if log:
               log.verbose = 1
       if shadowing:
           # shadow structures of shadowed db
           self.rels = shadow_dict(shadowing.rels, Relation0.unshadow)
           self.datadefs = shadow_dict(shadowing.datadefs)
           self.indices = shadow_dict(shadowing.indices)
       else:
           self.rels = {}
           self.datadefs = {}
           self.indices = {}
           if self.introspect:
               self.set_introspection()
               
   def set_introspection(self):
       import gfintrospect
       self["dual"] = gfintrospect.DualView()
       self["__table_names__"] = gfintrospect.RelationsView()
       self["__datadefs__"] = gfintrospect.DataDefsView()
       self["__indices__"] = gfintrospect.IndicesView()
       self["__columns__"] = gfintrospect.ColumnsView()
       self["__indexcols__"] = gfintrospect.IndexAttsView()
           
   def reshadow(self, db, dblog):
       """(re)make self into shadow of db with dblog"""
       self.shadowing = db
       self.log = dblog
       self.rels = shadow_dict(db.rels, Relation0.unshadow)
       self.datadefs = shadow_dict(db.datadefs)
       self.indices = shadow_dict(db.indices)
           
   def clear(self):
       """I'm not sure if database has circular structure, so this added"""
       self.shadowing = None
       self.log = None
       self.rels = {}
       self.datadefs = {}
       self.indices = {}
           
   def commit(self):
       """commit shadowed changes"""
       verbose = self.verbose
       if self.shadowing and self.touched:
          # log commit handled elsewhere
          #log = self.log
          #if log and not log.is_scratch:
              #if verbose: print "committing log"
              #self.log.commit(verbose)
          if verbose: print "committing rels"
          self.rels.commit(verbose)
          if verbose: print "committing datadefs"
          self.datadefs.commit(verbose)
          if verbose: print "committing indices"
          self.indices.commit(verbose)
          st = self.shadowing.touched
          if not st:
              if verbose: "print setting touched", self.touched
              self.shadowing.touched = self.touched
          elif verbose:
              print "shadowed database is touched"
       elif verbose:
          print "db0: commit on nonshadow instance"
       
   def __setitem__(self, name, relation):
       """bind a name (uppercased) to tuples as a relation."""
       from string import upper
       if self.indices.has_key(name):
          raise NameError, "cannot set index"
       self.rels[ upper(name) ] = relation
       if self.verbose: print "db0 sets rel", name
       
   def add_index(self, name, index):
       if self.rels.has_key(name):
          raise NameError, `name`+": is relation"
       self.indices[name] = index
       if self.verbose: print "db0 sets index", name
       
   def drop_index(self, name):
       if self.verbose: print "db0 drops index", name
       del self.indices[name]
       
   def __getitem__(self, name):
       if self.verbose: print "db0 gets rel", name
       from string import upper
       return self.rels[upper(name)]
       
   def get_for_update(self, name):
       """note: does not imply updates, just possibility of them"""
       verbose = self.verbose
       if verbose: print "db0 gets rel for update", name
       shadowing = self.shadowing
       gotit = 0
       from string import upper
       name = upper(name)
       rels = self.rels
       if shadowing:
           if rels.is_shadowed(name):
               test = rels[name]
               # do we really have a shadow or a db copy?
               if test.is_shadow:
                  gotit = 1
           if not gotit:
              if shadowing.has_relation(name):
                 test = shadowing.get_for_update(name)
              else:
                 # uncommitted whole relation
                 test = rels[name]
                 gotit = 1
       else:
           test = rels[name]
           gotit = 1
       if self.readonly:
           raise ValueError, "cannot update, db is read only"
       elif test.is_view:
           raise ValueError, "VIEW %s cannot be updated" % name
       elif shadowing and not gotit:
           if verbose: print "db0: making shadow for", name
           if test.is_shadow: return test
           shadow = Relation0(())
           shadow = shadow.shadow(test, self.log, name, self)
           rels[name] = shadow
           return shadow
       else:
           return test
       
   def __delitem__(self, name):
       if self.verbose: print "db0 drops rel", name
       from string import upper
       del self.rels[upper(name)]
       
   def relations(self):
       return self.rels.keys()
       
   def has_relation(self, name):
       return self.rels.has_key(name)
       
   def getdatadefs(self):
       result = self.datadefs.values()
       # sort to make create tables first, eg
       result.sort()
       return result
       
   def add_datadef(self, name, defn, logit=1):
       """only log the datadef if logit is set, else ignore redefinitions"""
       dd = self.datadefs
       if logit and dd.has_key(name):
          raise KeyError, `name`+": already defined"
       if logit:
          self.touched = 1
       dd[name] = defn
       
   def has_datadef(self, name):
       return self.datadefs.has_key(name)
       
   def drop_datadef(self, name):
       if self.verbose: print "db0 drops datadef",name
       dd = self.datadefs
       #print dd.keys()
       if not dd.has_key(name):
          raise KeyError, `name`+": no such element"
       del dd[name]
       
   def __repr__(self):
       l = []
       from string import join
       l.append("INDICES: "+`self.indices.keys()`)
       for (name, ddef) in self.datadefs.items():
           l.append("data definition %s::\n%s" % (name, ddef))
       for (name, rel) in self.rels.items():
           l.append(name + ":")
           l.append(rel.irepr())
       return join(l, "\n\n")
       
   def bindings(self, fromlist):
       """return (attdict, reldict, amb, ambatts) from fromlist = [(name,alias)...]
          where reldict: alias --> tuplelist
                attdict: attribute_name --> unique_relation
                amb: dict of dottedname --> (rel, att)
                ambatts: dict of ambiguous_name --> witness_alias
       """
       from string import upper
       rels = self.rels
       ambiguous_atts = {}
       ambiguous = {}
       relseen = {}
       attbindings = {}
       relbindings = {}
       for (name,alias) in fromlist:
           name = upper(name)
           alias = upper(alias)
           if relseen.has_key(alias):
              raise NameError, `alias` + ": bound twice in from list"
           relseen[alias]=alias
           try:
               therel = rels[name]
           except KeyError:
               raise NameError, `name` + " no such relation in DB"
           relbindings[alias] = therel
           for attname in therel.attributes():
               if not ambiguous_atts.has_key(attname):
                  if attbindings.has_key(attname):
                     oldrel = attbindings[attname]
                     oldbind = (oldrel, attname)
                     ambiguous[ "%s.%s" % oldbind] = oldbind
                     del attbindings[attname]
                     ambiguous_atts[attname]=alias
                     newbind = (alias, attname)
                     ambiguous[ "%s.%s" % newbind ] = newbind
                  else:
                     attbindings[attname] = alias
               else:
                  newbind = (alias, attname)
                  ambiguous[ "%s.%s" % newbind ] = newbind
       return (attbindings, relbindings, ambiguous, ambiguous_atts)
       
class File_Storage0:
   """quick and dirty file storage mechanism.
        relation names in directory/dbname.gfd
          contains a white separated list of relation names
        relations in directory/relname.grl
          contains sequence of marshalled tuples reps
          prefixed by marshalled list of atts
   """
   
   verbose = verbosity
   
   def __init__(self, dbname, directory):
       """directory must exist."""
       if self.verbose: print "fs0 init:", dbname, directory
       self.dbname = dbname
       self.directory = directory
       self.relation_implementation = Relation0
       self.recovery_mode = 0
       
   def load(self, parser=None, forscratch=0):
       # if logfile is present, need to recover
       # error condition: fail to load relation, ddf, but no log file!
       logfile = self.logfilename()
       blogfile = self.backup_logfilename()
       verbose = self.verbose
       if verbose: print "fs0 load, checking", logfile
       try:
           testlog = open(logfile, "rb")
           if verbose: print "fs0: opened", testlog
           testlog.close()
           testlog = open(blogfile, "rb")
           testlog.close()
           testlog = None
       except:
           recovery_mode = self.recovery_mode = 0
           if verbose: print "recovery not needed"
       else:
           recovery_mode = self.recovery_mode = 1
           if verbose: print "FS0 RECOVERY MODE LOAD!"
       resultdb = Database0()
       resultdb.is_scratch = forscratch
       commands = self.get_initstatements()
       #commands = parser.DoParse1(initstatements)
       for command in commands:
           if verbose: print "fs0 evals", command
           command.relbind(resultdb)
           command.eval()
       for name in resultdb.relations():
           if verbose: print "fs0 loads rel", name
           rel = resultdb[name]
           if rel.is_view:
              # don't need to load views
              continue
           rel.set_empty()
           try:
               data = self.get_relation(name)
           except StorageError, detail:
               raise StorageError, "load failure %s: %s" % (name, detail)
           attsin = tuple(data.attributes())
           attsout = tuple(rel.attributes())
           if attsin!=attsout:
               raise StorageError, "rel %s: atts %s don't match %s" % (
                  name, attsin, attsout)
           rel.add_tuples( data.rows() )
           # in sync!
           rel.touched = 0
       # db in sync
       resultdb.touched = 0
       # do recovery, if needed
       if recovery_mode:
           if verbose: print "fs0 recovering from logfile", logfile
           # restart the log file only if db is not scratch
           restart = not forscratch
           Log = DB_Logger(logfile, blogfile)
           if verbose: Log.verbose=1
           Log.recover(resultdb, restart)
           # do a checkpoint
           self.recovery_mode = 0
           if restart and not forscratch:
               Log.shutdown()
               Log = None
               del_file(logfile)
               if verbose: print "FS0: dumping database"
               self.dump(resultdb)
               Log = resultdb.log = DB_Logger(logfile, blogfile)
               Log.startup()
       elif not forscratch:
           Log = DB_Logger(logfile, blogfile)
           Log.startup()
           resultdb.log = Log
       return resultdb
       
   def relfilename(self, name):
       #return "%s/%s.grl" % (self.directory, name)
       return os.path.join(self.directory, name+".grl")
       
   def backup_relfilename(self, name):
       #return "%s/%s.brl" % (self.directory, name)
       return os.path.join(self.directory, name+".brl")
       
   def relfile(self, name, mode="rb"):
       if self.recovery_mode:
           return self.getfile_fallback(
        self.backup_relfilename(name), self.relfilename(name), mode)
       else:
           name = self.relfilename(name)
           return open(name, mode)
           
   def getfile_fallback(self, first, second, mode):
       try:
           return open(first, mode)
       except:
           return open(second, mode)
       
   def get_relation(self, name):
       f = self.relfile(name, "rb")
       rel = self.relation_implementation(())
       try:
           rel.load(f)
       except StorageError:
           if self.recovery_mode:
               f = open(self.relfilename(name), "rb")
               rel.load(f)
           else:
               raise StorageError, \
  "fs: could not unpack backup rel file or rel file in recovery mode: "+name
       return rel
       
   def dbfilename(self):
       #return "%s/%s.gfd" % (self.directory, self.dbname)
       return os.path.join(self.directory, self.dbname+".gfd")
       
   def backup_dbfilename(self):
       #return "%s/%s.bfd" % (self.directory, self.dbname)
       return os.path.join(self.directory, self.dbname+".bfd")
       
   def logfilename(self):
       #return "%s/%s.gfl" % (self.directory, self.dbname)
       return os.path.join(self.directory, self.dbname+".gfl")
       
   def backup_logfilename(self):
       #return "%s/%s.glb" % (self.directory, self.dbname)
       return os.path.join(self.directory, self.dbname+".glb")
       
   def get_initstat_file(self, mode):
       if self.recovery_mode:
           return self.getfile_fallback(
            self.backup_dbfilename(), self.dbfilename(), mode)
       else:
           return open(self.dbfilename(), mode)
       
   def get_initstatements(self):
       f = self.get_initstat_file("rb")
       if self.verbose:
           print "init statement from file", f
       try:
           data = checksum_undump(f)
       except StorageError:
           if self.recovery_mode:
               f = open(self.dbfilename, "rb")
               data = checksum_undump(f)
           else:
               raise StorageError, \
  "could not unpack ddf backup or ddf file in recovery mode: "+self.dbname
       f.close()
       from sqlsem import deserialize
       stats = map(deserialize, data)
       return stats
       
   def dump(self, db):
       """perform a checkpoint (no active transactions!)"""
       # db should be non-shadowing db
       # first thing: back up the log
       backup_file(self.logfilename(), self.backup_logfilename())
       verbose = self.verbose
       if verbose: print "fs0: checkpointing db"
       if db.is_scratch or db.readonly:
           # don't need to do anything.
           if verbose: print "fs0: scratch or readonly, returning"
           return
       log = db.log
       if log:
           log.commit()
           if verbose:
               print "DEBUG LOG TRACE"
               log.dump()
           log.shutdown()
       if db.touched:
           if verbose: print "fs0: db touched, backing up ddf file"
           backup_file(self.dbfilename(), 
                       self.backup_dbfilename())
       relations = db.relations()
       for r in relations:
           rel = db[r]
           #print r
           if rel.touched:
               if verbose: print "fs0: backing up touched rel", r
               backup_file(self.relfilename(r), 
                           self.backup_relfilename(r))
       for r in relations:
           if verbose: print "fs0: dumping relations now"
           self.dumprelation(r, db[r])
       if verbose: print "fs0: dumping datadefs now"
       self.dumpdatadefs(db)
       # del of logfile signals successful commit.
       if verbose: print "fs0: successful dump, deleting log file"
       logfilename = self.logfilename()
       blogfilename = self.backup_logfilename()
       del_file(logfilename)
       del_file(blogfilename)
       if db.touched:
           if verbose: print "fs0: deleting backup ddf file"
           del_file(self.backup_dbfilename())
           db.touched = 0
       for r in relations:
           rel = db[r]
           if rel.touched:
               if verbose: print "fs0: deleting rel backup", r
               del_file(self.backup_relfilename(r))
           rel.touched = 0
       if verbose: print "fs0: restarting db log"
       log = db.log = DB_Logger(logfilename, blogfilename)
       log.startup()
       if verbose: print "fs0: dump complete"
       self.recovery_mode = 0
       
   def dumprelation(self, name, rel, force=0):
       """set force to ignore the "touch" flag."""
       # ignore self.backup_mode
       if (force or rel.touched) and not rel.is_view:
           fn = self.relfilename(name)
           if self.verbose:
               print "dumping touched rel", name, "to", fn
           f = open(fn, "wb")
           rel.dump(f)
       
   def dumpdatadefs(self, db, force=0):
       """set force to ignore the touch flag"""
       # ignore self.backup_mode
       if not (force or db.touched): return
       #from marshal import dump, dumps
       fn = self.dbfilename()
       f = open(fn, "wb")
       datadefs = db.getdatadefs()
       from sqlsem import serialize
       datadefsd = map(serialize, datadefs)
       #for (defn, ser) in map(None, datadefs, datadefsd):
           #print defn
           #print ser
           #dumps(ser)  ### debug test
       checksum_dump(datadefsd, f)
       f.close()
       
class Relation0:
   """quick and dirty in core relation representation.
        self.tuples contains tuples or 0 if erased.
      tuples must not move (to preserve indices)
      unless indices regenerate.
   """
   
   is_view = 0 # Relation0 is not a view
   
   def __init__(self, attribute_names, tuples=None, filter=None):
       from sqlsem import kjbuckets
       self.indices = kjbuckets.kjGraph()
       self.index_list = []
       self.attribute_names = attribute_names
       if tuples is None:
          tuples = []
       self.filter = filter
       self.set_empty()
       self.add_tuples(tuples)
       # indices map attname --> indices containing att
       # relation to shadow and log (if non-null)
       self.log = None
       self.name = None # anonymous by default
       self.is_shadow = 0
       self.touched = 0
       
   def shadow(self, otherrelation, log, name, inshadowdb):
       """return structural replica of otherrelation (as self)
       
          for non-updatable relation (eg, view) may return otherrelation"""
       if otherrelation.is_view:
           # for now, assume VIEWS CANNOT BE UPDATED
           return otherrelation
       self.is_shadow = 1
       self.shadow_of_shadow = otherrelation.is_shadow
       self.log = log
       self.name = name
       # don't make any updates permanent if set.
       self.tuples = otherrelation.tuples[:]
       self.attribute_names = otherrelation.attribute_names
       self.filter = otherrelation.filter
       for index in otherrelation.index_list:
           copy = index.copy()
           name = copy.name
           self.add_index(copy, recordtuples=0)
           # record in shadowdb, but don't log it
           inshadowdb.add_index(name, copy)
           #inshadowdb.add_datadef(name, copy, logit=0)
       self.touched = otherrelation.touched
       return self
              
   def unshadow(self):
       """make self into a replacement for shadowed, return self."""
       if self.is_shadow:
           self.log = None
           self.is_shadow = self.shadow_of_shadow
       return self
       
   def dump(self, file):
       attributes = tuple(self.attributes())
       rows = self.rows()
       newrows = rows[:]
       count = 0
       tt = type
       from types import IntType
       for i in xrange(len(rows)):
           this = rows[i]
           if this is not None and tt(this) is not IntType:
              newrows[count] = rows[i].dump(attributes)
              count = count + 1
       newrows = newrows[:count]
       newrows.append(attributes)
       checksum_dump(newrows, file)

   def load(self, file):
       """checksum must succeed."""
       rows = checksum_undump(file)
       attributes = rows[-1]
       self.attribute_names = attributes
       rows = rows[:-1]
       from sqlsem import kjbuckets
       undump = kjbuckets.kjUndump
       for i in xrange(len(rows)):
           rows[i] = undump(attributes, rows[i]) 
       self.set_empty()
       self.add_tuples(rows)
       # in sync with disk copy!
       self.touched = 0
       
   def add_index(self, index, recordtuples=1):
       """unset recordtuples if the index is initialized already."""
       # does not "touch" the relation
       index_list = self.index_list
       indices = self.indices
       atts = index.attributes()
       for a in atts:
           indices[a] = index
       if recordtuples:
           (tuples, seqnums) = self.rows(1)
           index.clear()
           if tuples:
               index.add_tuples(tuples, seqnums)
       index_list.append(index)
           
   def drop_index(self, index):
       # does not "touch" the relation
       name = index.name
       if verbosity:
          print "rel.drop_index", index
          print "...", self.indices, self.index_list
       indices = self.indices
       for a in index.attributes():
           # contorted since one index be clone of the other.
           aindices = indices.neighbors(a)
           for ind in aindices:
               if ind.name == name:
                  indices.delete_arc(a, ind)
                  theind = ind
       # the (non-clone) index ought to have been found above...
       self.index_list.remove(theind)
           
   def choose_index(self, attributes):
       """choose an index including subset of attributes or None"""
       from sqlsem import kjbuckets
       kjSet = kjbuckets.kjSet
       atts = kjSet(attributes)
       #print "choosing index", atts
       indices = (atts * self.indices).values()
       choice = None
       for index in indices:
           indexatts = index.attributes()
           #print "index atts", indexatts
           iatts = kjSet(indexatts)
           if iatts.subset(atts):
              if choice is None:
                 #print "chosen", index.name
                 choice = index
                 lchoice = len(choice.attributes())
              else:
                 if index.unique or lchoice<len(indexatts):
                    choice = index
                    lchoice = len(choice.attributes())
       return choice
       
   def __repr__(self):
       rows = self.rows()
       atts = self.attributes()
       list_rep = [list(atts)]
       for r in rows:
           rlist = []
           for a in atts:
               try:
                   elt = r[a]
               except KeyError:
                   elt = "NULL"
               else:
                   elt = str(elt)
               rlist.append(elt)
           list_rep.append(rlist)
       # compute maxen for formatting
       maxen = [0] * len(atts)
       for i in xrange(len(atts)):
           for l in list_rep:
               maxen[i] = max(maxen[i], len(l[i]))
       for i in xrange(len(atts)):
           mm = maxen[i]
           for l in list_rep:
                old = l[i]
                l[i] = old + (" " * (mm-len(old)))
       from string import join
       for i in xrange(len(list_rep)):
           list_rep[i] = join(list_rep[i], " | ")
       first = list_rep[0]
       list_rep.insert(1, "=" * len(first))
       return join(list_rep, "\n")
       
   def irepr(self):
       List = [self] + list(self.index_list)
       List = map(str, List)
       from string import join
       return join(List, "\n")
       
   def set_empty(self):
       self.tuples = []
       for index in self.index_list:
           index.clear()
           
   def drop_indices(self, db):
       for index in self.index_list:
           name = index.name
           db.drop_datadef(name)
           db.drop_index(name)
       self.index_list = []
       from sqlsem import kjbuckets
       self.indices = kjbuckets.kjGraph()
           
   def regenerate_indices(self):
       (tuples, seqnums) = self.rows(1)
       #self.tuples = tuples
       for index in self.index_list:
           index.clear()
           index.add_tuples(tuples, seqnums)
       
   def add_tuples(self, tuples):
       if not tuples: return
       tuples = filter(self.filter, tuples)
       oldtuples = self.tuples
       first = len(oldtuples)
       oldtuples[first:] = list(tuples)
       last = len(oldtuples)
       for index in self.index_list:
           index.add_tuples(tuples, xrange(first,last))
       self.touched = 1
           
   def attributes(self):
       return self.attribute_names
       
   def rows(self, andseqnums=0):
       tups = self.tuples
       # short cut
       if 0 not in tups:
          if andseqnums:
             return (tups, xrange(len(tups)))
          else:
             return tups
       tt = type
       from types import IntType
       result = list(self.tuples)
       if andseqnums: seqnums = result[:]
       count = 0
       for i in xrange(len(result)):
           t = result[i]
           if tt(t) is not IntType:
              result[count] = t
              if andseqnums: seqnums[count] = i
              count = count+1
       result = result[:count]
       if andseqnums:
          return (result, seqnums[:count])
       else:
          return result
       
   def erase_tuples(self, seqnums):
       #print "et seqnums", seqnums
       if not seqnums: return
       tups = self.tuples
       # order important! indices first!
       for index in self.index_list:
           index.erase_tuples(seqnums, tups)
       for i in seqnums:
           #print "deleting", i
           tups[i] = 0
       #print self
       self.touched = 1
           
   def reset_tuples(self, tups, seqnums):
       # KISS for indices, maybe optimize someday...
       if not tups: return
       mytups = self.tuples
       for index in self.index_list:
           index.erase_tuples(seqnums, mytups)
       for i in xrange(len(seqnums)):
           seqnum = seqnums[i]
           mytups[seqnum] = tups[i]
       for index in self.index_list:
           index.add_tuples(tups, seqnums)
       self.touched = 1
       
# should views be here?

class View(Relation0):
   """view object, acts like relation, with addl operations."""
   touched = 0
   is_view = 1
   is_shadow = 0
   
   ### must fix namelist!
   
   def __init__(self, name, namelist, selection, indb):
       """set namelist to None for implicit namelist"""
       self.name = name
       self.namelist = namelist
       self.selection = selection
       # attempt a relbind, no outer bindings!
       self.relbind(indb, {})
       self.cached_rows = None
       self.translate = None
       
   def __repr__(self):
       return "view %s as %s" % (self.name, self.selection)
       
   irepr = __repr__
       
   def uncache(self):
       self.cached_rows = None
       
   def UNDEFINED_OP_FOR_VIEW(*args, **kw):
       raise ValueError, "operation explicitly undefined for view object"
       
   shadow = dump = load = add_index = drop_index = set_empty = \
   add_tuples = erase_tuples = reset_tuples = UNDEFINED_OP_FOR_VIEW
   
   def ignore_op_for_view(*args, **kw):
       """ignore this op when applied to view"""
       pass
       
   drop_indices = regenerate_indices = ignore_op_for_view
   
   def choose_index(s, a):
       """no indices on views (might change this?)"""
       return None
       
   def relbind(self, db, atts):
       """bind self to db, ignore atts"""
       name = self.name
       selection = self.selection
       selection = self.selection = selection.relbind(db)
       namelist = self.namelist
       if namelist is not None:
           from sqlsem import kjbuckets
           target_atts = selection.attributes()
           if len(namelist)!=len(target_atts):
              raise "select list and namelist don't match in %s"%name
           pairs = map(None, namelist, target_atts)
           self.translate = kjbuckets.kjGraph(pairs)
       return self
       
   def attributes(self):
       namelist = self.namelist
       if self.namelist is None:
           return self.selection.attributes()
       return namelist
       
   def rows(self, andseqs=0):
       cached_rows = self.cached_rows
       if cached_rows is None:
          cached_rows = self.cached_rows = self.selection.eval().rows()
          if self.namelist is not None:
              # translate the attribute names
              translate = self.translate
              for i in range(len(cached_rows)):
                  cached_rows[i] = cached_rows[i].remap(translate)
       if andseqs:
          return (cached_rows[:], range(len(cached_rows)))
       else:
          return cached_rows[:]
       
class Index:
   """Index for tuples in relation.  Tightly bound to relation rep."""
   
   ### should add "unique index" and check enforce uniqueness...
   
   def __init__(self, name, attributes, unique=0):
       self.unique = unique
       self.name = name
       self.atts = tuple(attributes)
       # values --> tuples
       self.index = {}
       self.dseqnums = {}
       
   def __repr__(self):
       un = ""
       if self.unique: un="UNIQUE "
       return "%sindex %s on %s" % (un, self.name, self.atts)
       
   def copy(self):
       """make a fast structural copy of self"""
       result = Index(self.name, self.atts, unique=self.unique)
       rindex = result.index
       rdseqnums = result.dseqnums
       myindex = self.index
       mydseqnums = self.dseqnums
       for k in myindex.keys():
           rindex[k] = myindex[k][:]
       for k in mydseqnums.keys():
           rdseqnums[k] = mydseqnums[k][:]
       return result
       
   def attributes(self):
       return self.atts
       
   def matches(self, tuple, translate=None):
       """return (tuples, seqnums) for tuples matching tuple
          (with possible translations"""
       if translate:
          tuple = translate * tuple
       atts = self.atts
       dump = tuple.dump(atts)
       index = self.index
       if index.has_key(dump):
          return (index[dump], self.dseqnums[dump])
       else:
          return ((), ())
       
   def clear(self):
       self.index = {}
       self.dseqnums = {}
       
   def add_tuples(self, tuples, seqnums):
       unique = self.unique
       atts = self.atts
       index = self.index
       dseqnums = self.dseqnums
       test = index.has_key
       for i in xrange(len(tuples)):
           tup = tuples[i]
           seqnum = seqnums[i]
           dump = tup.dump(atts)
           #print self.name, dump
           if test(dump):
              bucket = index[dump]
              #print "self", self
              #print "unique", unique
              #print "bucket", bucket
              if unique and bucket:
                  raise StorageError, "uniqueness violation: %s %s" %(
                    dump, self)
              bucket.append(tup)
              dseqnums[dump].append(seqnum)
           else:
              index[dump] = [tup]
              dseqnums[dump] = [seqnum]
           
   def erase_tuples(self, seqnums, all_tuples):
       # all_tuples must be internal rel tuple list
       atts = self.atts
       index = self.index
       dseqnums = self.dseqnums
       for seqnum in seqnums:
           tup = all_tuples[seqnum]
           dump = tup.dump(atts)
           index[dump].remove(tup)
           dseqnums[dump].remove(seqnum)
           
class shadow_dict:
    """shadow dictionary. defer & remember updates."""
    verbose = verbosity
    def __init__(self, shadowing, value_transform=None):
        self.shadowed = shadowing
        shadow = self.shadow = {}
        self.touched = {}
        for key in shadowing.keys():
            shadow[key] = shadowing[key]
        self.value_transform = value_transform
        # defeats inheritance! careful!
        self.values = shadow.values
        self.items = shadow.items
        self.keys = shadow.keys
        self.has_key = shadow.has_key
        
    def is_shadowed(self, name):
        return self.touched.has_key(name)
        
    def __len__(self):
        return len(self.shadow)
        
    def commit(self, verbose=0):
        """apply updates to shadowed."""
        import sys
        verbose = verbose or self.verbose
        if self.touched:
            shadowed = self.shadowed
            shadow = self.shadow
            value_transform = self.value_transform
            keys = shadowed.keys()
            if verbose:
                print "shadowdict oldkeys", keys
            for k in keys:
                del shadowed[k]
            keys = shadow.keys()
            if verbose:
                print "shadowdict newkeys", keys
            for k in shadow.keys():
                value = shadow[k]
                if value_transform is not None:
                   try:
                       value = value_transform(value)
                   except:
                       raise "transform fails", (sys.exc_type, sys.exc_value, k, value)
                shadowed[k] = value
            self.touched = {}
                    
    def __getitem__(self, key):
        return self.shadow[key]
           
    def __setitem__(self, key, item):
        from types import StringType
        if type(key) is not StringType:
           raise "nonstring", key
        if item is None:
           raise "none set", (key, item)
        self.touched[key] = 1
        self.shadow[key] = item
        
    def __delitem__(self, key):
        self.touched[key] = 1
        del self.shadow[key]
        
# stored mutations on relations
class Add_Tuples:
   """stored rel.add_tuples(tuples)"""
   def __init__(self, name):
       self.to_rel = name
       self.indb = None
   def initargs(self):
       return (self.to_rel,)
   def set_data(self, tuples, rel):
       """store self.data as tuple with tuple[-1] as to_rel, rest data"""
       attributes = tuple(rel.attributes())
       ltuples = len(tuples)
       data = list(tuples)
       for i in xrange(ltuples):
           tdata = tuples[i].dump(attributes)
           data[i] = tdata
       self.data = tuple(data)
   def __repr__(self):
       from string import join
       datarep = map(repr, self.data)
       datarep = join(datarep, "\n  ")
       return "add tuples to %s\n  %s\n\n" % (self.to_rel, datarep)
   def marshaldata(self):
       return self.data
   def demarshal(self, data):
       self.data = data
   def relbind(self, db):
       self.indb = db
   def eval(self, dyn=None):
       """apply operation to db"""
       db = self.indb
       data = self.data
       name = self.to_rel
       rel = db[name]
       attributes = tuple(rel.attributes())
       tuples = list(data)
       from sqlsem import kjbuckets
       undump = kjbuckets.kjUndump
       for i in xrange(len(tuples)):
           tuples[i] = undump(attributes, tuples[i])
       rel.add_tuples(tuples)
       
class Erase_Tuples(Add_Tuples):
   """stored rel.erase_tuples(seqnums)"""
   def set_data(self, seqnums, rel):
       seqnums = list(seqnums)
       self.data = tuple(seqnums)
   def __repr__(self):
       return "Erase seqnums in %s\n  %s\n\n" % (self.to_rel, self.data)
   def eval(self, dyn=None):
       db = self.indb
       seqnums = self.data
       name = self.to_rel
       rel = db[name]
       rel.erase_tuples(seqnums)
       
class Reset_Tuples(Add_Tuples):
   """stored rel.reset_tuples(tups, seqnums)"""
   def set_data(self, tups, seqnums, rel):
       attributes = tuple(rel.attributes())
       dtups = list(tups)
       for i in xrange(len(dtups)):
           dtups[i] = dtups[i].dump(attributes)
       self.data = (tuple(dtups), tuple(seqnums))
   def __repr__(self):
       (dtups, seqnums) = self.data
       pairs = map(None, seqnums, dtups)
       from string import join
       datarep = map(repr, pairs)
       datarep = join(datarep, "  \n")
       return "Reset tuples in %s\n  %s\n\n" % (self.to_rel, datarep)
   def eval(self, dyn=None):
       db = self.indb
       (dtups, seqnums) = self.data
       tups = list(dtups)
       rel = db[self.to_rel]
       attributes = tuple(rel.attributes())
       from sqlsem import kjbuckets
       undump = kjbuckets.kjUndump
       for i in xrange(len(dtups)):
           tups[i] = undump(attributes, dtups[i])
       rel.reset_tuples(tups, seqnums)
        
# Log entry tags
START = "START"
COMMIT = "COMMIT"
ABORT = "ABORT"
UNREADABLE = "UNREADABLE"
        
class Transaction_Logger:
   """quick and dirty Log implementation per transaction."""
   verbose = verbosity
   
   def __init__(self, db_log, transactionid, is_scratch=0):
       self.db_log = db_log
       self.transactionid = transactionid
       # ignore all operations if set
       self.is_scratch = is_scratch
       self.dirty = 0
       self.deferred = []
       
   def reset(self):
       self.deferred = []
       
   def __repr__(self):
       return "Transaction_Logger(%s, %s, %s)" % (
          self.db_log, self.transactionid, self.is_scratch)
       
   def log(self, operation):
       verbose = self.verbose
       tid = self.transactionid
       if not self.is_scratch:
          self.deferred.append(operation)
          if verbose:
             print "tid logs", tid, operation
             
   def flush(self):
       verbose = self.verbose
       if not self.is_scratch:
          tid = self.transactionid
          deferred = self.deferred
          self.deferred = []
          db_log = self.db_log
          if db_log:
              for operation in deferred:
                  db_log.log(operation, tid)
          self.dirty = 1
       elif verbose:
          print "scratch log ignored", tid, operation
       
   def commit(self, verbose=0):
       verbose = self.verbose or verbose
       tid = self.transactionid
       if verbose: print "committing trans log", tid
       if self.is_scratch: 
           if verbose:
               print "scratch commit ignored", tid
           return
       if not self.dirty:
           if verbose:
               print "nondirty commit", tid
           return
       self.flush()
       db_log = self.db_log
       db_log.commit(verbose, tid)
       if verbose:
          print "transaction is considered recoverable", tid
          
class DB_Logger:
   """quick and dirty global db logger."""
   verbose = verbosity
   is_scratch = 0
   
   def __init__(self, filename, backupname):
       self.filename = filename
       # backup name is never kept open: existence indicates log in use.
       self.backupname = backupname
       self.file = None
       self.dirty = 0
       if self.verbose:
          print id(self), "created DB_Logger on", self.filename
          
   def __repr__(self):
       return "DB_Logger(%s)" % self.filename
       
   def startup(self):
       if self.verbose:
           print id(self), "preparing", self.filename
       # open happens automagically
       #self.file = open(self.filename, "wb")
       self.clear()
       self.dirty = 0
       
   def shutdown(self):
       if self.verbose:
           print id(self), "shutting down log", self.filename
       file = self.file
       if file:
           file.close()
       self.file = None
       
   def clear(self):
       if self.verbose:
           print id(self), "clearing"
       self.shutdown()
       del_file(self.filename)
       
   def restart(self):
       if self.verbose:
           print id(self), "restarting log file", self.filename
       if self.file is not None:
          self.file.close()
       self.file = open(self.filename, "ab")
       dummy = open(self.backupname, "ab")
       dummy.close()
       self.dirty = 0
       
   def clear_log_file(self):
       if self.verbose:
           print id(self), "clearing logfile", self.filename
       if self.file is not None:
          self.file.close()
          self.file = None
       del_file(self.filename)
       del_file(self.backupname)
       self.dirty = 0
       
   def log(self, operation, transactionid=None):
       """transactionid of None means no transaction: immediate."""
       file = self.file
       if file is None:
          self.restart()
          file = self.file
       verbose = self.verbose
       from sqlsem import serialize
       serial = serialize(operation)
       data = (transactionid, serial)
       if verbose:
          print id(self), "logging:", transactionid
          print operation
       checksum_dump(data, file)
       self.dirty = 1
       
   def commit(self, verbose=0, transactionid=None):
       """add commit, if appropriate, flush."""
       verbose = self.verbose or verbose
       if not self.dirty and transactionid is None:
           if verbose: print "commit not needed", transactionid
           return
       elif verbose:
           print "attempting commit", transactionid
       if transactionid is not None:
          self.log( COMMIT, transactionid )
          if verbose: print "committed", transactionid
       if verbose: print "flushing", self.filename
       self.file.flush()
       self.dirty = 0
       
   def recover(self, db, restart=1):
       import sys
       verbose = self.verbose
       filename = self.filename
       if verbose:
          print "attempting recovery from", self.filename
       file = self.file
       if file is not None:
          if verbose: print "closing file"
          self.file.close()
          self.file = None
       if verbose:
           print "opens should generate an error if no recovery needed"
       try:
           file = open(filename, "rb")
           file2 = open(self.backupname, "rb")
       except:
           if verbose: 
               print "no recovery needed:", filename
               print sys.exc_type, sys.exc_value
           sys.exc_traceback = None
           return
       file2.close()
       if verbose: print "log found, recovering from", filename
       records = self.read_records(file)
       if verbose: print "scan for commit records"
       commits = {}
       for (i, (tid, op)) in records:
           if op==COMMIT:
               if verbose: print "transaction", tid, "commit at", i
               commits[tid] = i
           elif verbose:
               print i, tid, "operation\n", op
       if verbose: print commits, "commits total"
       if verbose: print "applying commited operations, in order"
       committed = commits.has_key
       from types import StringType
       for (i, (tid, op)) in records:
           if tid is None or (committed(tid) and commits[tid]>i):
               if type(op) is StringType:
                   if verbose:
                       print "skipping marker", tid, op
               if verbose:
                   print "executing for", tid, i
                   print op
               #### Note: silently eat errors unless verbose
               ### (eg in case of table recreation...)
               ### There should be a better way to do this!!!
               import sys
               try:
                   op.relbind(db)
                   op.eval()
               except:
                   if verbose:
                       print "error", sys.exc_type, sys.exc_value
                       print "binding or evaluating logged operation:"
                       print op
           elif verbose:
               print "uncommitted operation", tid, i
               op
       if verbose:
          print "recovery successful: clearing log file"
       self.clear()
       if restart:
           if verbose:
               print "recreating empty log file"
           self.startup()
               
   def read_records(self, file):
       """return log record as (index, (tid, op)) list"""
       verbose = self.verbose
       if verbose: print "reading log records to error"
       import sys
       records = {}
       from sqlsem import deserialize
       count = 0
       while 1:
           try:
               data = checksum_undump(file)
           except:
               if verbose:
                  print "record read terminated with error", len(records)
                  print sys.exc_type, sys.exc_value
               break
           (transactionid, serial) = data
           operation = deserialize(serial)
           records[count] = (transactionid, operation)
           if verbose:
               print count, ": read for", transactionid
               print operation
           count = count+1
       if verbose: print len(records), "records total"
       records = records.items()
       records.sort()
       return records
       
   def dump(self):
       verbose = self.verbose
       self.shutdown()
       print "dumping log"
       self.verbose = 1
       try:
           file = open(self.filename, "rb")
       except:
           print "DUMP FAILED, cannot open", self.filename
       else:
           self.read_records(file)
       self.verbose = verbose
       self.restart()
       