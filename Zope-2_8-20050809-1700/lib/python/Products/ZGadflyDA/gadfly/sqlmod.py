"""Database modification statement semantics"""

import sqlsem

# ordering of ddef storage is important so, eg, index defs
# follow table defs.

class Ordered_DDF:
    """mixin for DDF statement sorting, subclass defines s.cmp(o)"""
    def __cmp__(self, other):
        try:
            #print "comparing", self.name, other.name
            try:
                sc = self.__class__
                oc = other.__class__
                #print sc, oc
            except:
                #print "punting 1", -1
                return -1
            if sc in ddf_order and oc in ddf_order:
                test = cmp(ddf_order.index(sc), ddf_order.index(oc))
                #print "ddforder", test
                if test: return test
                return self.cmp(other)
            else:
                test = cmp(sc, oc)
                #print "punting 2", test
                return test
        except:
            #import sys
            #print "exception!"
            #print sys.exc_type, sys.exc_value
            return -1
            
    def __coerce__(self, other):
        return (self, other)
    def cmp(self, other):
        """redefine if no name field"""
        return cmp(self.name, other.name)

CTFMT = """\
CREATE TABLE %s (
  %s 
  )"""
       
class CreateTable(Ordered_DDF):
   """create table operation"""
   
   def __init__(self, name, colelts):
       self.name = name
       self.colelts = colelts
       self.indb = None # db in which to create
       
   def initargs(self):
       return (self.name, [])
       
   def marshaldata(self):
       from sqlsem import serialize
       return map(serialize, self.colelts)
       
   def demarshal(self, args):
       from sqlsem import deserialize
       self.colelts = map(deserialize, args)
       
   def __repr__(self):
       from string import join
       elts = list(self.colelts)
       elts = map(repr, elts)
       return CTFMT % (self.name, join(elts, ",\n  "))
       
   def relbind(self, db):
       """check that table doesn't already exist"""
       if db.has_relation(self.name):
          raise NameError, "cannot create %s, exists" % (self.name,)
       self.indb = db
       return self
       
   def eval(self, dyn=None):
       "create the relation now"
       # datatypes currently happily ignored :)
       db = self.indb
       if db is None:
          raise ValueError, "unbound or executed"
       self.indb = None
       name = self.name
       if db.has_relation(self.name):
          raise NameError, "relation %s exists, cannot create" % (self.name,)
       db.touched = 1
       attnames = []
       for x in self.colelts:
           attnames.append(x.colid)
       from gfdb0 import Relation0
       r = Relation0(attnames)
       # must store if new (unset for reloads)
       r.touched = 1
       db[name] = r
       db.add_datadef(name, self)
       log = db.log
       if log is not None:
           log.log(self)
       
viewfmt = """\
CREATE VIEW %s (%s) AS
%s"""
       
class CreateView(sqlsem.SimpleRecursive, Ordered_DDF):
   """CREATE VIEW name (namelist) AS selection"""
   
   # note: no check for cross-references on drops!
   def __init__(self, name, namelist, selection):
       self.name = name
       self.namelist = namelist
       self.selection = selection
       self.indb = None
       
   def __repr__(self):
       return viewfmt % (self.name, self.namelist, self.selection)
       
   def initargs(self):
       return (self.name, self.namelist, self.selection)
       
   def relbind(self, db):
       self.indb = db
       name = self.name
       if db.has_datadef(name):
          raise NameError, "(view) datadef %s exists" % name
       # don't bind the selection yet
       return self
       
   def eval(self, dyn=None):
       "create the view"
       db = self.indb
       name = self.name
       if db is None:
           raise ValueError, "create view %s unbound or executed" % name
       self.indb = None
       if db.has_relation(name):
           raise ValueError, "create view %s, name exists" % name
       db.touched = 1
       from gfdb0 import View
       v = View(self.name, self.namelist, self.selection, db)
       db[name] = v
       db.add_datadef(name, self)
       log = db.log
       if log is not None:
           log.log(self)
       
CREATEINDEXFMT = """\
CREATE %sINDEX %s ON %s (
   %s
   )"""
       
