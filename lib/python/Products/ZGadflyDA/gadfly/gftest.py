"""test script for gadfly

usage gftest.py <directory>

run in current directory creates a database in files
  test.dfs LIKES.grl SERVES.grl FREQUENTS.grl
"""

def test(directory):
    print "testing"
    from gadfly import gadfly
    connect = gadfly()
    connect.startup("test", directory)
    curs = connect.cursor()
    print
    print "TABLE CREATES"
    for x in table_creates:
        print x
        curs.execute(x)
    curs.execute("create table empty (nothing varchar)")
    C = """
    CREATE TABLE work (
       name VARCHAR,
       hours INTEGER,
       rate FLOAT)
       """
    print C
    curs.execute(C)
    print
    C = """
    CREATE TABLE accesses (
       page VARCHAR,
       hits INTEGER,
       month INTEGER)
       """
    print C
    curs.execute(C)
    print
    print "INSERTS"
    C = """
    INSERT INTO work(name, hours, rate) VALUES (?, ?, ?)
    """
    D = [
         ("sam", 30, 40.2),
         ("norm", 45, 10.2),
         ("woody", 80, 5.4),
         ("diane", 3, 4.4),
         ("rebecca", 120, 12.9),
         ("cliff", 26, 200.00),
         ("carla", 9, 3.5),
         ]
    for x in D: print x
    curs.execute(C, D)
    C = "create unique index wname on work(name)"
    print "Unique index:", C
    curs.execute(C)
    print "trying bad insert into unique field"
    C = "insert into work(name, hours, rate) values ('sam', 0, 0)"
    import sys
    try:
        curs.execute(C)
    except:
        print "exception as expected %s(%s)" %(sys.exc_type, sys.exc_value)
    else:
        raise "stop!", "unique index permits nonunique field"
    print; print "testing introspection"
    itests = ["select 10*4 from dual",
              "select * from __table_names__",
              #"select * from __datadefs__", # needs formatting
              "select * from __indices__",
              "select * from __columns__",
              "select * from __indexcols__",
              """
              select i.index_name, is_unique, table_name, column_name
              from __indexcols__ c, __indices__ i
              where c.index_name = i.index_name""",
              ]
    for C in itests:
        print C
        print
        curs.execute(C)
        print curs.pp()
        print
    print "testing complex, neg literals in insert"
    curs.execute("insert into work(name, hours, rate) values ('jo', -1, 3.1e-44-1e26j)")
    curs.execute("select * from work")
    print curs.pp()
    print "deleting jo"; print
    curs.execute("delete from work where name='jo'")
    C = """
    INSERT INTO accesses(page, month, hits) VALUES (?, ?, ?)
    """
    D = [
         ("index.html", 1, 2100),
         ("index.html", 2, 3300),
         ("index.html", 3, 1950),    
         ("products.html", 1, 15),   
         ("products.html", 2, 650),   
         ("products.html", 3, 98),   
         ("people.html", 1, 439),
         ("people.html", 2, 12),
         ("people.html", 3, 665),
         ]
    for x in D: print x
    curs.execute(C, D)
    for (table, stuff) in dpairs:
        ins = "insert into %s values (?, ?, ?)" % table
        if table!="frequents":
           for parameters in dataseq(stuff):
               print "singleinsert", table, parameters
               curs.execute(ins, parameters)
        else:
           print
           print "multiinsert", table
           parameters = dataseq(stuff)
           for p in parameters:
               print p
           print "multiinsert..."
           curs.execute(ins, parameters)
           print;print
    print
    print "INDICES"
    for ci in indices:
        print ci
        curs.execute(ci)
    print
    print "QUERIES"
    for x in workqueries:
        print;print
        print x
        curs.execute(x)
        print curs.pp()
        
    statement = """select name, hours
                   from work"""
    curs.execute(statement)
    print "Hours worked this week"
    print
    for (name,hours) in curs.fetchall():
        print "worker", name, "worked", hours, "hours"
    print
    print "end of work report"

    #return
    for x in queries:
        print; print
        print x
        curs.execute(x)
        #for x in curs.commands:
        #    print x
        all = curs.fetchall()
        if not all:
           print "empty!"
        else:
           print curs.pp()
           #for t in all:
               #print t
    #return
    print
    print "DYNAMIC QUERIES"
    for (x,y) in dynamic_queries:
        print; print
        print x
        print "dynamic=", y
        curs.execute(x, y)
        #for x in curs.commands:
        #    print x
        all = curs.fetchall()
        if not all:
           print "empty!"
        else:
           for t in all:
               print t
    print "repeat test"
    from time import time
    for x in repeats:
        print "repeating", x
        now = time()
        curs.execute(x)
        print time()-now, "first time"
        now = time()
        curs.execute(x)
        print time()-now, "second time"
        now = time()
        curs.execute(x)
        print time()-now, "third time"
    print "*** committing work"
    connect.commit()
    connect.close()
    print; print
    return connect
    
