
"""Simple relational algebra interpreter.

usage:

   To make the grammar

       python relalg.py make

   To run some relatoinal algebra expressions

       python relalg.py < expressions_file

"""

# EDIT INSTALLDIR TO BE ABLE TO LOAD UNDER ANY CWD
INSTALLDIR = "."

## simple relational algebra using only the equality predicate
## note: string values cannot contain ;

## statement sequencing using ; handled at higher level

relalg_rules = """

statement ::

@R statementassn :: statement >> assignment

@R statementexpr :: statement >> rexpr

@R assignment1 :: assignment >> name = rexpr

@R assignmentn :: assignment >> name = assignment

@R union :: rexpr >> rexpr U rterm

@R rterm :: rexpr >> rterm

@R minus :: rexpr >> rexpr - rterm

@R intersect :: rterm >> rterm intersect rfactor

@R join :: rterm >> rterm join rfactor

@R rfactor :: rterm >> rfactor

@R projection :: rfactor >> projection [ names ] rfactor

@R names0 :: names >>

@R namesn :: names >> names1

@R names11 :: names1 >> name

@R names1n :: names1 >> names1 name

@R selection :: rfactor >> selection ( condition ) rfactor

@R conditionor :: condition >> condition | boolfactor

@R condfactor :: condition >> boolfactor

@R factorand :: boolfactor >> boolfactor & boolprimary

@R factorprime :: boolfactor >> boolprimary

@R notprimary :: boolprimary >> ~ boolprimary

@R primarycondition :: boolprimary >> ( condition )

@R primaryeq :: boolprimary >> expression = expression

@R expname :: expression >> name

@R expvalue :: expression >> value

@R rename :: rfactor >> rename [ names ] to [ names ] rfactor

@R named :: rfactor >> name

@R factorexpr :: rfactor >> ( rexpr )

@R relationval :: rfactor >> [ names ] ( rows )

@R rows0 :: rows >>

@R rowsn :: rows >> somerows

@R somerows1 :: somerows >> row

@R somerowsn :: somerows >> somerows , row

@R emptyrow :: row >> NIL

@R row1 :: row >> value

@R rown :: row >> row value

@R valuenum :: value >> number

@R valuestr :: value >> string
"""

keywords = """
  selection intersect rename projection to NIL U join
"""

puncts = """=^~|,-[]()&"""

nonterms = """
statement assignment rexpr rterm value rfactor
names names1 condition boolfactor boolprimary
expression rows somerows row
"""

try:
    from kjbuckets import *
except ImportError:
    from kjbuckets0 import *


class relation:

   def __init__(self, names, rows):
       #print "relation init", names, rows
       names = self.names = tuple(names)
       nameset = self.nameset = kjSet(names)
       for r in rows:
           if nameset != kjSet(r.keys()):
               raise ValueError, \
                "bad names: "+`(names, r.items())`
       self.rows = kjSet(rows)

   def __repr__(self):
       from string import join
       names = self.names
       rows = self.rows.items()
       if not rows:
          nns = join(names)
          replist = [nns, "="*len(nns), " --<empty>--"]
          return join(replist, "\n")
       #print names, rows
       nnames = len(names)
       if nnames==1:
           replist = [names[0]]
       else:
           replist = [names]
       for r in rows:
           elt = r.dump(names)
           replist.append(r.dump(names))
       #print replist
       if nnames==1:
           replist = maxrep(replist)
       else:
           transpose = apply(map, tuple([None] + replist))
           adjusted = map(maxrep, transpose)
           replist = apply(map, tuple([None] + adjusted))
           replist = map(join, replist)
       replist.insert(1, "=" * len(replist[0]))
       #print replist
       return join(replist, "\n")
       
def maxrep(list):
    list = map(str, list)
    maxlen = max( map(len, list) )
    for i in range(len(list)):
        item = list[i]
        litem = len(item)
        list[i] = item + (" " * (maxlen-litem))
    return list

# context is a simple dictionary of named relations

def elt0(l, c):
    return l[0]

statementassn = elt0

def statementexpr(l, c):
    from string import split, join
    print
    print "  --- expression result ---"
    print
    data = str(l[0])
    print "   "+ join(split(data, "\n"), "\n   ")

def assignment1(l, c):
    [name, eq, val] = l
    c[name] = val
    return val

assignmentn = assignment1