class CreateIndex(sqlsem.SimpleRecursive, Ordered_DDF):
   """create index operation"""
   def __init__(self, name, tablename, atts, unique=0):
       self.name = name
       self.tablename=tablename
       self.atts = atts
       self.indb = None
       self.target = None
       self.unique = unique
       
   def initargs(self):
       return (self.name, self.tablename, self.atts, self.unique)
       
   def __cmp__(self, other):
       oc = other.__class__
       if oc is CreateTable:
          return 1 # after all create tables
       sc = self.__class__
       if oc is not sc:
          return cmp(sc, oc)
       else:
          return cmp(self.name, other.name)
          
   def __coerce__(self, other):
       return (self, other)
       
   def __repr__(self):
       from string import join
       un = ""
       if self.unique: un="UNIQUE "
       innards = join(self.atts, ",\n   ")
       return CREATEINDEXFMT % (un, self.name, self.tablename, innards)
       
   def relbind(self, db):
       name = self.name
       self.indb = db
       if db.has_datadef(name):
          raise NameError, `name`+": data def exists"
       try:
          self.target = db.get_for_update(self.tablename) #db[self.tablename]
       except:
          raise NameError, `self.tablename`+": no such relation"
       return self
          
   def eval(self, dyn=None):
       from gfdb0 import Index
       db = self.indb
       if db is None:
          raise ValueError, "create index unbound or executed"
       self.indb = None
       rel = self.target
       if rel is None:
          raise ValueError, "create index not bound to relation"
       db.touched = 1
       self.the_index = the_index = Index(self.name, self.atts, unique=self.unique)
       rel.add_index(the_index)
       name = self.name
       db.add_datadef(name, self)
       db.add_index(name, the_index)
       log = db.log
       if log is not None:
           log.log(self)
       
class DropIndex(sqlsem.SimpleRecursive):
   def __init__(self, name):
       self.name = name
       self.indb = None
       
   def initargs(self):
       return (self.name,)
       
   def __repr__(self):
       return "DROP INDEX %s" % (self.name,)
       
   def relbind(self, db):
       self.indb = db
       if not db.has_datadef(self.name):
          raise NameError, `self.name`+": no such index"
       return self
          
   def eval(self, dyn=None):
       db = self.indb
       self.indb=None
       if db is None:
          raise ValueError, "drop index executed or unbound"
       db.touched = 1
       indexname = self.name
       createindex = db.datadefs[indexname]
       index = createindex.the_index
       relname = createindex.tablename
       rel = db[relname]
       rel.drop_index(index)
       db.drop_datadef(indexname)
       db.drop_index(indexname)
       log = db.log
       if log is not None:
           log.log(self)
       
class DropTable(sqlsem.SimpleRecursive):
   def __init__(self, name):
       self.name = name
       self.indb = None
   def initargs(self):
       return (self.name,)
   def __repr__(self):
       return "DROP TABLE %s" % (self.name,)
   def relbind(self, db):
       self.indb = db
       name = self.name
       if not db.has_relation(name):
          raise NameError, `self.name` + ": cannot delete, no such table/view"
       self.check_kind(name, db)
       return self
   def check_kind(self, name, db):
       if db[name].is_view:
          raise ValueError, "%s is VIEW, can't DROP TABLE" % name
   def eval(self, dyn):
       db = self.indb
       if db is None:
          raise ValueError, "unbound or executed"
       db.touched = 1
       self.indb = None
       self.relbind(db)
       name = self.name
       rel = db[name]
       rel.drop_indices(db)
       db.drop_datadef(name)
       del db[name]
       log = db.log
       if log is not None:
           log.log(self)
            
class DropView(DropTable):
   """DROP VIEW name"""
   def __repr__(self):
       return "DROP VIEW %s" % self.name
   def check_kind(self, name, db):
       if not db[name].is_view:
          raise ValueError, "%s is TABLE, can't DROP VIEW" % name
       
COLDEFFMT = "%s %s %s %s"

class ColumnDef(sqlsem.SimpleRecursive):

   def __init__(self, colid, datatype, defaults, constraints):
       self.colid = colid
       self.datatype = datatype
       self.defaults = defaults
       self.constraints = constraints
       
   def initargs(self):
       return (self.colid, self.datatype, self.defaults, self.constraints)
       
   def __repr__(self):
       defaults = self.defaults
       if defaults is None: defaults=""
       constraints = self.constraints
       if constraints is None: constraints = ""
       return COLDEFFMT % (self.colid, self.datatype, defaults, constraints)
       