table_creates = [
 "create table frequents (drinker varchar, bar varchar, perweek integer)",
 "create table likes (drinker varchar, beer varchar, perday integer)",
 "create table serves (bar varchar, beer varchar, quantity integer)",
 """Create view nondrinkers(d, b)
    as select drinker, bar
       from frequents
       where drinker not in
         (select drinker from likes)""",
 ]
 
fdata = """\
  adam	lolas		1
  woody	cheers	5
  sam		cheers	5
  norm	cheers	3
  wilt	joes		2
  norm	joes		1
  lola	lolas		6
  norm	lolas		2
  woody	lolas		1
  pierre	frankies	0"""
  
sdata = """\
  cheers	bud		500
  cheers	samaddams	255
  joes	bud		217
  joes	samaddams	13
  joes	mickies	2222
  lolas	mickies	1515
  lolas	pabst		333
  winkos	rollingrock	432
  frankies	snafu       5"""
  
ldata = """\
  adam	bud			2
  wilt	rollingrock		1
  sam		bud			2
  norm	rollingrock		3
  norm	bud			2
  nan		sierranevada	1	
  woody	pabst			2
  lola	mickies		5"""
  
dpairs = [
   ("frequents", fdata),
   ("serves", sdata),
   ("likes", ldata),
  ]
  
def dataseq(s):
    from string import split
    l = split(s, "\n")
    result = map(split, l)
    from string import atoi
    for l in result:
        l[2] = atoi(l[2])
    result = map(tuple, result)
    return result
    
indices = [
"""create index fd on frequents (drinker)""",
"""create index sbb on serves (beer, bar)""",
"""create index lb on likes (beer)""",
"""create index fb on frequents (bar)""",
]

repeats = [
"""-- drinkers bars and beers
   -- where the drinker likes the beer
   -- the bar serves the beer
   -- and the drinker frequents the bar
   select f.drinker, l.beer, s.bar
   from frequents f, serves s, likes l
   where f.drinker=l.drinker and s.bar=f.bar and s.beer=l.beer""",
"""select *
   from frequents as f, serves as s
   where f.bar = s.bar and
     not exists(
       select l.drinker, l.beer
       from likes l
       where l.drinker=f.drinker and s.beer=l.beer)""",
"""select * from frequents
   where drinker = 'norm'""",
]

workqueries = [
"""-- everything from work
   select * from work""",
# stupid tests
"""select median(hours)
   from work""",
"""select *
   from work
   where name='carla' -- just carla""",
"""select name, ' ain''t worth ', rate
   from work -- the works table has more columns
   where name='carla'""",
"""select name, -- name of worker
          hours -- hours worked
   from work""",
"""select name, hours*rate as pay
   from work
   order by name""",
"""select name, rate
   from work
   where rate>=20 and rate<=100""",
"""select name, rate
   from work
   where rate between 20 and 100""",
"""select name, rate
   from work
   where rate not between 20 and 100""",
"""select name, rate, hours, hours*rate as pay
   from work""",
"""select name, rate, hours, hours*rate as pay
   from work
   where hours*rate>500 and (rate<100 or hours>5)""",
"""select name, rate, hours, hours*rate as pay
   from work
   where hours*rate>500 and rate<100 or hours>5""",
"""select avg(rate), min(hours), max(hours), sum(hours*rate) as expenses
   from work""",
"""select * from accesses""",
"""select month, sum(hits) as totalhits
   from accesses
   where month<>1
   group by month
   order by 2""",
"""select month, sum(hits) as totalhits
   from accesses
   group by month
   order by 2 desc""",
"""select month, sum(hits) as totalhits
   from accesses
   group by month
   having sum(hits)<3000
   order by 2 desc""",
"""select count(distinct month), count(distinct page)
   from accesses""",
"""select month, hits, page
   from  accesses
   order by month, hits desc""",
]
    
