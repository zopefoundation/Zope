#!/usr/local/bin/python
"""python lint using kwParsing

The goal of this module/filter is to help find
programming errors in python source files.

As a filter use thusly:

% python kjpylint.py source_file.py

As an internal tool use like this:

  import kjpylint
  (pyg, context) = kjpylint.setup()
  kjpylint.lint(data, pyg, context)

where data is the text of a python program.
You can build your own context structure by
subclassing GlobalContext, and redefining
GlobalContext.complain(string) for example.
You could do a lot more than that too...

Also, to lint all *.py files recursively contained
in a directory hierarchy use

  kjpylint.lintdir("/usr/local/lib/python") # for example

FEATURES:

Lint expects
  1) a newline or two at the end of the data;
  2) consistent indenting (and inconsistency may be invisible)
     [eg " \t" and "\t" are not the same indent
     to Lint, but Python sees them the same.]

If (1) or (2) are not satisfied Lint will raise
an exception.

Buglets: lambdas and for loops on one line generate
  extraneous warnings.

Notes:
======
The lint process works, in outline, like this.
Scan over a python program 

x = 1

def f(a):
    a = x
    d.x, y = b

z = w

and build annotations like

[ set("x", 1),
  [
    get("x", 4)
    set("a", 4)
    get("b", 5)
    get("d", 5)
    set("y", 5)
    pop_local()
  ]
  get("w", 7)
  set("z", 7) ]

from this stream conclude
  warning on line 5: b used before set
  warning on line 5: d used before set
  warning on line 5: y set, never used
etc. using simple one pass approximate flow
analysis.
"""

pyg = context = None

#import pygram
from pygram import newlineresult

# reduction rules:
#  only need to consider 
#    expressions, assignments, def, class, global, import, from, for
#
# expressions return a list of unqualified names, not known set
# qualified names are automatically put in context as refs
#
# assignments set left names, ref right names
#
# def sets new name for function and args,
#  refs other names
#
# class adds new name for class
#  refs other names
#
# global forces global interpretation for name
#
# import adds FIRST names
# from sets names
# for sets names
#
# related rules
# ASSIGNMENT REQUIRES SPECIAL TREATMENT
#@R assn1 :: assn >> testlist = testlist

def assn1(list, context):
    [t1, e, t2] = list
    return assn(t1, t2)

#@R assnn :: assn >> testlist = assn

def assnn(list, context):
    [t1, e, a1] = list
    return assn(t1, a1)

# @R assn1c :: assn >> testlist , = testlist
def assn1c(list, context):
    [t1, c, e, t2] = list
    return assn(t1, t2)

# @R assn1c2 :: assn >> testlist , = testlist ,
def assn1c2(list, context):
    del list[-1]
    return assn1c(list, context)

# @R assnnc :: assn >> testlist , = assn
def assnnc(list, context):
    return assn1c(list, context)

def assn(left, right):
    result = right
    for x in left:
        (ln, ri, op, name) = x
        if op == "ref":
           result.append( (ln, ri, "set", name) )
        else:
           result.append(x)
    return result

#@R except2 :: except_clause >> except test , test
def except2(list, context):
    [e, t1, c, t2] = list
    result = t1
    for (ln, ri, op, name) in t2:
        result.append( (ln, ri, "set", name) )
    return result

#@R smassn :: small_stmt >> assn
#  ignored

#@R rfrom :: import_stmt >> from dotted_name import name_list 
#@R rfromc :: import_stmt >> from dotted_name import name_list ,

def rfrom(list, context):
    #print rfrom, list
    [f, d, i, n] = list
    # ignore d
    return n

def rfromc(list, context):
    return rfrom(list[:-1])

def mark(kind, thing, context):
    L = context.LexD
    lineno = L.lineno
    # are we reducing on a newline?
    if L.lastresult==newlineresult:
       lineno = lineno-1
    return (lineno, -L.realindex, kind, thing)

#@R dn1 :: dotted_name >> NAME

def dn1(list, context):
    #print "dn1", list
    #L = context.LexD
    return [ mark("set", list[0], context) ]
    #return [ (L.lineno, -L.realindex, "set", list[0]) ]