def check_compat(v1, v2):
    names1, names2 = v1.names, v2.names
    if names1 != names2:
        raise ValueError, \
        "operands not union compatible "+`(names1, names2)`
    return names1, v1.rows, v2.rows

def union(l, c):
    [v1, U, v2] = l
    names1, r1, r2 = check_compat(v1, v2)
    return relation(names1, (r1+r2).items())

rterm = elt0

def minus(l, c):
    [v1, m, v2] = l
    names1, r1, r2 = check_compat(v1, v2)
    return relation(names1, (r1-r2).items())

def intersect(l, c):
    [v1, i, v2] = l
    names1, r1, r2 = check_compat(v1, v2)
    return relation(names1, (r1&r2).items())

def join(l, c):
    [v1, j, v2] = l
    n1, n2 = v1.names, v2.names
    r1, r2 = v1.rows.items(), v2.rows.items()
    n1s, n2s = kjSet(n1), kjSet(n2)
    common = tuple((n1s&n2s).items())
    result = kjSet()
    if common:
        # simple hashjoin
        G = kjGraph()
        for a in r1:
            G[a.dump(common)] = a
        for b in r2:
            for a in G.neighbors(b.dump(common)):
                result[a+b] = 1
    else:
        for a in r1:
            for b in r2:
                result[a+b] = 1
    return relation( (n1s+n2s).items(), result.items() )

rfactor = elt0

def projection(l, c):
    [p, b1, names, b2, val] = l
    proj = kjSet(names)
    result = kjSet()
    for row in val.rows.items():
        result[ proj * row ] = 1
    return relation( names, result.items())

def emptylist(l, c):
    return []

names0 = emptylist

namesn = elt0

def names11(l, c):
    return l

def names1n(l, c):
    [ns, n] = l
    ns.append(n)
    return ns

def selection(l, c):
    [sel, p1, cond, p2, val] = l
    return cond.filter(val)

## conditions are not optimized at all!

class conditionor:
    def __init__(self, l, c):
        [self.c1, op, self.c2] = l
    def filter(self, val):
        v1 = self.c1.filter(val)
        v2 = self.c2.filter(val)
        return relation(v1.names, (v1.rows+v2.rows).items())

condfactor = elt0

class factorand(conditionor):
    def filter(self, val):
        v1 = self.c1.filter(val)
        v2 = self.c2.filter(val)
        return relation(v1.names, (v1.rows&v2.rows).items())

factorprime = elt0

class notprimary:
    def __init__(self, l, c):
        [n, self.c1] = l
    def filter(self, val):
        v1 = self.c1.filter(val)
        return relation(v1.names, (val.rows-v1.rows).items())

def elt1(l, c):
    return l[1]

primarycondition = elt1

class primaryeq:
    def __init__(self, l, c):
        [self.e1, eq, self.e2] = l
    def filter(self, val):
        rows = val.rows.items()
        e1v = self.e1.value(rows)
        e2v = self.e2.value(rows)
        result = kjSet()
        for (r, v1, v2) in map(None, rows, e1v, e2v):
            if v1==v2:
                result[r] = 1
        return relation(val.names, result.items())

class expname:
    def __init__(self, l, c):
        self.name = l[0]
    def value(self, rows):
        name = self.name
        r = list(rows)
        for i in xrange(len(r)):
            r[i] = r[i][name]
        return r

class expvalue(expname):
    def value(self, rows):
        return [self.name] * len(rows)

def rename(l, c):
    [ren, b1, names, b2, to, b3, names2, b4, val] = l
    if len(names)!=len(names2):
        raise ValueError, "names lengths must match"+`(names1, names2)`
    remap = kjDict(map(None, names2, names))
    oldnames = kjSet(val.names)
    addnames = kjSet(names2)
    remnames = kjSet(names)
    keepnames = oldnames - remnames
    remap = remap + keepnames
    if not remnames.subset(oldnames):
        #print remnames, oldnames
        raise ValueError, "old names not present"+`(names, val.names)`
    newnames = keepnames+addnames
    rows = val.rows.items()
    for i in range(len(rows)):
        rows[i] = remap*rows[i]
    return relation(newnames.items(), rows)

def named(l, c):
    [name] = l
    return c[name]

