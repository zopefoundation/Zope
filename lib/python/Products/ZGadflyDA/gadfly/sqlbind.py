"""rule bindings for sql grammar."""

def elt0(list, context):
    """return first member of reduction"""
    return list[0]
    
def elt1(list, context):
    """return second member"""
    return list[1]
    
def elt2(list, context):
    return list[2]
    
def returnNone(list, context):
    return None
    
def stat1(list, context):
    """return list of len 1 of statements"""
    return list
    
#def statn(list, context):
#    """return a list of statement reductions"""
#    [stat, semi, statlist] = list
#    statlist.insert(0, stat)
#    return statlist
    
def thingcommalist(l, c):
    [thing, comma, list] = l
    list.insert(0, thing)
    return list
    
def listcommathing(l, c):
    [list, comma, thing] = l
    list.append(thing)
    return list
    
statn = thingcommalist
selstat = elt0
insstat = elt0
createtablestat = elt0
droptablestat = elt0
delstat = elt0
updatestat = elt0
createindexstat = elt0
dropindexstat = elt0
createviewstat = elt0
dropviewstat = elt0

# drop view statement stuff
def dropview(l, c):
    [drop, view, name] = l
    from sqlsem import DropView
    return DropView(name)
    
# create view statement stuff
def createview(l, c):
    [create, view, name, namelist, as, selection] = l
    from sqlsem import CreateView
    return CreateView(name, namelist, selection)
    
optnamelist0 = returnNone
optnamelistn = elt1

# drop index statement stuff
def dropindex(l, c):
    [drop, index, name] = l
    from sqlsem import DropIndex
    return DropIndex(name)

# create index statement stuff
def createindex(l, c):
    [create, index, name, on, table, op, namelist, cp] = l
    from sqlsem import CreateIndex
    return CreateIndex(name, table, namelist)

def createuniqueindex(l, c):
    [create, unique, index, name, on, table, op, namelist, cp] = l
    from sqlsem import CreateIndex
    return CreateIndex(name, table, namelist, unique=1)
    
names1 = stat1
namesn = listcommathing

# update statement stuff

def update(l, c):
    [upd, name, set, assns, condition] = l
    from sqlsem import UpdateOp
    return UpdateOp(name, assns, condition)
    
def assn(l, c):
    [col, eq, exp] = l
    return (col, exp)
    
def assn1(l, c):
    [ (col, exp) ] = l
    from sqlsem import TupleCollector
    result = TupleCollector()
    result.addbinding(col, exp)
    return result
    
def assnn(l, c):
    [ result, comma, (col, exp) ] = l
    result.addbinding(col, exp)
    return result
    
# delete statement stuff

def deletefrom(l, c):
    [delete, fromkw, name, where] = l
    from sqlsem import DeleteOp
    return DeleteOp(name, where)
    
# drop table stuff

def droptable(l, c):
    [drop, table, name] = l
    from sqlsem import DropTable
    return DropTable(name)

# create table statement stuff

def createtable(list, context):
    [create, table, name, p1, colelts, p2] = list
    from sqlsem import CreateTable
    return CreateTable(name, colelts)
    
colelts1 = stat1
coleltsn = listcommathing
#def coleltsn(list, c):
#    [c1, cc, ce] = list
#    c1.append(ce)
#    return c1
    
coleltid = elt0
coleltconstraint = elt0

def coldef(l, c):
    [colid, datatype, default, constraints] = l
    from sqlsem import ColumnDef
    return ColumnDef(colid, datatype, default, constraints)
    
optdef0 = returnNone
optcolconstr0 = returnNone
stringtype = exnumtype = appnumtype = integer = float = varchar = elt0
varcharn = elt0

# insert statement stuff

def insert1(l, c):
    [insert, into, name, optcolids, insert_spec] = l
    from sqlsem import InsertOp
    return InsertOp(name, optcolids, insert_spec)
    
optcolids0 = returnNone
optcolids1 = elt1
colids1 = stat1
colidsn = listcommathing

def insert_values(l, c):
    from sqlsem import InsertValues
    return InsertValues(l[2])
    
def insert_query(l, c):
    from sqlsem import InsertSubSelect
    return InsertSubSelect(l[0])
    
litlist1 = stat1
litlistn = listcommathing

sliteral0 = elt0
def sliteralp(l, c):
    [p, v] = l
    return +v
    
def sliterald(l, c):
    [l1, m, l2] = l
    return l1 - l2
    
def sliterals(l, c):
    [l1, p, l2] = l
    return l1 + l2
    
def sliteralm(l, c):
    [m, v] = l
    return -v

# select statement stuff
    
def selectx(list, context):
    [sub, optorder_by] = list
    #sub.union_select = optunion
    sub.order_by = optorder_by
    # number of dynamic parameters in this parse.
    sub.ndynamic = context.ndynamic()
    return sub
    
psubselect = elt1
    