#  handles import case, make name set local
#@R nlistn :: name_list >> name_list  , NAME

def nlistn(list, context):
    #print "nlistn", list
    [nl, c, n] = list
    #L = context.LexD
    #nl.append( (L.lineno, -L.realindex, "set", n) )
    nl.append( mark("set", n, context) )
    return nl

#@R nlist1 :: name_list >> NAME

def nlist1(list, context):
    #print "nlist1", list
    #L = context.LexD
    #return [ (L.lineno, -L.realindex, "set", list[0]) ]
    return [ mark("set", list[0], context) ]

# ignore lhs in calls with keywords.
#@R namearg :: argument >> test = test
def namearg(list, context):
    [t1, e, t2] = list
    return t2

#  handles from case, make names set local
#@R global1 :: global_stmt >> global NAME 

def global1(list, context):
    #print "global1", list
    #L = context.LexD
    #return [ (L.lineno, -L.realindex, "global", list[1]) ]
    return [ mark("global", list[1], context) ]

#@R globaln :: global_stmt >> global_stmt , NAME 
#  handles global, make names global (not set or reffed)

def globaln(list, context):
    #print "globaln", list
    [g, c, n] = list
    #L = context.LexD
    #g.append( (L.lineno, -L.realindex, "global", n) )
    g.append( mark("global", n, context) )
    return g

#@R for1 :: for_stmt >> 
#for exprlist in testlist  : 
#     suite

def for1(list, context):
    #print "for1", list
    [f, e, i, t, c, s] = list
    refs = t + s
    return assn(e, refs)

#@R for2 :: for_stmt >> 
#for exprlist in testlist  : 
#     suite 
#else : 
#     suite

def for2(list,context):
    #print "for2", list
    [f, e, i, t, c1, s1, el, c2, s2] = list
    refs = t + s1 + s2
    return assn(e, refs)

###
#@R class1 :: classdef  >> class NAME : suite
def class1(list, context):
    [c, n, cl, s] = list
    return Class(n, [], s, context)

#@R class2 :: classdef  >> class NAME ( testlist ) : suite
def class2(list, context):
    [c, n, opn, t, cls, cl, s] = list
    return Class(n, t, s, context)

def Class(name, testlist, suite, context):
    globals = analyse_scope(name, suite, context, unused_ok=1)
    context.defer_globals(globals)
    result = testlist
    L = context.LexD
    # try to correct lineno
    lineno = L.lineno
    realindex = L.realindex
    for (ln, ri, op, n) in testlist+suite:
        lineno = min(lineno, ln)
    result.append((lineno, -realindex, "set", name))
    #result.append( mark("set", name, context) )
    # supress complaints about unreffed classes
    result.append((lineno+1, -realindex, "qref", name))
    #result.append( mark("qref", name, context) )
    return result

# vararsglist requires special treatment.
#  return (innerscope, outerscope) pair of lists
# @R params1 :: parameters >> ( varargslist )
def params1(l, c):
    return l[1]

params1c = params1

#@R params2 :: varargslist >> 
def params2(l, c):
    return ([], [])

#@R params3 :: varargslist >> arg
def params3(l, c):
    return l[0]

#@R params4 :: varargslist >> varargslist , arg
def params4(l, c):
    #print "params4", l
    [v, c, a] = l
    v[0][0:0] = a[0]
    v[1][0:0] = a[1]
    return v

#@R argd :: arg >> NAME = test
def argd(l, c):
    [n, e, t] = l
    #L = c.LexD
    #return ([(L.lineno, -L.realindex, "set", n)], t)
    return ([ mark("set", n, c) ], t)

#@R arg2 :: arg >> fpdef
def arg2(l, c):
    return l[0]

#@R arg3 :: arg >> * NAME
def arg3(l, c):
    del l[0]
    return fpdef1(l, c)

#@R arg4 :: arg >> ** NAME
def arg4(l, c):
    #del l[0]
    return arg3(l, c)

#@R fpdef1 :: fpdef  >> NAME
def fpdef1(l, c):
    [n] = l
    #LexD = c.LexD
    return ([ mark("set", n, c) ], [])

#@R fpdef2 :: fpdef  >>  ( fplist )
def fpdef2(l, c):
    return l[1]