queries = [
"""select * from nondrinkers""",
"""select drinker as x from likes
   union select beer as x from serves
          union select drinker as x from frequents""",
"""select f.drinker, s.bar, l.beer
   from frequents f, serves s, likes l
   where f.drinker=l.drinker and s.beer=l.beer and s.bar=f.bar""",
"""select * from
   likes where beer in ('bud', 'pabst')""",
"""select l.beer, l.drinker, count(distinct s.bar)
   from likes l, serves s
   where l.beer=s.beer
   group by l.beer, l.drinker
   order by 3 desc""",
"""select l.beer, l.drinker, count(distinct s.bar) as nbars
   from likes l, serves s
   where l.beer=s.beer
   group by l.beer, l.drinker
    union distinct
     select beer, drinker, 0 as nbars
     from likes
     where beer not in (select beer from serves)
   order by 3 desc""",
"""select avg(perweek) from frequents""",
"""select * 
   from frequents
   where perweek <= (select avg(perweek) from frequents)""",
"""select * 
   from serves""",
"""select bar, avg(quantity)
   from serves
   group by bar""",
"""select * 
   from serves s1
   where quantity <= (select avg(quantity) 
                      from serves s2 
                      where s1.bar=s2.bar)""",
"""select * from frequents
   where perweek > (select avg(perweek) from frequents)""",
"""select * from frequents f1
   where perweek > (
   select avg(perweek) from frequents f2
   where f1.drinker = f2.drinker)""",
"""select * from frequents
   where perweek < any (select perweek from frequents)""",
"""select * from frequents
   where perweek >= all (select perweek from frequents)""",
"""select * from frequents
   where perweek <= all (select perweek from frequents)""",
"""select * from frequents f1
   where perweek < any 
   (select perweek from frequents f2
    where f1.drinker = f2.drinker)""",
"""select * from frequents f1
   where perweek = all 
   (select perweek from frequents f2
    where f1.drinker = f2.drinker)""",
"""select * from frequents f1
   where perweek <> all
   (select perweek from frequents f2
    where f1.drinker <> f2.drinker)""",
"""select beer
   from serves
   where beer = any (select beer from likes)""",
"""select beer
   from serves
   where beer <> all (select beer from likes)""",
"""select beer
   from serves
   where beer in (select beer from likes)""",
"""select beer
   from serves
   where beer not in (select beer from likes)""",
#"""select f1.drinker, f2.drinker
#   from frequents f1, frequents f2
#   where f1.drinker<>f2.drinker""",
#"""select *
#   from frequents f1
#   where not exists
#   (select f2.drinker
#    from frequents f2
#    where f1.drinker<>f2.drinker and f1.bar=f2.bar)""",
"""select *
   from frequents
   where perweek between 2 and 
        (select avg(perweek) from frequents)""",
"""select *
   from frequents
   where perweek not between 2 and 5""",
#   "stop",
"""select f.drinker, l.beer, s.bar
   from frequents f, serves s, likes l
   where f.drinker=l.drinker and s.bar=f.bar and s.beer=l.beer""",
   #"stop!",
"""select * from serves""",
"""select * from likes""",
"""select * from frequents
   where drinker = 'norm'""",
"""select drinker from likes
   union
   select drinker from frequents""",
"""select drinker from likes
   union distinct
   select drinker from frequents""",
"""select drinker from likes
   except
   select drinker from frequents""",
"""select drinker from likes
   intersect
   select drinker from frequents""",
#   "stop!",
"""select * from frequents
   where drinker>'norm'""",
"""select * from frequents
   where drinker<='norm'""",
"""select * from frequents
   where drinker>'norm' or drinker<'b'""",
"""select * from frequents
   where drinker<>'norm' and 'pierre'<>drinker""",
"""select * from frequents
   where drinker<>'norm'""",
"""select (drinker+' ')*2+bar
   from frequents
   where drinker>bar""",
"""select *
   from frequents as f, serves as s
   where f.bar = s.bar""",
"""select *
   from frequents as f, serves as s
   where f.bar = s.bar and
     not exists(
       select l.drinker, l.beer
       from likes l
       where l.drinker=f.drinker and s.beer=l.beer)""",
"""select *
   from likes l, frequents f
   where f.bar='cheers' and l.drinker=f.drinker and l.beer='bud'""",
"""select *
   from serves s
   where not exists (
     select *
     from likes l, frequents f
     where f.bar = s.bar and f.drinker=l.drinker and s.beer=l.beer)""",
"""select 'nonbeer drinker '+f.drinker
   from frequents f
   where not exists
      (select l.drinker, l.beer from likes l where l.drinker=f.drinker)""",
"""select l.drinker+' likes '+l.beer+' but goes to no bar'
   from likes l
   where not exists (select f.drinker from frequents f where f.drinker=l.drinker)""",
"""select bar from frequents""",
"""select distinct bar from frequents""",
"""select sum(quantity), avg(quantity), count(*), sum(quantity)/count(quantity)
   from serves""",
"""select beer, sum(quantity), avg(quantity), count(*), sum(quantity)/count(quantity)
   from serves 
   group by beer""",
"""select sum(quantity), avg(quantity), count(*), sum(quantity)/count(quantity)
   from serves
   where beer<>'bud'
""",
"""select bar, sum(quantity), avg(quantity), count(*), sum(quantity)/count(quantity)
   from serves
   where beer<>'bud'
   group by bar
   having sum(quantity)>500 or count(*)>3
   order by 2 desc
""",
"""select beer, sum(quantity), avg(quantity), count(*)
   from serves
   where beer<>'bud'
   group by beer
   having sum(quantity)>100
   order by 4 desc, beer
""",
"""select l.drinker, l.beer, count(*), sum(l.perday*f.perweek)
   from likes l, frequents f
   where l.drinker=f.drinker
   group by l.drinker, l.beer
   order by 4 desc, l.drinker, l.beer
""",
"""select l.drinker, l.beer, f.bar, l.perday, f.perweek
   from likes l, frequents f
   where l.drinker=f.drinker
   order by l.drinker, l.perday desc, f.perweek desc
""",
]