def subselect(list, context):
    [select, alldistinct, selectlist, fromkw, trlist,
     optwhere, optgroup, opthaving, optunion] = list
    from sqlsem import Selector
    sel = Selector(
      alldistinct, 
      selectlist, 
      trlist, 
      optwhere, 
      optgroup, 
      opthaving,
      # store # of dynamic parameters seen in this parse.
      ndynamic = context.ndynamic()
      )
    sel.union_select = optunion
    return sel
    
def ad0(list, context):
    return "ALL"
    
adall = ad0

def addistinct(list, context):
    return "DISTINCT"
    
def where0(list, context):
    from sqlsem import BTPredicate
    return BTPredicate() # true
    
where1 = elt1

group0 = returnNone

group1 = elt2

colnames1 = stat1
    
colnamesn = listcommathing

having0 = returnNone

having1 = elt1

union0 = returnNone

def union1(l, c):
    [union, alldistinct, selection] = l
    from sqlsem import Union
    return Union(alldistinct, selection)

def except1(l, c):
    [union, selection] = l
    alldistinct = "DISTINCT"
    from sqlsem import Except
    return Except(alldistinct, selection)

def intersect1(l, c):
    [union, selection] = l
    alldistinct = "DISTINCT"
    from sqlsem import Intersect
    return Intersect(alldistinct, selection)

order0 = returnNone
order1 = elt2
#orderby = elt2
sortspec1 = stat1
sortspecn = listcommathing

def sortint(l, c):
    from sqlsem import PositionedSort
    [num, ord] = l
    from types import IntType
    if type(num)!=IntType or num<=0:
       raise ValueError, `num`+': col position not positive int'
    return PositionedSort(num, ord)
    
def sortcol(l, c):
    from sqlsem import NamedSort
    [name, ord] = l
    return NamedSort(name, ord)
    
def optord0(l, c):
    return "ASC"
    
optordasc = optord0

def optorddesc(l, c):
    return "DESC"

## table reference list returns list of (name, name) or (name, alias)
def trl1(l, c):
    [name] = l
    return [(name, name)]
    
def trln(l,c):
    [name, comma, others] = l
    others.insert(0, (name, name))
    return others
    
def trl1a(l,c):
    [name, alias] = l
    return [(name, alias)]
    
def trlna(l,c):
    [name, alias, comma, others] = l
    others.insert(0, (name, alias))
    return others
    
def trl1as(l,c):
    [name, as, alias] = l
    return [(name, alias)]
    
def trlnas(l,c):
    [name, as, alias, comma, others] = l
    others.insert(0, (name, alias))
    return others
    
tablename1 = elt0
columnid1 = elt0

def columnname1(list, context):
    [ci] = list
    return columnname2([None, None, ci], context)
    
def columnname2(list, context):
    [table, ignore, col] = list
    from sqlsem import BoundAttribute
    return BoundAttribute(table, col)
    
def dynamic(list, context):
    from sqlsem import BoundAttribute
    # return a new dynamic parameter
    int = context.param()
    return BoundAttribute(0, int)
    
# expression stuff
def literal(list, context):
    [lit] = list
    from sqlsem import Constant
    return Constant(lit)
    
def stringstring(l, c):
    """two strings in sequence = apostrophe"""
    [l1, l2] = l
    from sqlsem import Constant
    value = "%s'%s" % (l1.value0, l2)
    return Constant(value)
    
numlit = literal
stringlit = literal
primarylit = elt0
primary1 = elt0
factor1 = elt0
term1 = elt0
exp1 = elt0

def expplus(list, context):
    [exp, plus, term] = list
    return exp + term
    
def expminus(list, context):
    [exp, minus, term] = list
    return exp - term
    
def termtimes(list, context):
    [exp, times, term] = list
    return exp * term
    
def termdiv(list, context):
    [exp, div, term] = list
    return exp / term
    
plusfactor = elt1

def minusfactor(list, context):
    [minus, factor] = list
    return -factor
    
primaryexp = elt1

primaryset = elt0

def countstar(l, c):
    from sqlsem import Count
    return Count("*")
    
def distinctset(l, c):
    [agg, p1, distinct, exp, p2] = l
    return set(agg, exp, 1)
    
distinctcount = distinctset
    
def allset(l, c):
    [agg, p1, exp, p2] = l
    return set(agg, exp, 0)
    
allcount = allset

def set(agg, exp, distinct):
    import sqlsem
    if agg=="AVG":
       return sqlsem.Average(exp, distinct)
    if agg=="COUNT":
       return sqlsem.Count(exp, distinct)
    if agg=="MAX":
       return sqlsem.Maximum(exp, distinct)
    if agg=="MIN":
       return sqlsem.Minimum(exp, distinct)
    if agg=="SUM":
       return sqlsem.Sum(exp, distinct)
    if agg=="MEDIAN":
       return sqlsem.Median(exp, distinct)
    raise NameError, `agg`+": unknown aggregate"
    