## @R fpdef2c :: fpdef  >>  ( fplist , )
#fpdef2c = fpdef2

##31
#@R fplist1 :: fplist >> fpdef
def fplist1(l, c):
    #print l
    return l[0]

#@R fplistn :: fplist >> fplist , fpdef
fplistn = params4

#@R rdef :: funcdef >> def NAME parameters : suite
def rdef(list, context):
    #print "rdef", list
    [ddef, name, parameters, c, suite] = list
    (l, g) = parameters
    globals = analyse_scope(name, l + suite, context)
    # for embedded function defs global internal refs must be deferred.
    context.defer_globals(globals)
    result = g
    L = context.LexD
    # try to steal a lineno from other declarations:
    lineno = L.lineno
    index = L.realindex
    for (ln, ri, op, n) in l+g+suite:
        lineno = min(lineno, ln)
    if name is not None:
       result.append((lineno, -index, "set", name))
       # Note: this is to prevent complaints about unreffed functions
       result.append((lineno+1, -index, "qref", name))
    return result

#@R testlambda1 :: test >> lambda varargslist : test
def testlambda1(list, context):
    [l, v, c, t] = list
    return rdef(["def", None, v, ":", t], context)

def analyse_scope(sname, var_accesses, context, unused_ok=0):
    var_accesses.sort()
    result = []
    globals = {}
    locals = {}
    # scan for globals
    for x in var_accesses:
        (ln, ri, op, name) = x
        if op == "global":
           globals[name] = ln
        #result.append(x) (ignore global sets in local context)
    # scan for locals
    for (ln, ri, op, name) in var_accesses:
        if op == "set" and not locals.has_key(name):
           if globals.has_key(name):
              context.complain(
     "Warning: set of global %s in local context %s" % (`name`, `sname`))
              result.append( (ln, ri, op, name) )
              pass # ignore global set in local context
           else:
              locals[name] = [ln, 0] # line assigned, #refs
    # scan for use before assign, etc.
    for x in var_accesses:
        (ln, ri, op, name) = x
        if locals.has_key(name):
           if op in ["ref", "qref"]:
              set = locals[name]
              set[1] = set[1] + 1
              assnln = set[0]
              if (ln <= assnln):
                 context.complain( 
          "(%s) local %s ref at %s before assign at %s" % (
           sname, `name`, ln, `assnln`))
        elif op not in ("global", "set"):
           # ignore global sets in local context.
           result.append(x)
    # scan for no use
    if not unused_ok:
       for (name, set) in locals.items():
           [where, count] = set
           if count<1:
              context.complain(
                 "(%s) %s defined before %s not used" % (sname, `name`, where))
    return result  

### note, need to make special case for qualified names
#@R powera :: power >> atom trailerlist

def powera(list, context):
    #print "powera", list
    [a, (t, full)] = list
    if a and full:
       # atom is a qualified name
       (ln, ri, op, n) = a[0]
       result = [ (ln, ri, "qref", n) ]
    else:
       result = a
    result = result + t
    #print "returning", result
    return result
       
#@R trailerlist0 :: trailerlist >> 
def trailerlist0(list, context):
    return ([], 0) # empty trailerlist

#@R trailerlistn :: trailerlist >> trailer trailerlist
def trailerlistn(list, context):
    #print "trailerlistn", list
    result = list[0] + list[1][0]
    for i in xrange(len(result)):
        (a, b, op, d) = result[i]
        result[i] = (a, b, "qref", d)
    return (result, 1)

# make name+parameters set local reduce suite...

def default_reduction(list, context):
    # append all lists
    from types import ListType
    #print "defred", list
    #return
    result = []
    for x in list:
        if type(x)==ListType:
           if result == []:
              if len(x)>0 and type(x[0])==ListType:
                 raise "oops", x
              result = x
           else:
              for y in x:
                  result.append(y)
    return result

def aname(list, context):
    #print "aname", list, context
    L = context.LexD
    # note -L.realindex makes rhs of assignment seem before lhs in sort.
    return [ (L.lineno, -L.realindex, "ref", list[0]) ]


# the highest level reduction!
# all1 :: all >> file_input DEDENT
def all1(list, context):
    stuff = list[0]
    context.when_done(stuff)

