
# kjbuckets in pure python

### needs more thorough testing!

#import sys # for debug

def kjtabletest(x):
    #print "kjtabletest"
    try:
        return x.is_kjtable
    except:
        return 0
        
unhashable = "unhashable key error"

class kjGraph:

   is_kjtable = 1

   def __init__(self, *args):
       #print "kjGraph.__init__", args
       key_to_list = self.key_to_list = {}
       self.dirty = 0
       self.hashed = None
       #print args
       if args:
          if len(args)>1:
             raise ValueError, "only 1 or 0 argument supported"
          from types import IntType, ListType, TupleType
          arg = args[0]
          targ = type(arg)
          test = key_to_list.has_key
          if type(arg) is IntType:
             return # ignore int initializer (presize not implemented)
          elif type(arg) is ListType or type(arg) is TupleType:
             for (x,y) in arg:
                 if test(x):
                    key_to_list[x].append(y)
                 else:
                    key_to_list[x] = [y]
             return
          aclass = arg.__class__
          if aclass is kjGraph:
             aktl = arg.key_to_list
             for k in aktl.keys():
                 key_to_list[k] = aktl[k][:]
             return
          if aclass is kjDict or aclass is kjSet:
             adict = arg.dict
             for k in adict.keys():
                 key_to_list[k] = [ adict[k] ]
             return
          raise ValueError, "arg for kjGraph must be tuple, list, or kjTable"

   def __repr__(self):
       return "%s(%s)" % (self.__class__.__name__, self.items())

   def _setitems(self, thing):
       #print "kjGraph._setitem", thing
       #print "setitems", thing
       if self.hashed is not None: 
          raise ValueError, "table has been hashed, it is immutable"
       try:
           for (k,v) in thing:
               #print k,v, "going"
               #inlined __setitem__
               try:
                   klist = self.key_to_list[k]
                   #print "klist gotten"
               except KeyError:
                   try:
                       klist = self.key_to_list[k] = []
                   except TypeError:
                       raise unhashable
               if v not in klist:
                   klist.append(v)
       except (TypeError, KeyError):
          #print sys.exc_type, sys.exc_value
          if kjtabletest(thing):
             self._setitems(thing._pairs())
             self.dirty = thing.dirty
          else: raise ValueError, "cannot setitems with %s" % type(thing)
       except unhashable:
          raise TypeError, "unhashable type"

   def __setitem__(self, item, value):
       ktl = self.key_to_list
       if ktl.has_key(item):
          l = ktl[item]
          if value not in l:
             l.append(value)
       else:
          ktl[item] = [value]

   def __getitem__(self, item):
       return self.key_to_list[item][0]

   def __delitem__(self, item):
       self.dirty = 1
       del self.key_to_list[item]

   def choose_key(self):
       return self.key_to_list.keys()[0]

   def _pairs(self, justtot=0):
       myitems = self.key_to_list.items()
       tot = 0
       for (k, v) in myitems:
           tot = tot + len(v)
       if justtot: return tot
       else:
          result = [None]*tot
          i = 0
          for (k,v) in myitems:
              for x in v:
                  result[i] = (k,x)
                  i = i+1
       return result

   def __len__(self):
       v = self.key_to_list.values()
       lv = map(len, v)
       from operator import add
       return reduce(add, lv, 0)

   def items(self):
       return self._pairs()

   def values(self):
       v = self.key_to_list.values()
       from operator import add
       tot = reduce(add, map(len, v), 0)
       result = [None] * tot
       count = 0
       for l in v:
           next = count + len(l)
           result[count:next] = l
           count = next
       return result

   def keys(self):
       return self.key_to_list.keys()

   def member(self, k, v):
       ktl = self.key_to_list
       if ktl.has_key(k):
          return v in ktl[k]
       return 0

   _member = member # because member redefined for kjSet

   def add(self, k, v):
       ktl = self.key_to_list
       if ktl.has_key(k):
          l = ktl[k]
          if v not in l:
             l.append(v)
       else:
          ktl[k] = [v]

   def delete_arc(self, k, v):
       self.dirty = 1
       if self.hashed is not None: 
          raise ValueError, "table has been hashed, it is  immutable"
       try:
           l = self.key_to_list[k]
           i = l.index(v)
           del l[i]
           if not l:
              del self.key_to_list[k]
       except:
           raise KeyError, "not in table"# % (k,v)

   def has_key(self, k):
       return self.key_to_list.has_key(k)

   def subset(self, other):
       oc = other.__class__
       if oc is kjGraph:
          oktl = other.key_to_list
          sktl = self.key_to_list
          otest = oktl.has_key
          for k in sktl.keys():
              if otest(k):
                 l = sktl[k]
                 ol = oktl[k]
                 for x in l:
                     if x not in ol:
                        return 0
              else:
                 return 0
          return 1
       elif oc is kjSet or oc is kjDict:
          sktl = self.key_to_list
          odict = other.dict
          otest = odict.has_key
          for k in sktl.keys():
              if otest(k):
                 l = sktl[k]
                 ov = odict[k]
                 for x in l:
                     if ov!=x: return 0
              else:
                 return 0
          return 1

   def neighbors(self, k):
       try:
           return self.key_to_list[k][:]
       except:
           return []

   def reachable(self, k):
       try:
           horizon = self.key_to_list[k]
       except:
           return kjSet()
       else:
           if not horizon: return []
           d = {}
           for x in horizon: d[x] = 1
           done = 0
           while horizon:
              newhorizon = []
              for n in horizon:
                  for n2 in self.neighbors(n):
                      if not d.has_key(n2):
                         newhorizon.append(n2)
                         d[n2] = 1
              horizon = newhorizon
           return kjSet(d.keys())

   def items(self):
       return self._pairs()


   # ????
   def ident(self):
       result = kjDict(self)
       result.dirty = self.dirty or result.dirty
       return result

   def tclosure(self):
       # quick and dirty
       try:
           raise self
       except (kjSet, kjDict):
           raise ValueError, "tclosure only defined on graphs"
       except kjGraph:
           pass
       except:
           raise ValueError, "tclosure only defined on graphs"
       result = kjGraph(self)
       result.dirty = self.dirty
       addit = result.add
       while 1:
          #print result
          more = result*result
          if more.subset(result):
             return result
          for (x,y) in more.items():
              addit(x,y)

   def Clean(self):
       if self.dirty: return None
       return self

   def Wash(self):
       self.dirty = 0

   def Soil(self):
       self.dirty = 1

   def remap(self, X):
       # really only should be defined for kjdict, but whatever
       return kjDict(X*self).Clean()

   def dump(self, seq):
       result = map(None, seq)
       for i in range(len(result)):
           result[i] = self[result[i]]
       if len(seq) == 1:
          return result[0]
       return tuple(result)

   def __hash__(self): # should test better
       """in conformance with kjbuckets, permit unhashable keys"""
       if self.hashed is not None:
          return self.hashed
       items = self._pairs()
       for i in xrange(len(items)):
           (a,b) = items[i]
           try:
              b = hash(b)
           except:
              b = 1877777
           items[i] = hash(a)^~b
       items.sort()
       result = self.hashed = hash(tuple(items))
       return result

   def __cmp__(self, other):
       #print "kjGraph.__cmp__"
       ls = len(self)
       lo = len(other)
       test = cmp(ls, lo)
       if test:
          return test
       si = self._pairs()
       oi = other._pairs()
       si.sort()
       oi.sort()
       return cmp(si, oi)
       
   def __nonzero__(self):
       if self.key_to_list: return 1
       return 0

   def __add__(self, other):
       result = kjGraph(self)
       rktl = result.key_to_list
       rtest = rktl.has_key
       result.dirty = self.dirty or other.dirty
       oc = other.__class__
       if oc is kjGraph:
          oktl = other.key_to_list
          for k in oktl.keys():
              l = oktl[k]
              if rtest(k):
                 rl = rktl[k]
                 for x in l:
                     if x not in rl:
                        rl.append(x)
              else:
                 rktl[k] = l[:]
       elif oc is kjSet or oc is kjDict:
          odict = other.dict
          for k in odict.keys():
              ov = odict[k]
              if rtest(k):
                 rl = rktl[k]
                 if ov not in rl:
                    rl.append(ov)
              else:
                 rktl[k] = [ov]
       else:
          raise ValueError, "kjGraph adds only with kjTable"
       return result

   __or__ = __add__

   def __sub__(self, other):
       result = kjGraph()
       rktl = result.key_to_list
       sktl = self.key_to_list
       oc = other.__class__
       if oc is kjGraph:
          oktl = other.key_to_list
          otest = oktl.has_key
          for k in sktl.keys():
              l = sktl[k][:]
              if otest(k):
                 ol = oktl[k]
                 for x in ol:
                     if x in l:
                        l.remove(x)
                 if l: 
                    rktl[k] = l
              else:
                 rktl[k] = l
       elif oc is kjSet or oc is kjDict:
           odict = other.dict
           otest = odict.has_key
           for k in sktl.keys():
               l = sktl[k][:]
               if otest(k):
                  ov = odict[k]
                  if ov in l:
                     l.remove(ov)
               if l:
                  rktl[k] = l
       else:
          raise ValueError, "kjGraph diffs only with kjTable"
       return result

   def __mul__(self, other):
       result = kjGraph()
       rktl = result.key_to_list
       sktl = self.key_to_list
       oc = other.__class__
       if oc is kjGraph:
          oktl = other.key_to_list
          otest = other.has_key
          for sk in sktl.keys():
              sklist = []
              for sv in sktl[sk]:
                  if otest(sv):
                     sklist[0:0] = oktl[sv]
              if sklist:
                 rktl[sk] = sklist
       elif oc is kjSet or oc is kjDict:
          odict = other.dict
          otest = odict.has_key
          for sk in sktl.keys():
              sklist=[]
              for sv in sktl[sk]:
                  if otest(sv):
                     sklist.append(odict[sv])
              if sklist:
                 rktl[sk] = sklist
       else:
          raise ValueError, "kjGraph composes only with kjTable"
       return result

   def __invert__(self):
       result = self.__class__()
       pairs = self._pairs()
       for i in xrange(len(pairs)):
           (k,v) = pairs[i]
           pairs[i] = (v,k)
       result._setitems(pairs)
       result.dirty = self.dirty or result.dirty
       return result

   def __and__(self, other):
       sktl = self.key_to_list
       oc = other.__class__
       if oc is kjGraph:
          result = kjGraph()
          rktl = result.key_to_list
          oktl = other.key_to_list
          otest = oktl.has_key
          for k in self.keys():
              if otest(k):
                 l = sktl[k]
                 ol = oktl[k]
                 rl = []
                 for x in l:
                     if x in ol:
                        rl.append(x)
                 if rl:
                    rktl[k] = rl
       elif oc is kjSet or oc is kjDict:
          result = oc() # less general!
          rdict = result.dict
          odict = other.dict
          stest = sktl.has_key
          for k in odict.keys():
              if stest(k):
                 v = odict[k]
                 l = sktl[k]
                 if v in l:
                    rdict[k] = v
       else:
          raise ValueError, "kjGraph intersects only with kjTable"
       result.dirty = self.dirty or other.dirty
       return result

   def __coerce__(self, other):
       return (self, other) # ?is this sufficient?