def evalcond(cond, eqs, target, dyn, rassns, translate, invtrans):
       """factored out shared op between Update and Delete."""
       if dyn:
          #print "dyn", dyn
          from sqlsem import dynamic_binding
          dynbind = dynamic_binding(len(dyn), dyn)
          if len(dynbind)>1:
             raise ValueError, "only one dynamic binding allowed for UPDATE"
          dynbind1 = dynbind = dynbind[0]
          if eqs is not None:
             dynbind1 = dynbind.remap(eqs)
          if dynbind1 is None:
             # inconsistent
             return
          dynbind = dynbind1 + dynbind
          if rassns is not None:
             rassns = rassns + invtrans * dynbind
             if rassns.Clean() is None:
                # inconsistent
                return
          else:
             rassns = invtrans * dynbind
          #print "dynbind", dynbind
          #print "rassn", rassns
       else:
          dynbind = None
       # get tuple set, try to use an index
       index = None
       if rassns is not None:
          known = rassns.keys()
          index = target.choose_index(known)
       if index is None:
          (tuples, seqnums) = target.rows(1)
       else:
          #print "using index", index.name
          (tuples, seqnums) = index.matches(rassns)
       ltuples = len(tuples)
       buffer = [0] * ltuples
       rtups = range(ltuples)
       for i in rtups:
           tup = tuples[i]
           #print tup
           ttup = translate * tup
           if dynbind:
              ttup = (ttup + dynbind).Clean()
           if ttup is not None:
              buffer[i] = ttup
       #print "buffer", buffer
       #print "cond", cond
       #for x in buffer:
           #print "before", x
       test = cond(buffer)
       #print "test", test
       return (test, rtups, seqnums, tuples)


UPDFMT = """\
UPDATE %s
SET %s
WHERE %s"""

# optimize to use indices and single call to "cond"
class UpdateOp(sqlsem.SimpleRecursive):
   def __init__(self, name, assns, condition):
       self.name = name
       self.assns = assns
       self.condition = condition
       
   def initargs(self):
       return (self.name, self.assns, self.condition)
       
   def __repr__(self):
       return UPDFMT % (self.name, self.assns, self.condition)
       
   def relbind(self, db):
       self.indb = db
       name = self.name
       target = self.target = db.get_for_update(name)
       (attb, relb, amb, ambatts) = db.bindings( [ (name, name) ] )
       assns = self.assns = self.assns.relbind(attb, db)
       cond = self.condition = self.condition.relbind(attb, db)
       constraints = cond.constraints
       if constraints is not None:
          eqs = self.eqs = constraints.eqs
          cassns = constraints.assns
       else:
          cassns = eqs = self.eqs = None
       #print constraints, eqs
       # check that atts of assns are atts of target
       #print dir(assns)
       resultatts = assns.attorder
       from sqlsem import kjbuckets
       kjSet = kjbuckets.kjSet
       kjGraph = kjbuckets.kjGraph
       resultatts = kjSet(resultatts)
       allatts = kjSet(target.attribute_names)
       self.preserved = allatts - resultatts
       huh = resultatts - allatts
       if huh:
          raise NameError, "%s lacks %s attributes" % (name, huh.items())
       # compute projection
       assnsatts = kjGraph(assns.domain().items()).neighbors(name)
       condatts = kjGraph(cond.domain().items()).neighbors(name)
       condatts = condatts+assnsatts
       #print "condatts", condatts
       translate = kjbuckets.kjDict()
       for att in condatts:
           translate[ (name, att) ] = att
       self.translate = translate
       invtrans= self.invtrans = ~translate
       if cassns is not None:
          self.rassns = invtrans * cassns
       else:
          self.rassns = None
       #print "cassns,rassns", cassns, self.rassns
       #print translate
       # compute domain of self.assns 
       # (do nothing with it, should add sanity check!)
       assns_domain = self.assns.domain()
       return self
       
   def eval(self, dyn=None):
       indb = self.indb
       name = self.name
       cond = self.condition
       cond.uncache()
       assns = self.assns
       assns.uncache()
       translate = self.translate
       preserved = self.preserved
       target = self.target
       rassns = self.rassns
       eqs = self.eqs
       invtrans = self.invtrans
       #print "assns", assns, assns.__class__
       #print "cond", cond
       #print "eqs", eqs
       #print "target", target
       #print "dyn", dyn
       #print "rassns", rassns
       #print "translate", translate
       #print "invtrans", invtrans
       (test, rtups, seqnums, tuples) = evalcond(
           cond, eqs, target, dyn, rassns, translate, invtrans)
       # shortcut
       if not test: return
       self.indb.touched = 1
       tt = type
       from types import IntType
       #print test
       (tps, attorder) = assns.map(test)
       count = 0
       newseqs = list(rtups)
       newtups = list(rtups)
       for i in rtups:
           new = tps[i]
           if tt(new) is not IntType and new is not None:
              seqnum = seqnums[i]
              old = tuples[i]
              if preserved:
                 new = new + preserved*old
              newtups[count] = new
              newseqs[count] = seqnum
              count = count + 1
       if count:
           newseqs = newseqs[:count]
           newtups = newtups[:count]
           target.reset_tuples(newtups, newseqs)
           log = indb.log
           if log is not None and not log.is_scratch:
               from sqlsem import Reset_Tuples
               op = Reset_Tuples(self.name)
               op.set_data(newtups, newseqs, target)
               log.log(op)