# first test
def BindRules(pyg):
    for name in pyg.RuleNameToIndex.keys():
        pyg.Bind(name, default_reduction)
    pyg.Bind("all1", all1)
    pyg.Bind("testlambda1", testlambda1)
    pyg.Bind("except2", except2)
    pyg.Bind("namearg", namearg)
    pyg.Bind("rfrom", rfrom)
    pyg.Bind("rfromc", rfromc)
    pyg.Bind("class1", class1)
    pyg.Bind("class2", class2)
    pyg.Bind("aname", aname)
    pyg.Bind("assn1", assn1)
    pyg.Bind("assnn", assnn)
    pyg.Bind("assn1c", assn1c)
    pyg.Bind("assn1c2", assn1c2)
    pyg.Bind("assnnc", assnnc)
    pyg.Bind("dn1", dn1)
    pyg.Bind("nlistn", nlistn)
    pyg.Bind("nlist1", nlist1)
    pyg.Bind("global1", global1)
    pyg.Bind("globaln", globaln)
    pyg.Bind("for1", for1)
    pyg.Bind("for2", for2)
    pyg.Bind("powera", powera)
    pyg.Bind("trailerlist0", trailerlist0)
    pyg.Bind("trailerlistn", trailerlistn)
    pyg.Bind("params1", params1)
    pyg.Bind("params1c", params1c)
    pyg.Bind("params2", params2)
    pyg.Bind("params3", params3)
    pyg.Bind("params4", params4)
    pyg.Bind("argd", argd)
    pyg.Bind("arg2", arg2)
    pyg.Bind("arg3", arg3)
    pyg.Bind("arg4", arg4)
    pyg.Bind("fpdef1", fpdef1)
    pyg.Bind("fpdef2", fpdef2)
#    pyg.Bind("fpdef2c", fpdef2c)
    pyg.Bind("fplist1" , fplist1 )
    pyg.Bind("fplistn" , fplistn)
    pyg.Bind("rdef" , rdef)
#    pyg.Bind( , )

class globalContext:
    def __init__(self, lexd):
        self.deferred = []
        self.LexD = lexd
    def complain(self, str):
        print str
    def defer_globals(self, globals):
        self.deferred[0:0] = globals
    def when_done(self, list):
        stuff = list + self.deferred + self.patch_globals()
        globals = analyse_scope("<module global>", stuff, self)
        seen = {}
        for (ln, ri, op, name) in globals:
            if not seen.has_key(name) and op!="set":
               seen[name] = name
               self.complain(
      "%s: (%s) %s not defined in module?" % (ln, op, `name`))
        self.deferred = [] # reset state.
    def patch_globals(self):
        # patch in global names
        import __builtin__
        names = dir(__builtin__)
        list = names[:]
        list2 = names[:]
        for i in xrange(len(list)):
            list[i] = (-2, -900, "set", names[i])
            list2[i] = (-1, -900, "qref", names[i])
        return list + list2

teststring = """
class x(y,z):
  '''
     a doc string
     blah
  '''
  def test(this, that):
    w = that+this+x, n
    x = 1
    return w
"""

def go():
    import sys
    try:
        file = sys.argv[1]
    except IndexError:
        print "required input file missing, defaulting to test string"
        data = teststring
    else:
        data = open(file).read()
    print "setup"
    (pyg, context) = setup()
    print "now parsing"
    lint(data, pyg, context)

def setup():
    global pyg, context
    import pygram
    pyg = pygram.unMarshalpygram()
    BindRules(pyg)
    context = globalContext(pyg.LexD)
    return (pyg, context)

def lint(data, pygin=None, contextin=None):
    if pygin is None: pygin = pyg
    if contextin is None: contextin = context
    pygin.DoParse1(data, contextin)

def lintdir(directory_name):
    """lint all files recursively in directory"""
    from find import find
    print "\n\nrecursively linting %s\n\n" % directory_name
    (pyg, context) = setup()
    python_files = find("*.py", directory_name)
    for x in python_files:
        print "\n\n [ %s ]\n\n" % x
        lint( open(x).read(), pyg, context )
        print "\014"

if __name__=="__main__": go()