class kjDict(kjGraph):

   def __init__(self, *args):
       #print "kjDict.__init__", args
       self.hashed = None
       dict = self.dict = {}
       self.dirty = 0
       if not args: return
       if len(args)==1:
          from types import TupleType, ListType, IntType
          arg0 = args[0]
          targ0 = type(arg0)
          if targ0 is IntType: return
          if targ0 is ListType or targ0 is TupleType:
             otest = dict.has_key
             for (a,b) in arg0:
                 if otest(a):
                    if dict[a]!=b:
                       self.dirty = 1
                 dict[a] = b
             return
          argc = arg0.__class__
          if argc is kjGraph:
             ktl = arg0.key_to_list
             for k in ktl.keys():
                 l = ktl[k]
                 if len(l)>1: self.dirty=1
                 for v in l:
                     dict[k] = v
             return
          if argc is kjSet or argc is kjDict:
             adict = arg0.dict
             for (k,v) in adict.items():
                 dict[k]=v
             return
       raise ValueError, "kjDict initializes only from list, tuple, kjTable, or int"

   def _setitems(self, thing):
       #print "kjDict._setitem", thing
       if self.hashed is not None: 
          raise KeyError, "table hashed, cannot modify"
       dict = self.dict
       try:
          for (k,v) in thing:
              if dict.has_key(k) and dict[k]!=v:
                 self.dirty = 1
              dict[k] = v
       except:
          self._setitems(thing._pairs()) # maybe too tricky!
          
   def dump(self, dumper):
       ld = len(dumper)
       if ld==1:
          return self.dict[dumper[0]]
       else:
          sdict = self.dict
          result = [None] * ld
          for i in xrange(ld):
              result[i] = sdict[ dumper[i] ]
          return tuple(result)
          
   def __setitem__(self, item, value):
       if self.hashed is not None:
          raise ValueError, "table has been hashed, it is immutable"
       d = self.dict
       if d.has_key(item):
          if d[item]!=value:
             self.dirty = 1
       self.dict[item]=value

   def __getitem__(self, item):
       return self.dict[item]

   def __delitem__(self, item):
       if self.hashed is not None:
          raise ValueError, "table has been hashed, it is immutable"
       self.dirty = 1
       del self.dict[item]

   def choose_key(self):
       return self.dict.keys()[0]
       
   def __len__(self):
       return len(self.dict)	

   def _pairs(self, justtot=0):
       if justtot: return len(self.dict)
       return self.dict.items()

   def values(self):
       return self.dict.values()

   def keys(self):
       return self.dict.keys()
       
   def items(self):
       return self.dict.items()
       
   def remap(self, X):
       if X.__class__ is kjGraph:
          if self.dirty or X.dirty: return None
          result = kjDict()
          resultd = result.dict
          selfd = self.dict
          inself = selfd.has_key
          inresult = resultd.has_key
          ktl = X.key_to_list
          for k in ktl.keys():
              for v in ktl[k]:
                  if inself(v):
                     map = selfd[v]
                     if inresult(k):
                        if resultd[k]!=map:
                           return None
                     else:
                        resultd[k]=map
          return result
       else:
          return (kjDict(X*self)).Clean()
          
   def __cmp__(s,o):
       from types import InstanceType
       if type(o) is not InstanceType:
          return -1
       oc = o.__class__
       if oc is kjDict or oc is kjSet:
          return cmp(s.dict, o.dict)
       return kjGraph.__cmp__(s, o)
       
   def __hash__(s):
       h = s.hashed
       if h is not None: return h
       return kjGraph.__hash__(s)
       
   def __add__(s,o):
       oc = o.__class__
       if oc is kjDict or oc is kjSet:
          result = kjDict()
          result.dirty = s.dirty or o.dirty
          rdict = result.dict
          rtest = result.has_key
          sdict = s.dict
          for k in sdict.keys():
              rdict[k] = sdict[k]
          odict = o.dict
          for k in odict.keys():
              if rtest(k):
                 if rdict[k]!=odict[k]:
                    result.dirty=1
              else:
                 rdict[k] = odict[k]
          return result
       if oc is kjGraph:
          return kjGraph.__add__(o,s)
       else:
          raise ValueError, "kjDict unions only with kjTable"
       
   __or__ = __add__
       
   def __and__(s,o):
       oc = o.__class__
       if oc is kjDict or oc is kjSet:
          result = oc()
          result.dirty = s.dirty or o.dirty
          rdict = result.dict
          odict = o.dict
          sdict = s.dict
          stest = sdict.has_key
          for k in odict.keys():
              v = odict[k]
              if stest(k) and sdict[k]==v:
                 rdict[k] = v
          return result
       elif oc is kjGraph:
          return kjGraph.__and__(o,s)
          

   def __sub__(s,o):
       oc = o.__class__
       result = kjDict()
       result.dirty = s.dirty or o.dirty
       sdict = s.dict
       rdict = result.dict
       if oc is kjDict:
          odict = o.dict
          otest = odict.has_key
          for k in sdict.keys():
              v = sdict[k]
              if otest(k):
                 if odict[k]!=v:
                    rdict[k] = v
              else:
                 rdict[k] = v
          return result
       if oc is kjGraph:
          oktl = o.key_to_list
          otest = oktl.has_key
          for k in sdict.keys():
              v = sdict[k]
              if otest(k):
                 if v not in oktl[k]:
                    rdict[k] = v
              else:
                 rdict[k] = v
          return result
       raise ValueError, "kjDict only diffs with kjGraph, kjDict"
          
   def __mul__(s,o):
       oc = o.__class__
       sdict = s.dict
       if oc is kjDict or oc is kjSet:
          result = kjDict()
          result.dirty = s.dirty or o.dirty
          rdict = result.dict
          odict = o.dict
          otest = odict.has_key
          for k in sdict.keys():
              kv = sdict[k]
              if otest(kv):
                 rdict[k] = odict[kv]
          return result
       elif oc is kjGraph:
          return kjGraph(s) * o
       else:
          raise ValueError, "kjDict only composes with kjTable"

   def member(self, k, v):
       d = self.dict
       try:
           return d[k] == v
       except:
           return 0

   _member = member

   def delete_arc(self, k, v):
       if self.dict[k] == v:
          del self.dict[k]
       else:
          raise KeyError, "pair not in table"

   def has_key(self, k):
       return self.dict.has_key(k)

   def neighbors(self, k):
       try:
          return [ self.dict[k] ]
       except: return []

   def reachable(self, k):
       result = {}
       d = self.dict
       try:
           while 1:
              next = d[k]
              if result.has_key(next): break
              result[next] = 1
              k = next
       except KeyError:
           pass
       return kjSet(result.keys())
       
   def __invert__(self):
       result = kjDict()
       dr = result.dict
       drtest = dr.has_key
       ds = self.dict
       for (a,b) in ds.items():
           if drtest(b):
              result.dirty=1
           dr[b]=a
       result.dirty = self.dirty or result.dirty
       return result
       
   def __nonzero__(self):
       if self.dict: return 1
       return 0
       
   def subset(s, o):
       oc = o.__class__
       sdict = s.dict
       if oc is kjDict or oc is kjSet:
          odict = o.dict
          otest = odict.has_key
          for k in sdict.keys():
              v = sdict[k]
              if otest(k):
                 if odict[k]!=v:
                    return 0
              else:
                 return 0
       elif oc is kjGraph:
          oktl = o.key_to_list
          otest = oktl.has_key
          for k in sdict.keys():
              v = sdict[k]
              if otest(k):
                 if v not in oktl[k]:
                    return 0
              else:
                 return 0
       else:
          raise ValueError, "kjDict subset test only for kjTable"
       return 1
       
   def add(s, k, v):
       if s.hashed is not None:
          raise ValueError, "table has been hashed, immutable"
       sdict = s.dict
       if sdict.has_key(k):
          if sdict[k]!=v:
             s.dirty = 1
       sdict[k] = v

