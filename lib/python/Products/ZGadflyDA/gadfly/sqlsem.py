
""" sql semantics 
"""

### trim unused methods.
### make assns use equivalence classes.

### maybe eventually implement disj-conj-eq optimizations

### note: for multithreading x.relbind(...) should ALWAYs return
###   a fresh copy of structure (sometimes in-place now).

### note: binding of order by is dubious with archiving,
###    should not bind IN PLACE, leave unbound elts alone!

### need to fix serialization/deserialization of btand and btor
###

# use kjbuckets builtin if available
try:
    import kjbuckets
except ImportError:
    import kjbuckets0
    kjbuckets = kjbuckets0
    
Tuple = kjbuckets.kjDict
Graph = kjbuckets.kjGraph
Set = kjbuckets.kjSet

import sys, traceback
### debug
#sys.stderr = sys.stdin
    
# operations on simple tuples, mostly from kjbuckets
#def maketuple(thing):
#    """try to make a tuple from thing.
#       thing should be a dictionary or sequence of (name, value)
#       or other tuple."""
#    from types import DictType
#    if type(thing)==DictType:
#       return Tuple(thing.items() )
#    else: return Tuple(thing)
    
def no_ints_nulls(list):
    """in place remove all ints, Nones from a list (for null handling)"""
    tt = type
    nn = None
    from types import IntType
    count = 0
    for x in list:
        if tt(x) is not IntType and x is not nn:
           list[count] = x
           count = count+1
    del list[count:]
    return list

# stuff for bound tuples.

class HashJoiner:

    def __init__(self, bt, relname, attributes, relation, witness):
        self.relname = relname
        self.attributes = attributes
        self.relation = relation
        self.witness = witness 
        self.bt = bt
        eqs = bt.eqs
        #print "relname", relname
        #print "attributes", attributes
        #print "relation", relation
        #print "witness", witness
        #print "bt", bt
        transform = self.transform = kjbuckets.kjDict()
        rbindings = self.rbindings = kjbuckets.kjSet()
        for a in attributes:
            b = (relname, a)
            transform[b] = a
            rbindings[b] = b
        self.eqs = eqs = eqs + kjbuckets.kjGraph(rbindings)
        witness = witness.remap(eqs)
        known = kjbuckets.kjSet(witness.keys()) & rbindings
        batts = tuple(known.items())
        if not batts:
           atts = ()
        elif len(batts)==1:
           atts = ( transform[batts[0]], )
        else:
           atts = transform.dump(batts)
        self.atts = atts
        self.batts = batts
        self.transform = transform
        eqs = bt.eqs
        #eqs = (rbindings * eqs)
        self.eqs = eqs = eqs + kjbuckets.kjGraph(rbindings)
        self.transformG = transformG = eqs * transform
        assns = self.assns = bt.assns
        self.rassns = assns.remap( ~transformG )
        
    def relbind(self, db, atts):
        rel = self.relation
        #print "rel is ", rel, type(rel)
        #print dir(rel)
        if rel.is_view:
            self.relation = rel.relbind(db, atts)
        return self
        
    def uncache(self):
        rel = self.relation
        if rel.is_view:
           self.relation.uncache()
        
    def join(self, subseq):
        relname = self.relname
        result = []
        assns = self.assns
        if not subseq: return result
        # apply equalities to unitary subseq (embedded subq)
        if len(subseq)==1:
           subseq0 = subseq[0]
           subseq0r = subseq0.remap(self.eqs)
           if subseq0r is None:
              return [] # inconsistent
           subseq0 = subseq0 + subseq0r + assns
           if subseq0.Clean() is None:
              return [] # inconsistent
           subseq = [subseq0]
        rassns = self.rassns
        #print "rassns", rassns
        #print "subseq", subseq
        if rassns is None:
           #print "inconsistent btup"
           return []
        relation = self.relation
        #print "assns", assns
        transformG = self.transformG
        #print "transformG", transformG
        transform = self.transform
        atts = self.atts
        batts = self.batts
        #print "batts, atts", batts, atts
        if not batts:
           #print "cross product", relname
           tuples = relation.rows()
           for t in tuples:
               #print "t is", t
               if rassns:
                  t = (t + rassns).Clean()
               if t is None:
                  #print "preselect fails"
                  continue
               new = t.remap(transformG)
               #print "new is", new
               if new is None:
                  #print "transform fails"
                  continue
               for subst in subseq:
                   #print "subst", subst
                   if subst:
                      add = (subst + new).Clean()
                   else:
                      add = new
                   #print "add is", add
                   if add is not None:
                      result.append(add)
        else:
           # hash join
           #print "hash join"
           # first try to use an index
           index = relation.choose_index(atts)
           #print transform
           if index is not None:
              #print "index join", index.name, relname
              #print index.index.keys()
              #print "rassns", rassns
              atts = index.attributes()
              invtransform = ~transform
              if len(atts)==1:
                 batts = (invtransform[atts[0]],)
              else:
                 batts = invtransform.dump(atts)
              hash_tups = 1
              tindex = index.index
              # memoize converted tuples
              tindex0 = {}
              test = tindex.has_key
              test0 = tindex0.has_key
              for i in xrange(len(subseq)):
                  subst = subseq[i]
                  #print "substs is", subst
                  its = subst.dump(batts)
                  #print "its", its
                  othersubsts = []
                  if test0(its):
                     othersubsts = tindex0[its]
                  elif test(its):
                     tups = tindex[its]
                     for t in tups:
                         #print "t before", t
                         t = (t+rassns).Clean()
                         #print "t after", t
                         if t is None: continue
                         new = t.remap(transformG)
                         #print "new", new
                         if new is None: continue
                         othersubsts.append(new)
                  tindex0[its] = othersubsts
                  for other in othersubsts:
                      #print "adding", other, subst
                      add = (other + subst).Clean()
                      if add is not None:
                         result.append(add)
           # hash join
           #print "hash join"
           else:
               tuples = relation.rows()
               if len(subseq)<len(tuples):
                  #print "hash subseq", relname
                  subseqindex = {}
                  test = subseqindex.has_key
                  for i in xrange(len(subseq)):
                      subst = subseq[i]
                      its = subst.dump(batts)
                      #print "items1", subseq, batts, its
                      if test(its):
                         subseqindex[its].append(subst)
                      else:
                         subseqindex[its] = [ subst ]
                  for t in tuples:
                      #print "on", t
                      if rassns:
                         t = (t+rassns).Clean()
                      if t is None:
                         #print "preselect fails"
                         continue
                      its = t.dump(atts)
                      #print "items2", its
                      if test(its):
                         new = t.remap(transformG)
                         #print "...new", new
                         if new is None:
                            #print "transform fails"
                            continue
                         l = subseqindex[its]
                         for subst in l:
                             add = (subst + new).Clean()
                             #print "adding", add
                             if add is not None:
                                result.append(add)
               else:
                  #print "hash tuples", relname
                  tindex = {}
                  test = tindex.has_key
                  for i in xrange(len(tuples)):
                      t = tuples[i]
                      if rassns:
                         t = (t + rassns).Clean()
                      if t is None:
                         #print "preselect fails"
                         continue
                      new = t.remap(transformG)
                      #print "new is", new
                      if new is None:
                         #print "transform fails"
                         continue
                      its = t.dump(atts)
                      #print "items3", its
                      if test(its):
                         tindex[its].append(new)
                      else:
                         tindex[its] = [ new ]
                  for subst in subseq:
                      its = subst.dump(batts)
                      #print "items4", its
                      if test(its):
                         n = tindex[its]
                         for new in n:
                             add = (subst + new).Clean()
                             if add is not None:
                                result.append(add)
        #print "hashjoin result"
        #for x in result:
            #print x
            #break
        return result
        
### essentially, specialized pickle for this app:
        
def deserialize(description):
    """simple protocol for generating a marshallable ob"""
    #print "deserialize", description
    from types import TupleType
    if type(description) is not TupleType:
        return description # base type
    try:
        (name, desc) = description
    except:
        return description # base type
    if name == "tuple":
        # tuple case
        return desc
    ### other special cases here...
    if name == "list":
        # list case: map deserialize across desc
        return map(deserialize, desc)
    # all other cases are classes of sqlsem
    import sqlsem
    klass = getattr(sqlsem, name)
    (args1, args2) = desc
    args1 = tuple(map(deserialize, args1))
    ob = apply(klass, args1)
    ob.demarshal(args2)
    return ob
    
def serialize(ob):
    """dual of deserialize."""
    from types import ListType
    tt = type(ob)
    # for lists map serialize across members
    #if tt is ListType:
    #    return ("list", map(serialize, ob))
    try:
        #print ob.__class__, ob
        args1 = ob.initargs()
        #print "args1 before", args1
        args1 = tuple(map(serialize, args1))
        #print "args1 after", args1
        args2 = ob.marshaldata()
        return (ob.__class__.__name__, (args1, args2))
    except:
        from types import InstanceType
        #tt = type(ob)
        if tt is InstanceType:
           #ext = traceback.extract_tb(sys.exc_traceback)
           #for x in ext: 
               #print x
           #print
           #print sys.exc_type, sys.exc_value
           #print ob.__class__
           raise ValueError, "couldn't serialize %s %s" % (
             tt, ob.__class__)
        # assume base type otherwise
        return ob
        
# invariant:
#   deserialize(serialize(ob)) returns semantic copy of ob
#   serialize(ob) is marshallable
# ie,
#   args1 = ob.initargs() # init args
#   args1d = map(serialize, args1) # serialized
#   args2 = ob.marshaldata() # marshalable addl info
#   # assert args1d, args2 are marshallable
#   args1copy = map(deserialize, args1)
#   ob2 = ob.__class__(args1copy)
#   ob2 = ob2.demarshal(args2)
#   # assert ob2 is semantic copy of ob

class SimpleRecursive:
    """Simple Recursive structure, only requires initargs"""
    def demarshal(self, args):
        pass
    def marshaldata(self):
        return ()