def relationval(l, c):
    [b1, names, b2, p1, rows, p2] = l
    names = tuple(names)
    ln = len(names)
    for i in xrange(len(rows)):
        this = rows[i]
        lt = len(this)
        if lt!=ln:
           raise ValueError, "names, vals don't match"+`(names,this)`
        if len(this)==1:
           this = this[0]
        else:
           this = tuple(this)
        rows[i] = kjUndump(names, this)
    return relation(names, rows)

rows0 = emptylist

rowsn = elt0

def somerows1(l, c):
    #print "somerows1", l
    return l

def somerowsn(l, c):
    #print "somerowsn", l
    [sr, c, r] = l
    sr.append(r)
    return sr

emptyrow = emptylist

row1 = somerows1

def factorexpr(l, c):
    return l[1]

def rown(l, c):
    #print "rows", l
    [r, v] = l
    r.append(v)
    return r

valuenum = valuestr = elt0

## snarfed from sqlbind
# note: all reduction function defs must precede this assign
VARS = vars()

class punter:
   def __init__(self, name):
       self.name = name
   def __call__(self, list, context):
       print "punt:", self.name, list
       return list
       
class tracer:
   def __init__(self, name, fn):
       self.name = name
       self.fn = fn
     
   def __call__(self, list, context):
       print "tracing", self.name, list
       test = self.fn(list, context)
       print self.name, "returns", test
       return test

def BindRules(sqlg):
    for name in sqlg.RuleNameToIndex.keys():
        if VARS.has_key(name):
           #print "binding", name
           sqlg.Bind(name, VARS[name]) # nondebug
           #sqlg.Bind(name, tracer(name, VARS[name]) ) # debug
        else:
           print "unbound", name
           sqlg.Bind(name, punter(name))
    return sqlg

## snarfed from sqlgen

MARSHALFILE = "relalg.mar"

import string
alphanum = string.letters+string.digits + "_"
userdefre = "[%s][%s]*" % (string.letters +"_", alphanum)
RACOMMENTREGEX = "COMMENT .*"

def userdeffn(str):
    return str
    
charstre = "'[^\n']*'"

def charstfn(str):
    return str[1:-1]
    
numlitre = "[%s][%s\.]*" % (string.digits, alphanum) # not really...

def numlitfn(str):
    """Note: this is "safe" because regex
       filters out dangerous things."""
    return eval(str)

def DeclareTerminals(Grammar):
    Grammar.Addterm("name", userdefre, userdeffn)
    Grammar.Addterm("string", charstre, charstfn)
    Grammar.Addterm("number", numlitre, numlitfn)
    
def Buildrelalg(filename=MARSHALFILE):
    import kjParseBuild
    SQLG = kjParseBuild.NullCGrammar()
    #SQLG.SetCaseSensitivity(0)
    DeclareTerminals(SQLG)
    SQLG.Keywords(keywords)
    SQLG.punct(puncts)
    SQLG.Nonterms(nonterms)
    # should add comments
    SQLG.comments([RACOMMENTREGEX])
    SQLG.Declarerules(relalg_rules)
    print "working..."
    SQLG.Compile()
    filename = INSTALLDIR+"/"+filename
    print "dumping to", filename
    outfile = open(filename, "wb")
    SQLG.MarshalDump(outfile)
    outfile.close()
    return SQLG
    
def reloadrelalg(filename=MARSHALFILE):
    import kjParser
    filename = INSTALLDIR+"/"+filename
    infile = open(filename, "rb")
    SQLG = kjParser.UnMarshalGram(infile)
    infile.close()
    DeclareTerminals(SQLG)
    BindRules(SQLG)
    return SQLG
    
def runfile(f):
    from string import split, join
    ragram = reloadrelalg()
    context = {}
    #f = open(filename, "r")
    data = f.read()
    #f.close()
    from string import split, strip
    commands = split(data, ";")
    for c in commands:
        if not strip(c): continue
        print " COMMAND:"
        data = str(c)
        pdata = "  "+join(split(c, "\n"), "\n  ")
        print pdata
        test = ragram.DoParse1(c, context)
        print

# c:\python\python relalg.py ratest.txt

if __name__=="__main__":
    try:
        done = 0
        import sys
        argv = sys.argv
        if len(argv)>1:
            command = argv[1]
            if command=="make":
                print "building relational algebra grammar"
                Buildrelalg()
                done = 1
        else:
            runfile(sys.stdin)
            done = 1
    finally:
        if not done:
            print __doc__