class DeleteOp(sqlsem.SimpleRecursive):

   def __init__(self, name, where):
       self.name = name
       self.condition = where
       
   def initargs(self):
       return (self.name, self.condition)
       
   def __repr__(self):
       return "DELETE FROM %s WHERE %s" % (self.name, self.condition)
       
   def relbind(self, db):
       self.indb = db
       name = self.name
       target = self.target = db.get_for_update(name)
       (attb, relb, amb, ambatts) = db.bindings( [ (name, name) ] )
       cond = self.condition = self.condition.relbind(attb, db)
       # compute domain of cond
       # do nothing with it (should add sanity check)
       cond_domain = cond.domain()
       constraints = cond.constraints
       if constraints is not None:
          cassns = constraints.assns
          self.eqs = constraints.eqs
       else:
          self.eqs = cassns = None
       # compute projection/rename
       from sqlsem import kjbuckets
       condatts = kjbuckets.kjGraph(cond.domain().items()).neighbors(name)
       translate = kjbuckets.kjDict()
       for att in condatts:
           translate[(name, att)] = att
       self.translate = translate
       invtrans = self.invtrans = ~translate
       if cassns is not None:
          self.rassns = invtrans * cassns
       else:
          self.rassns = None
       return self
       
   def eval(self, dyn=None):
       # note, very similar to update case...
       indb = self.indb
       name = self.name
       target = self.target
       tuples = target.tuples
       eqs = self.eqs
       rassns = self.rassns
       cond = self.condition
       cond.uncache()
       translate = self.translate
       invtrans = self.invtrans
       (test, rtups, seqnums, tuples) = evalcond(
          cond, eqs, target, dyn, rassns, translate, invtrans)
       # shortcut
       if not test: return
       indb.touched = 1
       tt = type
       from types import IntType
       count = 0
       newseqs = list(rtups)
       #print "rtups", rtups
       for i in rtups:
           new = test[i]
           if tt(new) is not IntType and new is not None:
              seqnum = seqnums[i]
              newseqs[count] = seqnum
              count = count + 1
       #print "newseqs", newseqs
       #print "count", count
       if count:
           newseqs = newseqs[:count]
           target.erase_tuples(newseqs)
           log = indb.log
           if log is not None and not log.is_scratch:
               from sqlsem import Erase_Tuples
               op = Erase_Tuples(self.name)
               op.set_data(newseqs, target)
               log.log(op)

INSFMT = """\
INSERT INTO %s 
%s
%s"""