class BoundTuple:

   clean = 1  # false if inconsistent
   closed = 0 # true if equality constraints inferred

   def __init__(self, **bindings):
       """bindings are name-->simpletuple associations."""
       self.eqs = Graph()
       self.assns = Tuple()
       for (name, simpletuple) in bindings.items():
           self.bind(name, simpletuple)
          
   def initargs(self):
       return ()
       
   def marshaldata(self):
       #print "btp marshaldata", self
       return (self.eqs.items(), self.assns.items(), self.clean, self.closed)
       
   def demarshal(self, args):
       (eitems, aitems, self.clean, self.closed) = args
       self.eqs = kjbuckets.kjGraph(eitems)
       self.assns = kjbuckets.kjDict(aitems)
           
   def relbind(self, dict, db):
       """return bindings of self wrt dict rel-->att"""
       result = BoundTuple()
       e2 = result.eqs
       a2 = result.assns
       for ((a,b), (c,d)) in self.eqs.items():
           if a is None:
              try:
                 a = dict[b]
              except KeyError:
                 raise NameError, `b`+": ambiguous or unknown attribute"
           if c is None:
              try:
                 c = dict[d]
              except KeyError:
                 raise NameError, `d`+": ambiguous or unknown attribute"
           e2[(a,b)] = (c,d)
       for ((a,b), v) in self.assns.items():
           if a is None:
              try:
                 a = dict[b]
              except KeyError:
                 raise NameError, `b`+": ambiguous or unknown attribute"
           a2[(a,b)] = v
       result.closed = self.closed
       result.clean = self.clean
       return result
           
   #def known(self, relname):
   #    """return ([(relname, a1), ...], [a1, ...])
   #       for attributes ai of relname known in self."""
   #    atts = []
   #    batts = []
   #    for x in self.assns.keys():
   #        (r,a) = x
   #        if r==relname:
   #           batts.append(x)
   #           atts.append(a)
   #    return (batts, atts)
                 
   def relorder(self, db, allrels):
       """based on known constraints, pick an
          ordering for materializing relations.
          db is database (ignored currently)
          allrels is names of all relations to include (list)."""
       ### not very smart about indices yet!!!
       if len(allrels)<2:
          # doesn't matter
          return allrels
       order = []
       eqs = self.eqs
       assns = self.assns
       kjSet = kjbuckets.kjSet
       kjGraph = kjbuckets.kjGraph
       pinned = kjSet()
       has_index = kjSet()
       needed = kjSet(allrels)
       akeys = assns.keys()
       for (r,a) in akeys:
           pinned[r]=r # pinned if some value known
       known_map = kjGraph(akeys)
       for r in known_map.keys():
           rknown = known_map.neighbors(r)
           if db.has_key(r):
              rel = db[r]
              index = rel.choose_index(rknown)
              if index is not None:
                 has_index[r] = r # has an index!
       if pinned: pinned = pinned & needed
       if has_index: has_index = has_index & needed
       related = kjGraph()
       for ( (r1, a1), (r2, a2) ) in eqs.items():
           related[r1]=r2 # related if equated to other
           related[r2]=r1 # redundant if closed.
       if related: related = needed * related * needed
       chosen = kjSet()
       pr = kjSet(related) & pinned
       # choose first victim
       if has_index:
          choice = has_index.choose_key()
       elif pr:
          choice = pr.choose_key()
       elif pinned:
          choice = pinned.choose_key()
       elif related:
          choice = related.choose_key()
       else:
          return allrels[:] # give up!
       while pinned or related or has_index:
          order.append(choice)
          chosen[choice] = 1
          if pinned.has_key(choice):
             del pinned[choice]
          if related.has_key(choice):
             del related[choice]
          if has_index.has_key(choice):
             del has_index[choice]
          nexts = related * chosen
          if nexts:
             # prefer a relation related to chosen
             choice = nexts.choose_key()
          elif pinned:
             # otherwise one that is pinned
             choice = pinned.choose_key()
          elif related:
             # otherwise one that relates to something...
             choice = related.choose_key()
       others = kjSet(allrels) - chosen
       if others: order = order + others.items()
       return order
           
   def domain(self):
       kjSet = kjbuckets.kjSet
       return kjSet(self.eqs) + kjSet(self.assns)
       
   def __repr__(self):
       from string import join
       result = []
       for ( (name, att), value) in self.assns.items():
           result.append( "%s.%s=%s" % (name, att, `value`) )
       for ( (name, att), (name2, att2) ) in self.eqs.items():
           result.append( "%s.%s=%s.%s" % (name, att, name2, att2) )
       if self.clean:
          if not result: return "TRUE"
       else:
          result.insert(0, "FALSE")
       result.sort()
       return join(result, " & ")
           
   def equate(self, equalities):
       """add equalities to self, only if not closed.
          equalities should be seq of ( (name, att), (name, att) )
          """
       if self.closed: raise ValueError, "cannot add equalities! Closed!"
       e = self.eqs
       for (a, b) in equalities:
           e[a] = b
           
   def close(self):
       """infer equalities, if consistent.
          only recompute equality closure if not previously closed.
          return None on inconsistency.
       """
       neweqs = self.eqs
       if not self.closed:
          self.eqs = neweqs = (neweqs + ~neweqs).tclosure() # sym, trans closure
          self.closed = 1
       # add trivial equalities to self
       for x in self.assns.keys():
           if not neweqs.member(x,x):
              neweqs[x] = x
       newassns = self.assns.remap(neweqs)
       if newassns is not None and self.clean:
          self.assns = newassns
          #self.clean = 1
          return self
       else:
          self.clean = 0
          return None
          
   def share_eqs(self):
       """make clone of self that shares equalities, closure.
          note: will share future side effects to eqs too."""
       result = BoundTuple()
       result.eqs = self.eqs
       result.closed = self.closed
       return result
       
   def __add__(self, other):
       """combine self with other, return closure."""
       result = self.share_eqs()
       se = self.eqs
       oe = other.eqs
       if (se is not oe) and (se != oe):
          result.eqs = se + oe
          result.closed = 0
       ra= result.assns = self.assns + other.assns
       result.clean = result.clean and (ra.Clean() is not None)
       return result.close()
       
   def __and__(self, other):
      """return closed constraints common to self and other."""
      result = BoundTuple()
      se = self.eqs
      oe = other.eqs
      if (se is oe) or (se == oe):
         result.eqs = self.eqs
         result.closed = self.closed
      else:
         result.eqs = self.eqs & other.eqs
      result.assns = self.assns & other.assns
      result.clean = self.clean and other.clean
      return result.close()
      
   def __hash__(self):
      # note: equalities don't enter into hash computation!
      # (some may be spurious)
      self.close()
      return hash(self.assns)# ^ hash(self.eqs)
      
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       sa = self.assns
       oa = other.assns
       test = cmp(sa, oa)
       if test: return test
       kjSet = kjbuckets.kjSet
       kjGraph = kjbuckets.kjSet
       se = self.eqs
       se = kjGraph(se) - kjGraph(kjSet(se))
       oe = other.eqs
       oe = kjGraph(oe) - kjGraph(kjSet(oe))
       return cmp(se, oe)
      
class BoundExpression(SimpleRecursive):
   """superclass for all bound expressions.
      except where overloaded expressions are binary
      with self.left and self.right
   """
   
   contains_aggregate = 0 # default
   
   def __init__(self, left, right):
       self.left = left
       self.right = right
       self.contains_aggregate = left.contains_aggregate or right.contains_aggregate
       
   def initargs(self):
       return (self.left, self.right)
       
   def uncache(self):
       """prepare for execution, clear cached data."""
       self.left.uncache()
       self.right.uncache()
   
   # eventually add converters...
   def equate(self,other):
       """return predicate equating self and other.
          Overload for special cases, please!"""
       return NontrivialEqPred(self, other)
       
   def attribute(self):
       return (None, `self`)
       
   def le(self, other):
       """predicate self<=other"""
       return LessEqPred(self, other)
   
   # these should be overridden for 2 const case someday...
   def lt(self, other):
       """predicate self<other"""
       return LessPred(self, other)
       
   def __coerce__(self, other):
       return (self, other)
       
   def __add__(self, other):
       return BoundAddition(self, other)
       
   def __sub__(self, other):
       return BoundSubtraction(self, other)
       
   def __mul__(self, other):
       return BoundMultiplication(self, other)
       
   def __neg__(self):
       return BoundMinus(self)
       
   def __div__(self, other):
       return BoundDivision(self, other)
       
   def relbind(self, dict, db):
       Class = self.__class__
       return Class(self.left.relbind(dict, db), self.right.relbind(dict, db))
   
   def __repr__(self):
       return "(%s)%s(%s)" % (self.left, self.op, self.right)
       
   def domain(self):
       return self.left.domain() + self.right.domain()
   # always overload value
   
class BoundMinus(BoundExpression, SimpleRecursive):
   def __init__(self, thing):
       self.thing = thing
       self.contains_aggregate = thing.contains_aggregate
   def initargs(self):
       return (self.thing,)
   def __repr__(self):
       return "-(%s)" % (self.thing,)
   def value(self, contexts):
       from types import IntType
       tt = type
       result = self.thing.value(contexts)
       for i in xrange(len(contexts)):
           if tt(contexts[i]) is not IntType:
              result[i] = -result[i]
       return result
   def relbind(self, dict, db):
       Class = self.__class__
       return Class(self.thing.relbind(dict,db))
   def uncache(self):
       self.thing.uncache()
   def domain(self):
       return self.thing.domain()
       

### stuff for aggregation
class Average(BoundMinus):
       
   contains_aggregate = 1

   def __init__(self, expr, distinct=0):
       self.distinct = distinct
       if expr.contains_aggregate:
          raise ValueError, `expr`+": aggregate in aggregate "+self.name
       self.thing = expr
       
   name = "Average"
   def __repr__(self):
       distinct = ""
       if self.distinct:
          distinct = "distinct "
       return "%s(%s%s)" % (self.name, distinct, self.thing)

   def relbind(self, dict, db):
       Class = self.__class__
       return Class(self.thing.relbind(dict,db), self.distinct)
       
   def value(self, contexts):
       if not contexts: return [] # ???
       test = contexts[0]
       if not test.has_key(None):
          return [self.all_value(contexts)]
       else:
          return self.agg_value(contexts)
          
   def dvalues(self, values):
       d = {}
       for i in xrange(len(values)):
           d[values[i]] = 1
       return d.keys()
          
   def all_value(self, contexts):
       thing = self.thing
       values = self.clean(thing.value(contexts), contexts)
       if self.distinct:
          values = self.dvalues(values)
       return self.op(values)
       
   def clean(self, values, contexts):
       D = {}
       from types import IntType
       tt = type
       for i in xrange(len(contexts)):
           if tt(contexts[i]) is not IntType:
              D[i] = values[i]
       return D.values()
       
   def agg_value(self, contexts):
       from types import IntType
       tt = type
       result = list(contexts)
       for i in xrange(len(contexts)):
           context = contexts[i]
           if tt(context) is not IntType:
              result[i] = self.all_value( context[None] )
       return result
       
   def op(self, values):
       sum = 0
       for x in values:
           sum = sum+x
       return sum/(len(values)*1.0)
       