dynamic_queries = [
( "select bar from frequents where drinker=?", ("norm",) ), 
( "select * from frequents where drinker=? or bar=?", ("norm", "cheers") )
]

updates = [
"""select * from frequents""",
"""select * from likes""",
"""select * from serves""",
"""select bar, sum(quantity), avg(quantity), count(*), sum(quantity)/count(quantity)
   from serves
   where beer<>'bud'
   group by bar
   having sum(quantity)>500 or count(*)>3
   order by 2 desc
""",

"""select count(*), d from nondrinkers group by d""",
"""insert into frequents (drinker, perweek, bar)
   values ('billybob', 4, 'cheers')""",
"""select * from nondrinkers""",
"""create table templikes (dr varchar, be varchar)""",
"""select * from templikes""",
"""insert into templikes(dr, be)
   select drinker, beer from likes""",
"""create index tdindex on templikes(dr)""",
"""create index tbindex on templikes(be)""",
"""select * from templikes""",
"""delete from templikes where be='rollingrock' """,
"""select * from templikes""",
"""update templikes set dr=dr+'an' where dr='norm' """,
"""drop index tdindex""",
"""delete from templikes
   where dr=(select min(dr) from templikes)""",
"""insert into templikes (dr, be) 
   select max(dr), min(be) from templikes""",
"""select * from templikes""",
"""select * from frequents""",
"""update frequents 
   set perweek=(select max(perweek) 
                from frequents
                where drinker='norm')
   where drinker='woody'""",
"""select * from frequents""",
"""create view lazy as
   select drinker, sum(perweek) as wasted 
   from frequents
   group by drinker
   having sum(perweek)>4
   order by drinker""",
"""select * from lazy""",
"""drop view lazy""",
"""drop table templikes""",
]