class kjSet(kjDict):

   def __init__(self, *args):
       #print "kjSet.__init__", args
       # usual cases first
       dict = self.dict = {}
       self.hashed = None
       self.dirty = 0
       largs = len(args)
       if largs<1: return
       if largs>1:
          raise ValueError, "at most one argument supported"
       from types import IntType, TupleType, ListType
       arg0 = args[0]
       targ0 = type(arg0)
       if targ0 is IntType: return
       if targ0 is TupleType or targ0 is ListType:
          for x in arg0:
              dict[x] = x
          return
       argc = arg0.__class__
       if argc is kjDict or argc is kjSet:
          stuff = arg0.dict.keys()
       elif argc is kjGraph:
          stuff = arg0.key_to_list.keys()
       else:
          raise ValueError, "kjSet from kjTable, int, list, tuple only"
       for x in stuff:
          dict[x] = x
           
   def __add__(s,o):
       oc = o.__class__
       if oc is kjSet:
          result = kjSet()
          result.dirty = s.dirty or o.dirty
          rdict = result.dict
          for x in s.dict.keys():
              rdict[x]=x
          for x in o.dict.keys():
              rdict[x]=x
          return result
       elif oc is kjDict:
          return kjDict.__add__(o,s)
       elif oc is kjGraph:
          return kjGraph.__add__(o,s)
          
   __or__ = __add__
   
   def __sub__(s,o):
       if o.__class__ is kjSet:
          result = kjSet()
          result.dirty = s.dirty or o.dirty
          rdict = result.dict
          otest = o.dict.has_key
          for x in s.dict.keys():
              if not otest(x):
                 rdict[x] = x
          return result
       else:
          return kjDict.__sub__(s,o)
          
   def __and__(s,o):
       oc = o.__class__
       if oc is kjSet or oc is kjDict:
          result = kjSet()
          result.dirty = s.dirty or o.dirty
          rdict = result.dict
          odict = o.dict
          otest = odict.has_key
          for x in s.dict.keys():
              if otest(x) and odict[x]==x:
                 rdict[x] = x
          return result
       elif oc is kjGraph:
          return kjGraph.__and__(o,s)
       raise ValueError, "kjSet only intersects with kjTable"

   # illegal methods
   values = keys = remap = None

   def __repr__(self):
       return "kjSet(%s)" % self.items()
             
   def _setelts(self, items):
       #print "kjSet.setelts", items
       try:
           items = items._pairs()
       except:
           items = list(items)
           for i in xrange(len(items)):
               items[i] = (items[i], items[i])
           self._setitems(items)
       else:
           items = list(items)
           for i in xrange(len(items)):
               items[i] = (items[i][0], items[i][0])
       self._setitems(items)
       # hack!
       #D = self.dict
       #for x in D.keys():
       #    D[x] = x

   def _pairs(self, justtot=0):
       if justtot: return kjDict._pairs(self, justtot=1)
       pairs = kjDict.keys(self)
       for i in xrange(len(pairs)):
           pairs[i] = (pairs[i], pairs[i])
       return pairs

   member = kjDict.has_key

   items = kjDict.keys

   #def neighbors(self, x):
   #    raise ValueError, "operation on kjSet undefined"

   #reachable = neighbors

   def __getitem__(self, item):
       test = self.dict.has_key(item)
       if test: return 1
       raise KeyError, "item not in set"
       
   def __setitem__(self, item, ignore):
       d = self.dict
       if self.hashed:
          raise ValueError, "table hashed, immutable"
       d[item] = item
       
   def add(self, elt):
       if self.hashed:
          raise ValueError, "table hashed, immutable"
       self.dict[elt] = elt
       
   def __mul__(s,o):
       oc = o.__class__
       if oc is kjSet:
          return s.__and__(o)
       else:
          return kjDict.__mul__(s, o)