class Sum(Average):
   name = "Sum"
   def op(self, values):
       if not values: return 0
       sum = values[0]
       for x in values[1:]:
           sum = sum+x
       return sum
       
class Median(Average):
   name = "Median"
   def op(self, values):
       if not values:
          raise ValueError, "Median of empty set"
       values = list(values)
       values.sort()
       lvals = len(values)
       return values[lvals/2]
   
class Maximum(Average):
   name = "Maximum"
   def op(self, values):
       return max(values)
       
class Minimum(Average):
   name = "Minimum"
   def op(self, values):
       return min(values)
       
class Count(Average):
   name = "Count"
   distinct = 0
   def __init__(self, thing, distinct = 0):
       if thing=="*":
          self.thing = "*"
       else:
          Average.__init__(self, thing, distinct)
          
   def domain(self):
       thing = self.thing
       if thing=="*":
          return kjbuckets.kjSet()
       return thing.domain()
       
   def all_value(self, contexts):
       thing = self.thing
       if thing=="*" or not self.distinct:
          test = self.clean(contexts, contexts)
          #print "count len", len(test), contexts[0]
          return len(test)
       return Average.all_value(self, contexts)
   def op(self, values):
       return len(values)
   def relbind(self, dict, db):
       if self.thing=="*":
          return self
       return Average.relbind(self, dict, db)
   def uncache(self):
       if self.thing!="*": self.thing.uncache()

def aggregate(assignments, exprlist):
    """aggregates are a assignments with special
       attribute None --> list of subtuple"""
    lexprs = len(exprlist)
    if lexprs<1:
       raise ValueError, "aggregate on no expressions?"
    lassns = len(assignments)
    pairs = list(exprlist)
    for i in xrange(lexprs):
        expr = exprlist[i]
        attributes = [expr.attribute()]*lassns
        values = expr.value(assignments)
        pairs[i] = map(None, attributes, values)
    #for x in pairs:
        #print "pairs", x
    if lexprs>1:
       newassnpairs = apply(map, (None,)+tuple(pairs))
    else:
       newassnpairs = pairs[0]
    #for x in newassnpairs:
        #print "newassnpairs", x
    xassns = range(lassns)
    dict = {}
    test = dict.has_key
    for i in xrange(lassns):
        thesepairs = newassnpairs[i]
        thissubassn = assignments[i]
        if test(thesepairs):
           dict[thesepairs].append(thissubassn)
        else:
           dict[thesepairs] = [thissubassn]
    items = dict.items()
    result = list(items)
    kjDict = kjbuckets.kjDict
    if lexprs>1:
       for i in xrange(len(items)):
           (pairs, subassns) = items[i]
           #print "pairs", pairs
           #print "subassns", subassns
           D = kjDict(pairs)
           D[None] = subassns
           result[i] = D
    else:
       for i in xrange(len(items)):
           (pair, subassns) = items[i]
           #print "pair", pair
           #print "subassns", subassns
           result[i] = kjDict( [pair, (None, subassns)] )
    return result

### stuff for order_by
class DescExpr(BoundMinus):
   """special wrapper used only for order by descending
      for things with no -thing operation (eg, strings)"""
      
   def __init__(self, thing):
       self.thing = thing
       self.contains_aggregate = thing.contains_aggregate

   def value(self, contexts):
       from types import IntType, StringType
       tt = type
       result = self.thing.value(contexts)
       allwrap = None
       allnowrap = None
       for i in xrange(len(contexts)):
           if tt(contexts[i]) is not IntType:
              resulti = result[i]
              # currently assume only value needing wrapping is string
              if tt(resulti) is StringType:
                 if allnowrap is not None:
                    raise ValueError, "(%s, %s) cannot order desc" % (allnowrap, resulti)
                 allwrap = resulti
                 result[i] = descOb(resulti)
              else:
                 if allwrap is not None:
                    raise ValueError, "(%s, %s) cannot order desc" % (allwrap, resulti)
                 allnowrap = resulti
                 result[i] = -resulti
       return result
   def __repr__(self):
       return "DescExpr(%s)" % (self.thing,)
   def orderbind(self, order):
       """order is list of (att, expr)."""
       Class = self.__class__
       return Class(self.thing.orderbind(order))
       
class SimpleColumn(SimpleRecursive):
   """a simple column name for application to a list of tuples"""
   contains_aggregate = 0
   def __init__(self, name):
       self.name = name
   def relbind(self, dict, db):
       # already bound!
       return self
   def orderbind(self, whatever):
       # already bound!
       return self
   def initargs(self):
       return (self.name,)
   def value(self, simpletuples):
       from types import IntType
       tt = type
       name = self.name
       result = list(simpletuples)
       for i in xrange(len(result)):
           ri = result[i]
           if tt(ri) is not IntType:
              result[i] = ri[name]
           else:
              result[i] = None # ???
       return result
   def __repr__(self):
       return "<SimpleColumn %s>" % (self.name,)
       
class NumberedColumn(BoundMinus):
   """order by column number"""
   contains_aggregate = 0
   def __init__(self, num):
       self.thing = num
   def __repr__(self):
       return "<NumberedColumn %s>" % (self.thing,)
   def relbind(self, dict, db):
       from types import IntType
       if type(self.thing)!=IntType:
          raise ValueError, `self.thing`+": not a numbered column"
       return self
   def orderbind(self, order):
       return SimpleColumn( order[self.thing-1][0] )
       
class OrderExpr(BoundMinus):
   """order by expression."""
   def orderbind(self, order):
       expratt = self.thing.attribute()
       for (att, exp) in order:
           if exp.attribute()==expratt:
              return SimpleColumn(att)
       else:
           raise NameError, `self`+": invalid ordering specification"
   def __repr__(self):
       return "<order expression %s>" % (self.thing,)
       
class descOb:

   """special wrapper only used for sorting in descending order
      should only be compared with other descOb instances.
      should only wrap items that cannot be easily "order inverted",
      (eg, strings).
   """
      
   def __init__(self, ob):
       self.ob = ob
       
   def __cmp__(self, other):
       #test = cmp(self.__class__, other.__class__)
       #if test: return test
       return -cmp(self.ob,other.ob)
       
   def __coerce__(self, other):
       return (self, other)
       
   def __hash__(self):
       return hash(self.ob)
       
   def __repr__(self):
       return "descOb(%s)" % (self.ob,)
       
def PositionedSort(num, ord):
    nc = NumberedColumn(num)
    if ord=="DESC":
       return DescExpr(nc)
    return nc
    
def NamedSort(name, ord):
    oe = OrderExpr(name)
    if ord=="DESC":
       return DescExpr(oe)
    return oe
    
def relbind_sequence(order_list, dict, db):
    result = list(order_list)
    for i in xrange(len(order_list)):
        result[i] = result[i].relbind(dict,db)
    return result
        
def orderbind_sequence(order_list, order):
    result = list(order_list)
    for i in xrange(len(order_list)):
        result[i] = result[i].orderbind(order)
    return result
    
def order_tuples(order_list, tuples):
    lorder_list = len(order_list)
    ltuples = len(tuples)
    if lorder_list<1:
       raise ValueError, "order on empty list?"
    order_map = list(order_list)
    for i in xrange(lorder_list):
        order_map[i] = order_list[i].value(tuples)
    if len(order_map)>1:
       order_vector = apply(map, (None,)+tuple(order_map) )
    else:
       order_vector = order_map[0]
    #G = kjbuckets.kjGraph()
    pairs = map(None, range(ltuples), tuples)
    ppairs = map(None, order_vector, pairs)
    G = kjbuckets.kjGraph(ppairs)
    #for i in xrange(ltuples):
    #    G[ order_vector[i] ] = (i, tuples[i])
    Gkeys = G.keys()
    Gkeys.sort()
    result = list(tuples)
    index = 0
    for x in Gkeys:
        #print x
        for (i, y) in G.neighbors(x):
            #print "   ", y
            result[index]=y
            index = index+1
    if index!=ltuples:
       raise ValueError, \
        "TUPLE LOST IN ORDERING COMPUTATION! (%s,%s)" % (ltuples, index)
    return result
   
class BoundAddition(BoundExpression):
   """promised addition."""
   op = "+"
   def value(self, contexts):
       from types import IntType
       tt = type
       lvs = self.left.value(contexts)
       rvs = self.right.value(contexts)
       for i in xrange(len(contexts)):
           if tt(contexts[i]) is not IntType:
              lvs[i] = lvs[i] + rvs[i]
       return lvs
   
class BoundSubtraction(BoundExpression):
   """promised subtraction."""
   op = "-"
   def value(self, contexts):
       from types import IntType
       tt = type
       lvs = self.left.value(contexts)
       rvs = self.right.value(contexts)
       for i in xrange(len(contexts)):
           if tt(contexts[i]) is not IntType:
              lvs[i] = lvs[i] - rvs[i]
       return lvs
   
class BoundMultiplication(BoundExpression):
   """promised multiplication."""
   op = "*"
   def value(self, contexts):
       from types import IntType
       tt = type
       lvs = self.left.value(contexts)
       rvs = self.right.value(contexts)
       #print lvs
       for i in xrange(len(contexts)):
           if tt(contexts[i]) is not IntType:
              lvs[i] = lvs[i] * rvs[i]
       return lvs
   
class BoundDivision(BoundExpression):
   """promised division."""
   op = "/"
   def value(self, contexts):
       from types import IntType
       tt = type
       lvs = self.left.value(contexts)
       rvs = self.right.value(contexts)
       for i in xrange(len(contexts)):
           if tt(contexts[i]) is not IntType:
              lvs[i] = lvs[i] / rvs[i]
       return lvs
       