average = count = maximum = minimum = summation = median = elt0

def predicateeq(list, context):
    [e1, eq, e2] = list
    return e1.equate(e2)
    
def predicatene(list, context):
    [e1, lt, gt, e2] = list
    return ~(e1.equate(e2))
    
def predicatelt(list, context):
    [e1, lt, e2] = list
    return e1.lt(e2)

def predicategt(list, context):
    [e1, lt, e2] = list
    return e2.lt(e1)

def predicatele(list, context):
    [e1, lt, eq, e2] = list
    return e1.le(e2)

def predicatege(list, context):
    [e1, lt, eq, e2] = list
    return e2.le(e1)
    
def predbetween(list, context):
    [e1, between, e2, andkw, e3] = list
    from sqlsem import BetweenPredicate
    return BetweenPredicate(e1, e2, e3)
    
def prednotbetween(list, context):
    [e1, notkw, between, e2, andkw, e3] = list
    from sqlsem import BetweenPredicate
    return ~BetweenPredicate(e1, e2, e3)
    
predicate1 = elt0
bps = elt1
bp1 = elt0

# exists predicate stuff
predexists = elt0
def exists(l, c):
    [ex, paren1, subquery, paren2] = l
    from sqlsem import ExistsPred
    return ExistsPred(subquery)

def notbf(list, context):
    [ notst, thing ] = list
    return ~thing
    
# quantified predicates
nnall = elt0
nnany = elt0

def predqeq(list, context):
    [exp, eq, allany, p1, subq, p2] = list
    from sqlsem import QuantEQ, QuantNE
    if allany=="ANY":
       return QuantEQ(exp, subq)
    else:
       return ~QuantNE(exp, subq)
    
def predqne(list, context):
    [exp, lt, gt, allany, p1, subq, p2] = list
    from sqlsem import QuantEQ, QuantNE
    if allany=="ANY":
       return QuantNE(exp, subq)
    else:
       return ~QuantEQ(exp, subq)
    
def predqlt(list, context):
    [exp, lt, allany, p1, subq, p2] = list
    from sqlsem import QuantLT, QuantGE
    if allany=="ANY":
       return QuantLT(exp, subq)
    else:
       return ~QuantGE(exp, subq)
    
def predqgt(list, context):
    [exp, gt, allany, p1, subq, p2] = list
    from sqlsem import QuantGT, QuantLE
    if allany=="ANY":
       return QuantGT(exp, subq)
    else:
       return ~QuantLE(exp, subq)

def predqle(list, context):
    [exp, less, eq, allany, p1, subq, p2] = list
    from sqlsem import QuantGT, QuantLE
    if allany=="ANY":
       return QuantLE(exp, subq)
    else:
       return ~QuantGT(exp, subq)
       
def predqge(list, context):
    [exp, gt, eq, allany, p1, subq, p2] = list
    from sqlsem import QuantGE, QuantLT
    if allany=="ANY":
       return QuantGE(exp, subq)
    else:
       return ~QuantLT(exp, subq)
       
# subquery expression
def subqexpr(list, context):
    [p1, subq, p2] = list
    from sqlsem import SubQueryExpression
    return SubQueryExpression(subq)
       
def predin(list, context):
    [exp, inkw, p1, subq, p2] = list
    from sqlsem import InPredicate
    return InPredicate(exp, subq)
    
def prednotin(list, context):
    [exp, notkw, inkw, p1, subq, p2] = list
    from sqlsem import InPredicate
    return ~InPredicate(exp, subq)
    
def predinlits(list, context):
    [exp, inkw, p1, lits, p2] = list
    from sqlsem import InLits
    return InLits(exp, lits)
    
def prednotinlits(list, context):
    [exp, notkw, inkw, p1, lits, p2] = list
    from sqlsem import InLits
    return ~InLits(exp, lits)

    
bf1 = elt0

def booln(list, context):
    [ e1, andst, e2 ] = list
    return e1&e2
    
bool1 = elt0

def searchn(list, context):
    [ e1, orst, e2 ] = list
    return e1 | e2
    
search1 = elt0

colalias = elt0

# select list stuff
def selectstar(l,c):
    return "*"
    
selectsome = elt0
select1 = elt0

# selectsub returns (expression, asname)

def select1(list, context):
    [ (exp, name) ] = list
    from sqlsem import TupleCollector
    result = TupleCollector()
    result.addbinding(name, exp)
    return result
    
def selectn(list, context):
    [ selectsubs, comma, select_sublist ] = list
    (exp, name) = select_sublist
    selectsubs.addbinding(name, exp)
    return selectsubs
    
def selectit(list, context):
    [exp] = list
    return (exp, None) # no binding!
    
def selectname(list, context):
    [exp, as, alias] = list
    return (exp, alias)
    
colalias = elt0


#### do the bindings.

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
       print self.name, list
       return self.fn(list, context)

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