def more_general(t1, t2):
    try:
        raise t1
    except kjSet:
        try:
           raise t2
        except (kjGraph, kjDict, kjSet):
           return t2.__class__
    except kjDict:
        try:
           raise t2
        except kjSet:
           return t1.__class__
        except (kjDict, kjGraph):
           return t2.__class__
    except kjGraph:
        return t1.__class__
    except:
        raise ValueError, "cannot coerce, not kjtable"

def less_general(t1,t2):
    try: 
        raise t1
    except kjSet:
        return t1.__class__
    except kjDict:
        try:
           raise t2
        except kjSet:
           return t2.__class__
        except (kjDict, kjGraph):
           return t1.__class__
    except kjGraph:
        return t2.__class__
    except:
        raise ValueError, "cannot coerce, not kjtable"

def kjUndump(t1, t2):
    result = kjDict()
    rdict = result.dict
    lt1 = len(t1)
    if lt1 == 1:
       rdict[t1[0]] = t2
    else:
       # tightly bound to implementation
       for i in xrange(lt1):
           rdict[t1[i]] = t2[i]
    return result
    

def test():
    global S, D, G
    G = kjGraph()
    r3 = range(3)
    r = map(None, r3, r3)
    for i in range(3):
        G[i] = i+1
    D = kjDict(G)
    D[9]=0
    G[0]=10
    S = kjSet(G)
    S[-1] = 5
    print "%s.remap(%s) = %s" % (D, G, D.remap(G))
    print "init test"
    for X in (S, D, G, r, tuple(r), 1):
        print "ARG", X
        for C in (kjGraph, kjSet, kjDict):
            print "AS", C
            T = C(X)
            T2 = C()
            print X, T, T2
    ALL = (S, D, G)
    for X in ALL:
        print "X=", X
        print "key", X.choose_key()
        print "len", len(X)
        print "items", X.items()
        print X, "Clean before", X.Clean()
        del X[2]
        print X, "Clean after", X.Clean()
        if not X.subset(X):
           raise "trivial subset fails", X
        if not X==X:
           raise "trivial cmp fails", X
        if not X:
           raise "nonzero fails", X
        if X is S:
           if not S.member(0):
              raise "huh 1?"
           if S.member(123):
              raise "huh 2?", S
           S.add(999)
           del S[1]
           if not S.has_key(999):
              raise "huh 3?", S
        else:
           print "values", X.values()
           print "keys", X.keys()
           print X, "inverted", ~X
           if not X.member(0,1):
              raise "member test fails (0,1)", X
           print "adding to", X
           X.add(999,888)
           print "added", X
           X.delete_arc(999,888)
           print "deleted", X
           if X.member(999,888):
              raise "member test fails (999,888)", X
           if X.has_key(999):
              raise "has_key fails 999", X
           if not X.has_key(0):
              raise "has_key fails 0", X
        for Y in ALL:
            print "Y", Y
            if (X!=S and Y!=S):
               print "diff", X, Y
               print "%s-%s=%s" % (X,Y,X-Y)
            elif X==S:
               D = kjSet(Y)
               print "diff", X, D
               print "%s-%s=%s" % (X,D,X-D)
            print "%s+%s=%s" % (X,Y,X+Y)
            print "%s&%s=%s" % (X,Y,X&Y)
            print "%s*%s=%s" % (X,Y,X*Y)
            x,y = cmp(X,Y), cmp(Y,X)
            if x!=-y: raise "bad cmp!", (X, Y)
            print "cmp(X,Y), -cmp(Y,X)", x,-y
            print "X.subset(Y)", X.subset(Y)
            


           
    