class BoundAttribute(BoundExpression):
   """bound attribute: initialize with relname=None if
      implicit."""
      
   contains_aggregate = 0
      
   def __init__(self, rel, name):
       self.rel = rel
       self.name = name
       
   def initargs(self):
       return (self.rel, self.name)
       
   def relbind(self, dict, db):
       if self.rel is not None: return self
       name = self.name
       try:
           rel = dict[name]
       except KeyError:
           raise NameError, `name` + ": unknown or ambiguous"
       return BoundAttribute(rel, name)
       
   def uncache(self):
       pass
       
   def __repr__(self):
       return "%s.%s" % (self.rel, self.name)
       
   def attribute(self):
       """return (rename, attribute) for self."""
       return (self.rel, self.name)
       
   def domain(self):
       return kjbuckets.kjSet([ (self.rel, self.name) ])
       
   def value(self, contexts):
       """return value of self in context (bound tuple)."""
       #print "value of ", self, "in", contexts
       from types import IntType
       tt = type
       result = list(contexts)
       ra = (self.rel, self.name)
       for i in xrange(len(result)):
           if tt(result[i]) is not IntType:
              result[i] = contexts[i][ra]
       return result
       
   def equate(self, other):
       oc = other.__class__
       if oc==BoundAttribute:
          result = BoundTuple()
          result.equate([(self.attribute(), other.attribute())])
          return BTPredicate(result)
       elif oc==Constant:
          result = BoundTuple()
          result.assns[ self.attribute() ] = other.value([1])[0]
          return BTPredicate(result)
       else:
          return NontrivialEqPred(self, other)
          
class Constant(BoundExpression):
   contains_aggregate = 0
   
   def __init__(self, value):
       self.value0 = value
       
   def __hash__(self):
       return hash(self.value0)
       
   def initargs(self):
       return (self.value0,)
       
   def domain(self):
       return kjbuckets.kjSet()
       
   def __add__(self, other):
       if other.__class__==Constant:
          return Constant(self.value0 + other.value0)
       return BoundAddition(self, other)
       
   def __sub__(self, other):
       if other.__class__==Constant:
          return Constant(self.value0 - other.value0)
       return BoundSubtraction(self, other)
       
   def __mul__(self, other):
       if other.__class__==Constant:
          return Constant(self.value0 * other.value0)
       return BoundMultiplication(self, other)
       
   def __neg__(self):
       return Constant(-self.value0)
       
   def __div__(self, other):
       if other.__class__==Constant:
          return Constant(self.value0 / other.value0)
       return BoundDivision(self, other)

   def relbind(self, dict, db):
       return self
       
   def uncache(self):
       pass
       
   def value(self, contexts):
       """return the constant value associated with self."""
       return [self.value0] * len(contexts)
       
   def equate(self,other):
       if other.__class__==Constant:
          if other.value0 == self.value0:
             return BTPredicate() #true
          else:
             return ~BTPredicate() #false
       else:
          return other.equate(self)
          
   def attribute(self):
       """invent a pair to identify a constant"""
       return ('unbound', `self`)
       
   def __repr__(self):
       return "<const %s at %s>" % (`self.value0`, id(self))
          
class TupleCollector:
   """Translate a sequence of assignments to simple tuples.
      (for implementing the select list of a SELECT).
   """
   contains_aggregate = 0
   contains_nonaggregate = 0
   
   def __init__(self):
       self.final = None
       self.order = []
       self.attorder = []
       self.exporder = []
       
   def initargs(self):
       return ()
       
   def marshaldata(self):
       exps = map(serialize, self.exporder)
       return (self.attorder, exps, 
               self.contains_aggregate, self.contains_nonaggregate)
       
   def demarshal(self, args):
       (self.attorder, exps, self.contains_aggregate,
        self.contains_nonaggregate) = args
       exporder = self.exporder = map(deserialize, exps)
       self.order = map(None, self.attorder, exporder)
       
   def uncache(self):
       for exp in self.exporder:
           exp.uncache()
       
   def domain(self):
       all=[]
       for e in self.exporder:
           all = all+e.domain().items()
       return kjbuckets.kjSet(all)
       
   def __repr__(self):
       l = []
       for (att, exp) in self.order:
           l.append( "%s as %s" % (exp, att) )
       from string import join
       return join(l, ", ")
       
   def addbinding(self, attribute, expression):
       """bind att-->expression."""
       self.order.append((attribute, expression) )
       self.attorder.append(attribute )
       self.exporder.append(expression)
       if expression.contains_aggregate:
          self.contains_aggregate = 1
       else:
          self.contains_nonaggregate = 1
       
   def map(self, assnlist):
       """remap btlist by self. return (tuplelist, attorder)"""
       # DON'T eliminate nulls
       from types import IntType
       tt = type
       values = []
       for exp in self.exporder:
           values.append(exp.value(assnlist))
       if len(values)>1:
          valtups = apply(map, (None,) + tuple(values) )
       else:
          valtups = values[0]
       kjUndump = kjbuckets.kjUndump
       undumper = tuple(self.attorder)
       for i in xrange(len(valtups)):
           test = assnlist[i]
           if tt(test) is IntType or test is None:
              valtups[i] = 0 # null/false
           else:
              tup = valtups[i]
              valtups[i] = kjUndump(undumper, tup)
       return (valtups, self.attorder)
       
   def relbind(self, dict, db):
       """disambiguate missing rel names if possible.
          also choose output names appropriately."""
       # CURRENTLY THIS IS AN "IN PLACE" OPERATION
       order = self.order
       attorder = self.attorder
       exporder = self.exporder
       known = {}
       for i in xrange(len(order)):
           (att, exp) = order[i]
           #print exp
           exp = exp.relbind(dict, db)
           if att is None:
              # choose a name for this column
              #print exp
              (rname, aname) = exp.attribute()
              if known.has_key(aname):
                 both = rname+"."+aname
                 att = both
                 count = 0
                 while known.has_key(att):
                    # crank away!
                    count = count+1
                    att = both+"."+`count`
              else:
                 att = aname
           else:
              if known.has_key(att):
                 raise NameError, `att`+" ambiguous in select list"
           order[i] = (att, exp)
           exporder[i] = exp
           attorder[i] = att
           known[att] = att
       return self

class BTPredicate(SimpleRecursive):
   """superclass for bound tuple predicates.
      Eventually should be modified to use "compile" for speed
      to generate an "inlined" evaluation function.
      self(bt) returns bt with additional equality constraints
      (possible) or None if predicate fails."""
      
   false = 0
   constraints = None
   contains_aggregate = 0
      
   def __init__(self, constraints=None):
       """default interpretation: True."""
       if constraints is not None:
          self.constraints = constraints.close()
          
   def initargs(self):
       return (self.constraints,)
          
   def relbind(self, dict, db):
       c = self.constraints
       if c is None: return self
       return BTPredicate( self.constraints.relbind(dict, db) )
       
   def uncache(self):
       pass
          
   #def evaluate(self, db, relnames):
       #"""evaluate the predicate over database bindings."""
       # pretty simple strategy right now...
       ### need to do something about all/distinct...
       #c = self.constraints
       #if c is None:
       #  c = BoundTuple()
       #order = c.relorder(db, relnames)
       #if not order:
       #   raise ValueError, "attempt to evaluate over no relations: "+`relnames`
       #result = [c]
       #for r in order:
       #    result = hashjoin(result, r, db[r])
       #if self.__class__==BTPredicate:
       #   # if it's just equality conjunction, we're done
       #   return result
       #else:
       #   # apply additional constraints
       #   return self(result)
          
   def domain(self):
       c = self.constraints
       kjSet = kjbuckets.kjSet
       if c is None: return kjSet()
       return c.domain()
       
   def __repr__(self):
       if self.false: return "FALSE"
       c = self.constraints
       if c is None: c = "true"
       return "[pred](%s)" % c
          
   def detrivialize(self):
       """hook added to allow elimination of trivialities
          return None if completely true, or simpler form
          or self, if no simplification is possible."""
       if self.false: return self
       if not self.constraints: return None
       return self
          
   def negated_constraints(self):
       """equality constraints always false of satisfactory tuple."""
       return BoundTuple() # there aren't any
       
   def __call__(self, assignments, toplevel=0):
       """apply self to sequence of assignments
          return copy of asssignments with false results
          replaced by 0!  Input may have 0's!"""
       # optimization
       #   if toplevel, the btpred has been evaluated during join.
       if toplevel:
          return list(assignments)
       from types import IntType
       tt = type
       lbt = len(assignments)
       if self.false: return [0] * lbt
       c = self.constraints
       if c is None or not c:
          result = assignments[:] # no constraints
       else:
          assns = c.assns
          eqs = c.eqs
          eqsinteresting = 0
          for (a,b) in eqs.items():
              if a!=b:
                 eqsinteresting = 1
          result = assignments[:]
          for i in xrange(lbt):
              this = assignments[i]
              #print "comparing", self, "to", this
              if type(this) is IntType: continue
              this = (this + assns).Clean()
              if this is None:
                 result[i] = 0
              elif eqsinteresting:
                 this = this.remap(eqs)
                 if this is None:
                    result[i] = 0
       return result
          
   def __and__(self, other):
       """NOTE: all subclasses must define an __and__!!!"""
       #print "BTPredicate.__and__", (self, other)
       if self.__class__==BTPredicate and other.__class__==BTPredicate:
          c = self.constraints
          o = other.constraints
          if c is None: return other
          if o is None: return self
          if self.false: return self
          if other.false: return other
          # optimization for simple constraints
          all = (c+o)
          result = BTPredicate( all ) # all constraints
          if all is None: result.false = 1
       else:
          result = other & self
       return result
       
   def __or__(self, other):
       if self.__class__==BTPredicate and other.__class__==BTPredicate:
          c = self.constraints
          o = other.constraints
          if c is None: return self # true dominates
          if o is None: return other
          if other.false: return self
          if self.false: return other
          if self == other: return self
       result = BTor_pred([self, other])
       return result
       
   def __invert__(self):
       if self.false:
          return BTPredicate()
       if not self.constraints:
          result = BTPredicate()
          result.false = 1
          return result
       return BTnot_pred(self)
       
   def __cmp__(self, other):
       test = cmp(other.__class__, self.__class__)
       if test: return test
       if self.false and other.false: return 0
       return cmp(self.constraints, other.constraints)
       
   def __hash__(self):
       if self.false: return 11111
       return hash(self.constraints)
       