class InsertOp(sqlsem.SimpleRecursive):

   def __init__(self, name, optcolids, insertspec):
       self.name = name
       self.optcolids = optcolids
       self.insertspec = insertspec
       self.target = None # target relation
       self.collector = None # name map for attribute translation
       
   def initargs(self):
       return (self.name, self.optcolids, self.insertspec)
       
   def __repr__(self):
       return INSFMT % (self.name, self.optcolids, self.insertspec)
       
   def relbind(self, db):
       self.indb = db
       name = self.name
       # determine target relation
       target = self.target = db.get_for_update(name)
       targetatts = target.attributes()
       from sqlsem import kjbuckets
       kjSet = kjbuckets.kjSet
       targetset = kjSet(targetatts)
       # check or set colid bindings
       colids = self.optcolids
       if colids is None:
          colids = self.optcolids = target.attributes()
       colset = kjSet(colids)
       ### for now all attributes must be in colset
       cdiff = colset-targetset
       if cdiff:
          raise NameError, "%s: no such attributes in %s" % (cdiff.items(), name)
       cdiff = targetset-colset
       ### temporary!!!
       if cdiff:
          raise NameError, "%s: not set in insert on %s" % (cdiff.items(), name)
       # bind the insertspec
       insertspec = self.insertspec
       self.insertspec = insertspec = insertspec.relbind(db)
       # create a collector for result
       from sqlsem import TupleCollector
       collector = self.collector = TupleCollector()
       # get ordered list of expressions to eval on bound attributes of insertspec
       resultexps = insertspec.resultexps()
       if len(resultexps)!=len(colset):
          raise ValueError, "result and colset of differing length %s:%s" % (colset,resultexps)
       pairs = map(None, colids, resultexps)
       for (col,exp) in pairs:
           collector.addbinding(col, exp)
       return self
       
   def eval(self, dyn=None):
       resultbts = self.insertspec.eval(dyn)
       #print "resultbts", resultbts
       # shortcut
       if not resultbts: return
       indb = self.indb
       indb.touched = 1
       (resulttups, resultatts) = self.collector.map(resultbts)
       #print "resulttups", resulttups
       if resulttups:
           target = self.target
           target.add_tuples(resulttups)
           #target.regenerate_indices()
           log = indb.log
           if log is not None and not log.is_scratch:
               from sqlsem import Add_Tuples
               op = Add_Tuples(self.name)
               op.set_data(resulttups, target)
               log.log(op)

       
Insert_dummy_arg = [ ( (1,1), 1 ) ]
                     
class InsertValues(sqlsem.SimpleRecursive):

   def __init__(self, List):
       self.list = List
       
   def initargs(self):
       return (self.list,)
       
   def __repr__(self):
       return "VALUES " +` tuple(self.list) `
       
   def resultexps(self):
       return self.list
       
   def relbind(self, db):
       l = self.list
       bindings = {}
       for i in xrange(len(self.list)):
           li = l[i]
           l[i] = li.relbind(bindings, db)
           # do nothing with domain, for now
           li_domain = li.domain()
       return self
       
   def eval(self, dyn=None):
       if dyn:
          from sqlsem import dynamic_binding
          dynbt = dynamic_binding(len(dyn), dyn)
       else:
          # dummy value to prevent triviality
          from sqlsem import kjbuckets
          dynbt = [kjbuckets.kjDict(Insert_dummy_arg)]
       #print "bindings", dynbt.assns
       return dynbt # ??
       
class InsertSubSelect(sqlsem.SimpleRecursive):

   def __init__(self, subsel):
       self.subsel = subsel
       
   def initargs(self):
       return (self.subsel,)
       
   def __repr__(self):
       return "[subsel] %s" % (self.subsel,)
       
   def resultexps(self):
       # get list of result bindings
       subsel = self.subsel
       atts = self.subsel.attributes()
       # bind each as "result.name"
       exps = []
       from sqlsem import BoundAttribute
       for a in atts:
           exps.append( BoundAttribute("result", a) )
       return exps # temp
       
   def relbind(self, db):
       subsel = self.subsel
       self.subsel = subsel.relbind(db)
       # do nothing with domain for now
       #subsel_domain = subsel.domain()
       return self
       
   def eval(self, dyn=None):
       subsel = self.subsel
       subsel.uncache()
       rel = subsel.eval(dyn)
       tups = rel.rows()
       from sqlsem import BoundTuple ### temp
       from sqlsem import kjbuckets
       kjDict = kjbuckets.kjDict
       for i in xrange(len(tups)):
           tupsi = tups[i]
           new = kjDict()
           for k in tupsi.keys():
               new[ ("result", k) ] = tupsi[k]
           tups[i] = new
       return tups
       
# ordering for archiving datadefs
ddf_order = [CreateTable, CreateIndex, CreateView]