trace_updates = [
"""drop index tdindex""",
]

rollback_queries = [
"""select * from likes""",
"""select * from frequents""",
"""select * from nondrinkers""",
"""select * from alldrinkers""",
"""select * from dummy""",
]
rollback_updates = [
"""create table dummy (nothing varchar)""",
"""insert into frequents(drinker, bar, perweek)
   values ('nobody', 'nobar', 0)""",
"""insert into likes(drinker, beer, perday)
   values ('wally', 'nobar', 0)""",
"""drop view alldrinkers""",
]
keep_updates = [
"""insert into frequents(drinker, bar, perweek)
   values ('peter', 'pans', 1)""",
"""create view alldrinkers as
    select drinker from frequents
    union
    select drinker from likes""",
]

def rollbacktest(directory):
    print "*" * 30
    print "*** recovery test ***"
    print; print; print
    import sys
    from gadfly import gadfly
    print "*** connecting"
    connect = gadfly("test", directory)
    cursor = connect.cursor()
    connect.autocheckpoint = 0
    print "*** executing updates to commit"
    for x in keep_updates:
        print x
        cursor.execute(x)
    connect.verbose=1
    print "*** COMMITTING OPERATIONS (connection set to verbose)"
    connect.commit()
    print "*** DUMP LOG"
    connect.dumplog()
    print; print "*** RUNNING OPS TO ROLL BACK"
    preresults = []
    for s in rollback_queries:
        print; print; print s
        try:
            cursor.execute(s)
            preresults.append(cursor.fetchall())
            print cursor.pp()
        except:
            d = sys.exc_type
            print "exception", d
            preresults.append(d)
    print; print "*** now updating with ops to rollback"
    for s in rollback_updates:
        print; print; print s
        cursor.execute(s)
    print; print; print "*** testing noncommitted results"
    for dummy in (1,2):
        postresults = []
        for s in rollback_queries:
            print s
            try:
                cursor.execute(s)
                postresults.append(cursor.fetchall())
                print cursor.pp()
            except:
                d = sys.exc_type
                print "*** exception", d
                postresults.append(d)
        if preresults==postresults:
            print "*** same results as before uncommitted updates"
        else:
            print "*** differing results from before uncommitted updates"
        if dummy==1:
            print; print "*** ROLLING BACK!"
            connect.rollback()
    print; print "*** EMULATING RECOVERY"
    for s in rollback_updates:
        print; print; print s
        cursor.execute(s)
    for dummy in (1,2):
        postresults = []
        for s in rollback_queries:
            print s
            try: 
                cursor.execute(s)
                postresults.append(cursor.fetchall())
                print cursor.pp()
            except:
                d = sys.exc_type
                print "*** exception", d
                postresults.append(d)
        if preresults==postresults:
            print "*** same results as before uncommitted updates"
        else:
            print "*** differing results from before uncommitted updates"
        if dummy==1:
            print "*** RESTART: DUMPLOG"
            connect.dumplog()
            print "*** RESTARTING (RECOVER FROM LOG, DISCARD UNCOMMITTED)"
            connect.restart()
    
def retest(directory): 
    print "*" * 30
    print "*** reconnect test"
    from gadfly import gadfly
    connect = gadfly("test", directory)
    cursor = connect.cursor()
    for s in updates:
        print; print
        print s
        if s in trace_updates:
            cursor.EVAL_DUMP = 1
        cursor.execute(s)
        cursor.EVAL_DUMP = 0
        print cursor.pp()
    #print; print "CONNECTION DATA BEFORE COMMIT"
    #connect.DUMP_ALL()
    connect.commit()
    #print; print "CONNECTION DATA AFTER COMMIT"
    #connect.DUMP_ALL()
    connect.close()
    return connect
    
if __name__=="__main__":
   import sys
   argv = sys.argv
   if len(argv)<2:
      print "USAGE: python <thismodule> <db_directory>"
      print "  please provide a directory for test database!"
   else:
      directory = argv[1]
      test(directory)
      rollbacktest(directory)
      retest(directory)
      