class BTor_pred(BTPredicate):

   def __init__(self, members, *othermembers):
       # replace any OR in members with its members
       #print "BTor_pred", members
       members = list(members) + list(othermembers)
       for m in members[:]:
           if m.__class__==BTor_pred:
              members.remove(m)
              members = members + m.members
       #print "before", members
       members = self.members = kjbuckets.kjSet(members).items()
       #print members
       for m in members[:]:
           if m.false: members.remove(m)
       self.constraints = None # common constraints
       for m in members:
          if m.contains_aggregate:
             self.contains_aggregate = 1
       if members:
          # common constraints are those in all members
          constraints = members[0].constraints
          for m in members[1:]:
              mc = m.constraints
              if not constraints or not mc:
                 constraints = None
                 break
              constraints = constraints & mc
          self.constraints = constraints
       #print members
       
   def initargs(self):
       return ((),) + tuple(self.members)
          
   def relbind(self, dict, db):
       ms = []
       for m in self.members:
           ms.append( m.relbind(dict, db) )
       return BTor_pred(ms)
       
   def uncache(self):
       for m in self.members:
           m.uncache()
          
   def domain(self):
       all = BTPredicate.domain(self).items()
       for x in self.members:
           all = all + x.domain().items()
       return kjbuckets.kjSet(all)
       
   def __repr__(self):
       c = self.constraints
       m = self.members
       mr = map(repr, m)
       from string import join
       mr.sort()
       mr = join(mr, " | ")
       if not mr: mr = "FALSE_OR"
       if c:
          mr = "[disj](%s and %s)" % (c, mr)
       return mr

   def detrivialize(self):
       """hook added to allow elimination of trivialities
          return None if completely true, or simpler form
          or self, if no simplification is possible."""
       ms = self.members
       for i in xrange(len(ms)):
           ms[i] = ms[i].detrivialize()
       # now suck out subordinate ors
       someor = None
       for m in ms:
           if m.__class__== BTor_pred:
              someor = m
              ms.remove(m)
              break
       if someor is not None:
           result = someor
           for m in ms:
               result = result + m
           return result.detrivialize()
       allfalse = 1
       for m in ms:
           if m is None: allfalse=0; break # true member
           allfalse = allfalse & m.false
       if allfalse: return ~BTPredicate() # boundary case
       ms[:] = filter(None, ms)
       if not ms: return None # all true.
       ms[:] = kjbuckets.kjSet(ms).items()
       if len(ms)==1: return ms[0] # or of 1
       return self           

   def __call__(self, boundtuples, toplevel=0):
       # apply common constraints first
       lbt = len(boundtuples)
       # boundary case for or is false
       members = self.members
       if not members:
          return [0] * lbt
       current = BTPredicate.__call__(self, boundtuples, toplevel)
       # now apply first alternative
       alt1 = members[0](current)
       # determine questionables
       questionables = current[:]
       rng = xrange(len(current))
       from types import IntType
       tt = type
       for i in rng:
           if tt(alt1[i]) is not IntType:
              questionables[i]=0
       # now test other alternatives
       #print "alt1", members[0]
       #for x in alt1: 
           #print x
       for m in self.members[1:]:
           #print "questionables", m
           #for x in questionables:
               #print x
           passm = m(questionables)
           for i in rng:
               test = passm[i]
               if tt(test) is not IntType:
                  questionables[i] = 0
                  alt1[i] = test
       return alt1

   def negated_constraints(self):
       """the negated constraints of an OR are
          the negated constraints of *all* members"""
       ms = self.members
       result = ms.negated_constraints()
       for m in ms[1:]:
           if not result: return result
           mc = m.negated_constraints()
           if not mc: return mc
           result = result & mc
       return result
       
   def __and__(self, other):
       """push "and" down"""
       newmembers = self.members[:]
       for i in xrange(len(newmembers)):
           newmembers[i] = newmembers[i] & other
       return BTor_pred(newmembers)
       
   def __or__(self, other):
       """collapse two ors, otherwise just add new member"""
       if self.__class__==BTor_pred and other.__class__==BTor_pred:
          return BTor_pred(self.members+other.members)
       return BTor_pred(self.members + [other])
       
   def __invert__(self):
       """translate to and-not"""
       ms = self.members
       if not ms: return BTPredicate() # boundary case
       result = ~ms[0]
       for m in ms[1:]:
           result = result & ~m
       return result
       
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       kjSet = kjbuckets.kjSet
       test = cmp(kjSet(self.members), kjSet(other.members))
       if test: return test
       return BTPredicate.__cmp__(self, other)
       
   def __hash__(self):
       return hash(kjbuckets.kjSet(self.members))
       
class BTnot_pred(BTPredicate):

   def __init__(self, thing):
       self.negated = thing
       self.contains_aggregate = thing.contains_aggregate
       self.constraints = thing.negated_constraints()
       
   def initargs(self):
       return (self.negated,)
       
   def relbind(self, dict, db):
       return BTnot_pred( self.negated.relbind(dict, db) )
       
   def uncache(self):
       self.negated.uncache()
       
   def domain(self):
       result = BTPredicate.domain(self) + self.negated.domain()
       #print "neg domain is", `self`, result
       return result
       
   def __repr__(self):
       c = self.constraints
       n = self.negated
       r = "(NOT %s)" % n
       if c: r = "[neg](%s & %s)" % (c, r)
       return r

   def detrivialize(self):
       """hook added to allow elimination of trivialities
          return None if completely true, or simpler form
          or self, if no simplification is possible."""
       # first, fix or/and/not precedence
       thing = self.negated
       if thing.__class__ == BTnot_pred:
          return thing.negated.detrivialize()
       if thing.__class__ == BTor_pred:
          # translate to and_not
          members = thing.members[:]
          for i in xrange(len(members)):
              members[i] = ~members[i]
          result = BTand_pred(members)
          return result.detrivialize()
       if thing.__class__ == BTand_pred:
          # translate to or_not
          members = thing.members[:]
          c = thing.constraints # precondition
          if c is not None:
             members.append(BTPredicate(c))
          for i in xrange(len(members)):
              members[i] = ~members[i]
          result = BTor_pred(members)
          return result.detrivialize()
       self.negated = thing = self.negated.detrivialize()
       if thing is None: return ~BTPredicate() # uniquely false
       if thing.false: return None # uniquely true
       return self

   def __call__(self, boundtuples, toplevel=0):
       from types import IntType
       tt = type
       current = BTPredicate.__call__(self, boundtuples, toplevel)
       omit = self.negated(current)
       for i in xrange(len(current)):
           if tt(omit[i]) is not IntType:
              current[i]=0
       return current

   def negated_constraints(self):
       """the negated constraints of a NOT are the
          negated constraints of the thing negated."""
       return self.negated.constraints
       
   def __and__(self, other):
       """do the obvious thing."""
       return BTand_pred([self, other])
       
   def __or__(self, other):
       """do the obvious thing"""
       return BTor_pred([self, other])
       
   def __invert__(self):
       return self.negated
       
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       test = cmp(self.negated,other.negated)
       if test: return test
       return BTPredicate.__cmp__(self,other)
       
   def __hash__(self):
       return hash(self.negated)^787876^hash(self.constraints)
       
class BTand_pred(BTPredicate):

   def __init__(self, members, precondition=None, *othermembers):
       #print "BTand_pred", (members, precondition)
       members = list(members) + list(othermembers)
       members = self.members = kjbuckets.kjSet(members).items()
       self.constraints = precondition # common constraints
       if members:
          # common constraints are those in any member
          if precondition is not None:
             constraints = precondition
          else:
             constraints = BoundTuple()
          for i in xrange(len(members)):
              m = members[i]
              mc = m.constraints
              if mc:
                 #print "constraints", constraints
                 constraints = constraints + mc
                 if constraints is None: break
              if m.__class__==BTPredicate:
                 members[i] = None # subsumed above
          members = self.members = filter(None, members)
          for m in members:
              if m.contains_aggregate:
                 self.contains_aggregate=1
          ### consider propagating constraints down?
          self.constraints = constraints
          if constraints is None: self.false = 1
          
   def initargs(self):
       #print "self.members", self.members
       #print "self.constraints", self.constraints
       #return (list(self.members), self.constraints)
       return ((), self.constraints) + tuple(self.members)
          
   def relbind(self, dict, db):
       ms = []
       for m in self.members:
           ms.append( m.relbind(dict, db) )
       c = self.constraints.relbind(dict, db)
       return BTand_pred(ms, c)
       
   def uncache(self):
       for m in self.members:
           m.uncache()
          
   def domain(self):
       all = BTPredicate.domain(self).items()
       for x in self.members:
           all = all + x.domain().items()
       return kjbuckets.kjSet(all)
       
   def __repr__(self):
       m = self.members
       c = self.constraints
       r = map(repr, m)
       if self.false: r.insert(0, "FALSE")
       from string import join
       r = join(r, " AND ")
       r = "(%s)" % r
       if c: r = "[conj](%s and %s)" % (c, r)
       return r

   def detrivialize(self):
       """hook added to allow elimination of trivialities
          return None if completely true, or simpler form
          or self, if no simplification is possible."""
       # first apply demorgan's law to push ands down
       # (exponential in worst case).
       #print "detrivialize"
       #print self
       ms = self.members
       some_or = None
       c = self.constraints
       for m in ms:
           if m.__class__==BTor_pred:
              some_or = m
              ms.remove(m)
              break
       if some_or is not None:
          result = some_or
          if c is not None:
             some_or = some_or & BTPredicate(c)
          for m in ms:
              result = result & m # preserves or/and precedence
          if result.__class__!=BTor_pred:
             raise "what the?"
          result = result.detrivialize()
          #print "or detected, returning"
          #print result
          return result
       for i in xrange(len(ms)):
           ms[i] = ms[i].detrivialize()
       ms[:] = filter(None, ms)
       if not ms:
          #print "returning boundary case of condition"
          if c is None:
             return None
          else: 
             return BTPredicate(c).detrivialize()
       ms[:] = kjbuckets.kjSet(ms).items()
       if len(ms)==1 and c is None: 
          #print "and of 1, returning"
          #print ms[0]
          return ms[0] # and of 1
       return self           

   def __call__(self, boundtuples, toplevel=0):
       # apply common constraints first
       current = BTPredicate.__call__(self, boundtuples, toplevel)
       for m in self.members:
           current = m(current)
       return current

   def negated_constraints(self):
       """the negated constraints of an AND are
          the negated constraints of *any* member"""
       ms = self.members
       result = BoundTuple()
       for m in ms:
           mc = m.negated_constraints()
           if mc: result = result + mc 
       return result
       
   def __and__(self, other):
       """push "and" down if other is an or"""
       if other.__class__==BTor_pred:
          return other & self
       c = self.constraints
       # merge in other and
       if other.__class__==BTand_pred:
          allmem = self.members+other.members
          oc = other.constraints
          if c is None:
             c = oc
          elif oc is not None:
             c = c+oc
          return BTand_pred(allmem, c)
       return BTand_pred(self.members + [other], c)
       
   def __or__(self, other):
       """do the obvious thing."""
       return BTor_pred([self, other])
       
   def __invert__(self):
       """translate to or-not"""
       ms = self.members
       if not ms: return ~BTPredicate() # boundary case
       result = ~ms[0]
       for m in ms[1:]:
           result = result | ~m
       return result
       
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       kjSet = kjbuckets.kjSet
       test = cmp(kjSet(self.members), kjSet(other.members))
       if test: return test
       return BTPredicate.__cmp__(self, other)
       
   def __hash__(self):
       return hash(kjbuckets.kjSet(self.members))
       
class NontrivialEqPred(BTPredicate):
   """equation of nontrivial expressions."""
   
   def __init__(self, left, right):
       #print "making pred", self.__class__, left, right
       # maybe should used reflexivity...
       self.left = left
       self.right = right
       self.contains_aggregate = left.contains_aggregate or right.contains_aggregate
       
   def initargs(self):
       return (self.left, self.right)
       
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       test = cmp(self.right, other.right)
       if test: return test
       return cmp(other.left, other.left)
       
   def hash(self, other):
       return hash(self.left) ^ hash(self.right)
       
   def relbind(self, dict, db):
       Class = self.__class__
       return Class(self.left.relbind(dict,db), self.right.relbind(dict,db) )
       
   def uncache(self):
       self.left.uncache()
       self.right.uncache()
       
   def domain(self):
       return self.left.domain() + self.right.domain()
       
   op = "=="
       
   def __repr__(self):
       return "(%s)%s(%s)" % (self.left, self.op, self.right)
       
   def detrivialize(self):
       return self
       
   def __call__(self, assigns, toplevel=0):
       from types import IntType
       tt = type
       lv = self.left.value(assigns)
       rv = self.right.value(assigns)
       result = assigns[:]
       for i in xrange(len(assigns)):
           t = assigns[i]
           if type(t) is not IntType and lv[i]!=rv[i]:
              result[i] = 0
       return result
       
   def negated_constraints(self):
       return None
       
   def __and__(self, other):
       return BTand_pred( [self, other] )
       
   def __or__(self, other):
       return BTor_pred( [self, other] )
       
   def __invert__(self):
       return BTnot_pred(self)
       
class BetweenPredicate(NontrivialEqPred):
   """e1 BETWEEN e2 AND e3"""
   def __init__(self, middle, lower, upper):
       self.middle = middle
       self.lower = lower
       self.upper = upper
       
   def initargs(self):
       return (self.middle, self.lower, self.upper)
       
   def domain(self):
       return (
   self.middle.domain() + self.lower.domain() + self.upper.domain())
        
   def relbind(self, dict, db):
       self.middle = self.middle.relbind(dict, db)
       self.lower = self.lower.relbind(dict, db)
       self.upper = self.upper.relbind(dict, db)
       return self
       
   def uncache(self):
       self.middle.uncache()
       self.upper.uncache()
       self.lower.uncache()
       
   def __repr__(self):
       return "(%s BETWEEN %s AND %s)" % (
        self.middle, self.lower, self.upper)
        
   def __hash__(self):
       return hash(self.middle)^~hash(self.lower)^hash(self.upper)^55
       
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       test = cmp(self.lower, other.lower)
       if test: return test
       test = cmp(self.middle, other.middle)
       if test: return test
       return cmp(self.upper, other.upper)
       
   def __call__(self, assigns, toplevel=0):
       from types import IntType
       tt = type
       lowv = self.lower.value(assigns)
       upv = self.upper.value(assigns)
       midv = self.middle.value(assigns)
       result = assigns[:]
       for i in xrange(len(assigns)):
           t = assigns[i]
           if tt(t) is not IntType:
              midvi = midv[i]
              if lowv[i]>midvi or upv[i]<midvi:
                 result[i] = 0
       return result
       
class ExistsPred(NontrivialEqPred):
   """EXISTS subquery."""
   contains_aggregate = 0
   
   def __init__(self, subq):
       self.cached_result = None
       self.cachable = None
       self.subq = subq
       
   def initargs(self):
       return (self.subq,)
       
   def domain(self):
       result = self.subq.unbound()
       # if there are no outer bindings, evaluate ONCE!
       if not result:
          self.cachable = 1
       return result
       
   def relbind(self, dict, db):
       self.subq = self.subq.relbind(db, dict)
       return self
       
   def uncache(self):
       self.cached_result = None
       self.subq.uncache()
       
   def __repr__(self):
       return "\nEXISTS\n%s\n" % (self.subq,)
       
   def __call__(self, assigns, toplevel=0):
       ### should optimize!!!
       #print "exists"
       #print self.subq
       from types import IntType
       tt = type
       eval = self.subq.eval
       result = assigns[:]
       # shortcut: if cachable, eval only once and cache
       if self.cachable:
           test = self.cached_result
           if test is None:
              self.cached_result = test = eval()
           #print "exists cached", self.cached_result
           if test:
              return result
           else:
              return [0] * len(result)
       kjDict = kjbuckets.kjDict
       for i in xrange(len(assigns)):
           #print "exists uncached"
           assignsi = assigns[i]
           if tt(assignsi) is IntType: continue
           testbtup = BoundTuple()
           testbtup.assns = kjDict(assignsi)
           test = eval(outerboundtuple=testbtup).rows()
           #for x in test:
               #print "exists for", assignsi
               #print x
               #break
           if not test:
                 result[i] = 0
       return result
       
   def __hash__(self):
       return hash(self.subq)^3333
       
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       return cmp(self.subq, other.subq)
       
class QuantEQ(NontrivialEqPred):
   """Quantified equal any predicate"""
   
   def __init__(self, expr, subq):
       self.expr = expr
       self.subq = subq
       self.cachable = 0
       self.cached_column = None
       self.att = None
       
   def initargs(self):
       return (self.expr, self.subq)
       
   def uncache(self):
       self.cached_column = None
       
   def domain(self):
       first = self.subq.unbound()
       if not first:
          self.cachable = 1
       more = self.expr.domain()
       return first + more
       
   def relbind(self, dict, db):
       subq = self.subq = self.subq.relbind(db, dict)
       self.expr = self.expr.relbind(dict, db)
       # test that subquery is single column and determine att
       sl = subq.select_list
       atts = sl.attorder
       if len(atts)<>1:
          raise ValueError, \
            "Quantified predicate requires unit select list: %s" % atts
       self.att = atts[0]
       return self
       
   fmt = "(%s %s ANY %s)"
   op = "="
       
   def __repr__(self):
       return self.fmt % (self.expr, self.op, self.subq)
       
   def __call__(self, assigns, toplevel=0):
       cached_column = self.cached_column
       cachable = self.cachable
       expr = self.expr
       subq = self.subq
       att = self.att
       if cachable:
           if cached_column is None:
               subqr = subq.eval().rows()
               cc = self.cached_column = dump_single_column(subqr, att)
           #print self, "cached", self.cached_column
       exprvals = expr.value(assigns)
       kjDict = kjbuckets.kjDict
       compare = self.compare
       tt = type
       from types import IntType
       result = assigns[:]
       for i in xrange(len(assigns)):
           assignsi = assigns[i]
           if tt(assignsi) is IntType: continue
           thisval = exprvals[i]
           testbtup = BoundTuple()
           testbtup.assns = kjDict(assignsi)
           if not cachable:
               subqr = subq.eval(outerboundtuple=testbtup).rows()
               cc = dump_single_column(subqr, att)
               #print self, "uncached", cc, thisval
           if not compare(thisval, cc):
               #print "eliminated", assignsi
               result[i] = 0
       return result
       
   def compare(self, value, column):
       return value in column
       
   def __hash__(self):
       return hash(self.subq) ^ ~hash(self.expr)
       
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       test = cmp(self.expr, other.expr)
       if test: return test
       return cmp(self.subq, other.subq)
       
# "expr IN (subq)" same as "expr = ANY (subq)"
InPredicate = QuantEQ

class InLits(NontrivialEqPred):
   """expr IN literals, support dynamic bindings."""   
   def __init__(self, expr, lits):
       self.expr = expr
       self.lits = lits
       self.cached_lits = None
       
   def initargs(self):
       return (self.expr, self.lits)
       
   def uncache(self):
       self.cached_lits = None
       
   def domain(self):
       d = []
       for l in self.lits:
           d0 = l.domain()
           if d0:
               d = d + d0.items()
       d0 = self.expr.domain()
       if d:
          kjSet = kjbuckets.kjSet
          return d0 + kjSet(d)
       else:
          return d0
       
   def relbind(self, dict, db):
       newlits = []
       for l in self.lits:
           newlits.append(l.relbind(dict, db))
       self.lits = newlits
       self.expr = self.expr.relbind(dict, db)
       return self
       
   fmt = "(%s IN %s)"
       
   def __repr__(self):
       return self.fmt % (self.expr, self.lits)
       
   def __call__(self, assigns, toplevel=0):
       # LITERALS ARE CONSTANT! NEED ONLY LOOK FOR ONE ASSIGN.
       tt = type
       from types import IntType
       litvals = self.cached_lits
       if litvals is None:
          assigns0 = []
          for asn in assigns:
              if tt(asn) is not IntType:
                 assigns0.append(asn)
                 break
          if not assigns0:
             # all false/unknown
             return assigns
          litvals = []
          for lit in self.lits:
              value = lit.value(assigns0)
              litvals.append(value[0])
          self.cached_lits = litvals
       expr = self.expr
       exprvals = expr.value(assigns)
       result = assigns[:]
       for i in xrange(len(assigns)):
           assignsi = assigns[i]
           if tt(assignsi) is IntType: continue
           thisval = exprvals[i]
           if thisval not in litvals:
               #print "eliminated", assignsi
               result[i] = 0
       return result
       
   def compare(self, value, column):
       return value in column
       
   def __hash__(self):
       return 10 ^ hash(self.expr)
       
   def __cmp__(self, other):
       test = cmp(self.__class__, other.__class__)
       if test: return test
       test = cmp(self.expr, other.expr)
       if test: return test
       return cmp(self.lits, other.lits)

class QuantNE(QuantEQ):
   """Quantified not equal any predicate"""
   op = "<>"
   def compare(self, value, column):
       for x in column:
           if value!=x: return 1
       return 0
       
### note: faster NOT IN using QuantNE?

class QuantLT(QuantEQ):
   """Quantified less than any predicate"""
   op = "<"
   def uncache(self):
       self.testval = self.cached = self.cached_column = None
   def compare(self, value, column):
       if self.cachable:
           if self.cached:
               testval = self.testval
           else:
               testval = self.testval = max(column)
               self.cached = 1
       else:
           testval = max(column)
       return value < testval

class QuantLE(QuantLT):
   """Quantified less equal any predicate"""
   op = "<="
   def compare(self, value, column):
       if self.cachable:
           if self.cached:
               testval = self.testval
           else:
               testval = self.testval = max(column)
               self.cached = 1
       else:
           testval = max(column)
       return value <= testval

class QuantGE(QuantLT):
   """Quantified greater equal any predicate"""
   op = ">="
   def compare(self, value, column):
       if self.cachable:
           if self.cached:
               testval = self.testval
           else:
               testval = self.testval = min(column)
               self.cached = 1
       else:
           testval = min(column)
       return value >= testval
       
class QuantGT(QuantLT):
   """Quantified greater than any predicate"""
   op = ">"
   def compare(self, value, column):
       if self.cachable:
           if self.cached:
               testval = self.testval
           else:
               self.testval = testval = min(column)
               self.cached = 1
       else:
           testval = min(column)
       return value > testval
       
def dump_single_column(assigns, att):
    """dump single column assignment"""
    result = assigns[:]
    for i in xrange(len(result)):
        result[i] = result[i][att]
    return result

class LessPred(NontrivialEqPred):
   op = "<"
   def __call__(self, assigns, toplevel=0):
       from types import IntType
       tt = type
       lv = self.left.value(assigns)
       rv = self.right.value(assigns)
       result = assigns[:]
       for i in xrange(len(assigns)):
           t = assigns[i]
           if tt(t) is not IntType and lv[i]>=rv[i]:
              result[i] = 0
       return result
       
   def __inv__(self):
       return LessEqPred(self.right, self.left)
       
   def __hash__(self):
       return hash(self.left)^hash(self.right)

       
class LessEqPred(LessPred):
   op = "<="
   def __call__(self, assigns, toplevel=0):
       from types import IntType
       tt = type
       lv = self.left.value(assigns)
       rv = self.right.value(assigns)
       result = assigns[:]
       for i in xrange(len(assigns)):
           t = assigns[i]
           if tt(t) is not IntType and lv[i]>rv[i]:
              result[i] = 0
       return result
       
   def __inv__(self):
       return LessPred(self.right, self.left)
       
class SubQueryExpression(BoundMinus, SimpleRecursive):
   """sub query expression (subq), must eval to single column, single value"""
   def __init__(self, subq):
       self.subq = subq
       self.att = self.cachable = self.cached = self.cached_value = None
       
   def initargs(self):
       return (self.subq,)
       
   def uncache(self):
       self.cached = self.cached_value = None

   def domain(self):
       result = self.subq.unbound()
       if not result:
           self.cachable = 1
       #print "expr subq domain", result
       return result
       
   def relbind(self, dict, db):
       subq = self.subq = self.subq.relbind(db, dict)
       # test that subquery is single column and determine att
       sl = subq.select_list
       atts = sl.attorder
       if len(atts)<>1:
          raise ValueError, \
            "Quantified predicate requires unit select list: %s" % atts
       self.att = atts[0]
       return self
       
   def __repr__(self):
       return "(%s)" % self.subq
       
   def value(self, contexts):
       subq = self.subq
       att = self.att
       if self.cachable:
           if self.cached:
               cached_value = self.cached_value
           else:
               self.cached = 1
               seval = subq.eval().rows()
               lse = len(seval)
               if lse<>1:
                   raise ValueError, \
          "const subquery expression must return 1 result: got %s" % lse
               self.cached_value = cached_value = seval[0][att]
           #print "const subq cached", cached_value
           return [cached_value] * len(contexts)
       from types import IntType
       tt = type
       result = contexts[:]
       kjDict = kjbuckets.kjDict
       for i in xrange(len(contexts)):
           contextsi = contexts[i]
           if tt(contextsi) is not IntType:
               testbtup = BoundTuple()
               testbtup.assns = kjDict(contextsi)
               #print "subq exp", testbtup
               seval = subq.eval(outerboundtuple=testbtup).rows()
               lse = len(seval)
               if lse<>1:
                   raise ValueError, \
          "dynamic subquery expression must return 1 result: got %s" % lse
               result[i] = seval[0][att]
               #print "nonconst subq uncached", result[i], contextsi
       return result

SELECT_TEMPLATE = """\
SELECT %s %s
FROM %s
WHERE %s
GROUP BY %s
HAVING %s %s
ORDER BY %s %s
"""

def dynamic_binding(ndynamic, dynamic):
    """create bindings from dynamic tuple for ndynamic parameters
       if a tuple is given create one
       if a list is given create many
    """
    from types import ListType, TupleType
    if not dynamic:
       if ndynamic>0:
             raise ValueError, `ndynamic`+" dynamic parameters unbound"
       return [kjbuckets.kjDict()]
    ldyn = len(dynamic)
    undumper = map(None, [0]*ndynamic, range(ndynamic))
    undumper = tuple(undumper)
    tdyn = type(dynamic)
    if tdyn is TupleType:
       ldyn = len(dynamic)
       if len(dynamic)!=ndynamic:
          raise ValueError, "%s,%s: wrong number of dynamics" % (ldyn,ndynamic)
       dynamic = [dynamic]
    elif tdyn is not ListType:
       raise TypeError, "dynamic parameters must be list or tuple"
    else:
       lens = map(len, dynamic)
       ndynamic = max(lens)
       if ndynamic!=min(lens):
          raise ValueError, "dynamic parameters of inconsistent lengths"
    undumper = map(None, [0]*ndynamic, range(ndynamic))
    undumper = tuple(undumper)
    result = list(dynamic)
    kjUndump = kjbuckets.kjUndump
    for i in xrange(len(dynamic)):
        dyn = dynamic[i]
        ldyn = len(dyn)
        #print undumper, dyn
        if ldyn==1:
           dynresult = kjUndump(undumper, dyn[0])
        else:
           dynresult = kjUndump(undumper, dyn)
        result[i] = dynresult
    return result

class Selector:
   """For implementing, eg the SQL SELECT statement."""
   def __init__(self, alldistinct,
                      select_list,
                      table_reference_list,
                      where_pred,
                      group_list,
                      having_cond,
                      union_select =None,
                      order_by_spec =None,
                      ndynamic=0, # number of dyn params expected
                      ):
       self.ndynamic = ndynamic
       self.alldistinct = alldistinct
       self.select_list = select_list
       self.table_list = table_reference_list
       self.where_pred = where_pred
       self.group_list = group_list
       self.having_cond = having_cond
       self.union_select = union_select
       self.order_by = order_by_spec
       #self.union_spec = "DISTINCT" # default union mode
       self.relbindings = None # binding of relations
       self.unbound_set = None # unbound attributes
       self.rel_atts = None # graph of alias-->attname bound in self
       self.all_aggregate = 0
       if select_list!="*" and not group_list:
          if select_list.contains_aggregate:
             ### should restore this check somewhere else!
             #if select_list.contains_nonaggregate:
                #raise ValueError, "aggregates/nonaggregates don't mix without grouping"
             self.all_aggregate = 1
       if where_pred and where_pred.contains_aggregate:
          raise ValueError, "aggregate in WHERE"
       self.query_plan = None
          
   def initargs(self):
       #print self.alldistinct
       #print self.select_list
       #print self.table_list
       #print self.where_pred
       #print self.having_cond
       #print self.union_select
       #print self.group_list
       #print self.order_by
       #print self.ndynamic
       # note: order by requires special handling
       return (self.alldistinct, self.select_list, self.table_list, self.where_pred,
               None, self.having_cond, self.union_select, None,
               self.ndynamic)
               
   def marshaldata(self):
       order_by = self.order_by
       if order_by:
           order_by = map(serialize, order_by)
       group_list = self.group_list
       if group_list:
           group_list = map(serialize, group_list)
       #print "marshaldata"
       #print order_by
       #print group_list
       return (order_by, group_list)
       
   def demarshal(self, data):
       (order_by, group_list) = data
       if order_by:
          order_by = map(deserialize, order_by)
       if group_list:
          group_list = map(deserialize, group_list)
       #print "demarshal"
       #print order_by
       #print group_list
       self.order_by = order_by
       self.group_list = group_list
          
   def unbound(self):
       result = self.unbound_set
       if result is None:
          raise ValueError, "binding not available"
       return result
       
   def uncache(self):
       wp = self.where_pred
       hc = self.having_cond
       sl = self.select_list
       if wp is not None: wp.uncache()
       if hc is not None: hc.uncache()
       sl.uncache()
       qp = self.query_plan
       if qp:
          for joiner in qp:
              joiner.uncache()
       
   def relbind(self, db, outerbindings=None):
       ad = self.alldistinct
       sl = self.select_list
       tl = self.table_list
       wp = self.where_pred
       gl = self.group_list
       hc = self.having_cond
       us = self.union_select
       ob = self.order_by
       test = db.bindings(tl)
       #print len(test)
       #for x in test: 
            #print x
       (attbindings, relbindings, ambiguous, ambiguousatts) = test
       if outerbindings:
          # bind in outerbindings where unambiguous
          for (a,r) in outerbindings.items():
              if ((not attbindings.has_key(a))
                  and (not ambiguousatts.has_key(a)) ):
                 attbindings[a] = r
       # fix "*" select list
       if sl=="*":
          sl = TupleCollector()
          for (a,r) in attbindings.items():
              sl.addbinding(None, BoundAttribute(r,a))
          for (dotted, (r,a)) in ambiguous.items():
              sl.addbinding(dotted, BoundAttribute(r,a))
       sl = sl.relbind(attbindings, db)
       wp = wp.relbind(attbindings, db)
       if hc is not None: hc = hc.relbind(attbindings, db)
       if us is not None: us = us.relbind(db, attbindings)
       # bind grouping if present
       if gl:
          gl = relbind_sequence(gl, attbindings, db)
       # bind ordering list if present
       #print ob
       if ob:
          ob = relbind_sequence(ob, attbindings, db)
          ob = orderbind_sequence(ob, sl.order)
       result = Selector(ad, sl, tl, wp, gl, hc, us, ob)
       result.relbindings = relbindings
       result.ndynamic = self.ndynamic
       result.check_domains()
       result.plan_query()
       query_plan = result.query_plan
       for i in range(len(query_plan)):
           query_plan[i] = query_plan[i].relbind(db, attbindings)
       return result
       
   def plan_query(self):
       """generate a query plan (sequence of join operators)."""
       rel_atts = self.rel_atts # rel-->attname
       where_pred = self.where_pred.detrivialize()
       #select_list = self.select_list
       # shortcut
       if where_pred is None:
          bt = BoundTuple()
       else:
          bt = self.where_pred.constraints
       if bt is None: 
          bt = BoundTuple()
       eqs = kjbuckets.kjGraph(bt.eqs)
       witness = kjbuckets.kjDict()
       # set all known and unbound atts as witnessed
       for att in bt.assns.keys():
           witness[att] = 1
       #print self, "self.unbound_set", self.unbound_set
       for att in self.unbound_set.items():
           witness[att] = 1
       relbindings = self.relbindings
       allrels = relbindings.keys()
       #print relbindings
       allrels = bt.relorder(relbindings, allrels)
       #print allrels
       rel_atts = self.rel_atts
       plan = []
       for rel in allrels:
           relation = relbindings[rel]
           ratts = rel_atts.neighbors(rel)
           h = HashJoiner(bt, rel, ratts, relation, witness)
           plan.append(h)
           for a in ratts:
               ra = (rel, a)
               witness[ra] = 1
               eqs[ra] = ra
           witness = witness.remap(eqs)
       self.query_plan = plan
       
   def check_domains(self):
       """determine set of unbound names in self.
       """
       relbindings = self.relbindings
       sl = self.select_list
       wp = self.where_pred
       gl = self.group_list
       hc = self.having_cond
       us = self.union_select
       all = sl.domain().items()
       if wp is not None:
          all = all + wp.domain().items()
       # ignore group_list ???
       if hc is not None:
          all = all + hc.domain().items()
       kjSet = kjbuckets.kjSet
       kjGraph = kjbuckets.kjGraph
       alldomain = kjSet(all)
       rel_atts = self.rel_atts = kjGraph(all)
       allnames = kjSet()
       #print "relbindings", relbindings.keys()
       for name in relbindings.keys():
           rel = relbindings[name]
           for att in rel.attributes():
               allnames[ (name, att) ] = 1
       # union compatibility check
       if us is not None:
          us.check_domains()
          myatts = self.attributes()
          thoseatts = us.attributes()
          if myatts!=thoseatts:
             if len(myatts)!=len(thoseatts):
                raise IndexError, "outer %s, inner %s: union select lists lengths differ"\
                  % (len(myatts), len(thoseatts))
          for p in map(None, myatts, thoseatts):
              (x,y)=p
              if x!=y:
                 raise NameError, "%s union names don't match" % (p,)
       self.unbound_set = alldomain - allnames
       
   def attributes(self):
       return self.select_list.attorder
       
   def eval(self, dynamic=None, outerboundtuple=None):
       """leaves a lot to be desired.
          dynamic and outerboundtuple are mutually
          exclusive.  dynamic is only pertinent to
          top levels, outerboundtuple to subqueries"""
       #print "select eval", dynamic, outerboundtuple
       from gfdb0 import Relation0
       # only uncache if outerboundtuple is None (not subquery)
       # ???
       if outerboundtuple is None:
           self.uncache()
       query_plan = self.query_plan
       where_pred = self.where_pred.detrivialize()
       select_list = self.select_list
       # shortcut
       if where_pred is not None and where_pred.false: 
          return Relation0(select_list.attorder, [])
       #print "where_pred", where_pred
       if where_pred is None or where_pred.constraints is None:
          assn0 = assn1 = kjbuckets.kjDict()
       else:
          assn1 = self.where_pred.constraints.assns
          assn0 = assn1 = kjbuckets.kjDict(assn1)
       # erase stored results from possible previous evaluation
       ndynamic = self.ndynamic
       if outerboundtuple is not None: 
          assn1 = assn1 + outerboundtuple.assns
       elif ndynamic:
          dyn = dynamic_binding(ndynamic, dynamic)
          if len(dyn)!=1:
             raise ValueError, "only one dynamic subst for selection allowed"
          dyn = dyn[0]
          assn1 = assn1 + dyn
          #print "dynamic", bt
       #print "assn1", assn1
       # check unbound names
       unbound_set = self.unbound_set
       #print "unbound", unbound_set
       #print unbound_set
       #print self.rel_atts
       for pair in unbound_set.items():
           if not assn1.has_key(pair):
              raise KeyError, `pair`+": unbound in selection"
       assn1 = (unbound_set * assn1) + assn0
       #print "assn1 now", assn1
       substseq = [assn1]
       for h in query_plan:
           #print "***"
           #for x in substseq:
               #print x
           #print "***"
           substseq = h.join(substseq)
           if not substseq: break
           #print "***"
           #for x in substseq:
               #print x
           #print "***"
       # apply the rest of the where predicate at top level
       if substseq and where_pred is not None:
          #where_pred.uncache()
          substseq = where_pred(substseq, 1)
       # eliminate zeros/nulls
       substseq = no_ints_nulls(substseq)
       # apply grouping if present
       group_list = self.group_list
       if substseq and group_list:
          substseq = aggregate(substseq, group_list)
          having_cond = self.having_cond
          #print having_cond
          if having_cond is not None:
             #having_cond.uncache()
             substseq = no_ints_nulls(having_cond(substseq))
       elif self.all_aggregate:
          # universal group
          substseq = [kjbuckets.kjDict( [(None, substseq)] ) ]
       (tups, attorder) = select_list.map(substseq)
       # do UNION if present
       union_select = self.union_select
       if union_select is not None:
          tups = union_select.eval(tups, dynamic, outerboundtuple)
       # apply DISTINCT if appropriate
       if self.alldistinct=="DISTINCT":
          tups = kjbuckets.kjSet(tups).items()
       # apply ordering if present
       ob = self.order_by
       if ob:
          tups = order_tuples(ob, tups)
       return Relation0(attorder, tups)
       
   def __repr__(self):
       ndyn = ""
       if self.ndynamic:
          ndyn = "\n[%s dynamic parameters]" % self.ndynamic
       result = SELECT_TEMPLATE % (
         self.alldistinct,
         self.select_list,
         self.table_list,
         self.where_pred,
         self.group_list,
         self.having_cond,
         #union_spec,
         self.union_select,
         self.order_by,
         ndyn
         )
       return result   
       
class Union(SimpleRecursive):
   """union clause."""

   def __init__(self, alldistinct, selection):
       self.alldistinct = alldistinct
       self.selection = selection
       
   def initargs(self):
       return (self.alldistinct, self.selection)
       
   def unbound(self):
       return self.selection.unbound()
       
   def relbind(self, db, outer=None):
       self.selection = self.selection.relbind(db, outer)
       return self
       
   def check_domains(self):
       self.selection.check_domains()
       
   def attributes(self):
       return self.selection.attributes()
       
   def eval(self, assns, dyn=None, outer=None):
       r = self.selection.eval(dyn, outer)
       rows = r.rows()
       allrows = rows + assns
       if self.alldistinct=="DISTINCT":
          allrows = kjbuckets.kjSet(allrows).items()
       return allrows
       
   def __repr__(self):
       return "\nUNION %s %s " % (self.alldistinct, self.selection)
       
class Intersect(Union):
   def eval(self, assns, dyn=None, outer=None):
       r = self.selection.eval(dyn, outer)
       rows = r.rows()
       kjSet = kjbuckets.kjSet
       allrows = (kjSet(assns) & kjSet(rows)).items()
       return allrows
   op = "INTERSECT"
   def __repr__(self):
       return "\n%s %s" % (self.op, self.selection)
       
class Except(Union):
   def eval(self, assns, dyn=None, outer=None):
       r = self.selection.eval(dyn, outer)
       rows = r.rows()
       kjSet = kjbuckets.kjSet
       allrows = (kjSet(assns) - kjSet(rows)).items()
       return allrows
   op = "EXCEPT"
       
              
class Parse_Context:
   """contextual information for parsing
        p.param() returns a new sequence number for external parameter.
   """
   # not serializable
   
   parameter_index = 0
   
   # no __init__ yet
   def param(self):
       temp = self.parameter_index
       self.parameter_index = temp+1
       return temp
       
   def ndynamic(self):
       return self.parameter_index
# update/delete/insert statements
import sqlmod
CreateTable = sqlmod.CreateTable
CreateIndex = sqlmod.CreateIndex
DropIndex = sqlmod.DropIndex
DropTable = sqlmod.DropTable
UpdateOp = sqlmod.UpdateOp
DeleteOp = sqlmod.DeleteOp
InsertOp = sqlmod.InsertOp
InsertValues = sqlmod.InsertValues
InsertSubSelect = sqlmod.InsertSubSelect
ColumnDef = sqlmod.ColumnDef
CreateView = sqlmod.CreateView
DropView = sqlmod.DropView

# update storage structures from gfdb0
import gfdb0
Add_Tuples = gfdb0.Add_Tuples
Erase_Tuples = gfdb0.Erase_Tuples
Reset_Tuples = gfdb0.Reset_Tuples
       
####### testing
# test helpers
#def tp(**kw):
#    return maketuple(kw)
    
#def st(**kw):
#    return BTPredicate(BoundTuple(r=kw))
    
