
"""test script for gadfly client and server

Usage:  This script interacts with the test database generated
  by gftest.py.  To start the server from the directory containing
  the dbtest directory use:

     python gfstest.py start

  THIS WILL ONLY WORK IF YOU CREATED THE test DATABASE IN
  DIRECTORY dbtest FIRST USING 

     python gftest.py dbtest

  UNLESS YOU RUN THE SERVER IN THE BACKGROUND THE SERVER WILL
  HOG THE WINDOW YOU STARTED IT IN AND YOU WILL HAVE TO USE ANOTHER
  WINDOW UNTIL THE SERVER IS SHUT DOWN (SEE BELOW).

  Then from *anywhere* (on the same machine) access the database
  using
     python gfstest.py restart
       - restart the server (reread the database)
     python gfstest.py checkpoint
       - force checkpoint the server
     python gfstest.py queries
       - run some example queries and updates
     python gfstest.py policy_test
       - test the policies test and test1 created by the startup
         function in this module.
     python gfstest.py bogusshutdown
       - attempt to shut down the server with a bogus password
         [should generate an exception]

...and finally
     python gfstest.py shutdown
       - shut down the server for real.

As mentioned the startup function of this module illustrates
how to create a "startup" function for a server and initialize policy
objects with named, prepared queries.

"""

PORT = 2222
DB = "test"
DBDIR = "dbtest"
PW = "admin"
STARTUP = "gfstest"

import sys, socket


def main():
    argv = sys.argv
    command = argv[1]
    if command=="start":
        print "attempting to start the server"
        from gfserve import Server
        print "making a server on", PORT, DB, DBDIR, PW, STARTUP
        S = Server(PORT, DB, DBDIR, PW, STARTUP)
        print "initializing the server"
        S.init()
        print "starting the server", S.connection
        S.start()
    elif command=="shutdown":
        dosimple("shutdown", PW)
    elif command=="bogusshutdown":
        print "BOGUS shutdown attempt"
        dosimple("shutdown", "bad password")
    elif command=="restart":
        dosimple("restart", PW)
    elif command=="checkpoint":
        dosimple("checkpoint", PW)
    elif command=="queries":
        doqueries()
    elif command=="policy_test":
        policy_test()
    else:
        print "unknown command", command
        print __doc__

def policy_test():
    """test the test1 and test policies"""
    print "testing non-admin policies test and test1"
    from gfclient import gfclient
    import sys
    machine = socket.gethostname()
    conn = gfclient("test", PORT, "test", machine)
    cursor = conn.cursor()
    print "testing test policy: nan values before:"
    cursor.execute_prepared("getnan")
    for x in cursor.fetchall():
        print x
    print "updating nan"
    cursor.execute_prepared("updatenan", ("pabst", 4))
    print "nan after"
    cursor.execute_prepared("getnan")
    for x in cursor.fetchall():
        print x
    print "updating nan again"
    cursor.execute_prepared("updatenan", ("rollingrock", 1))
    print "trying an illegal update"
    try:
        cursor.execute("delete from frequents")
    except:
        print "exception", sys.exc_type, sys.exc_value
        print "as expected"
    else:
        raise "DAMN!", "illegal query apparently completed!!!"
    print; print "testing policy test1"; print
    conn = gfclient("test1", PORT, "test1", machine)
    cursor = conn.cursor()
    print "getting norm"
    cursor.execute_prepared("qlike", ("norm",))
    print cursor.description
    for x in cursor.fetchall():
        print x
    print "trying an illegal query again"
    try:
        cursor.execute("create table test(name varchar)")
    except:
        print "exception", sys.exc_type, sys.exc_value
        print "as expected"
    else:
        raise "Damn!(2)", "illegal query apparently completed"

def startup(admin_policy, connection, Server_instance):
    """example startup script.

       add a policies test and test1 passwords same
         test1 is allowed to query the frequents table by name
         test is allowed to update likes where drinker='nan'
       also add prepared query dumpwork to admin_policy.
    """
    from gfserve import Policy
    admin_policy["dumpwork"] = "select * from work"
    test1 = Policy("test1", "test1", connection, queries=0)
    test = Policy("test", "test", connection, queries=0)
    test1["qlike"] = "select * from likes where drinker=?"
    test["updatenan"] = """
      update likes
      set beer=?, perday=?
      where drinker='nan'
    """
    test["getnan"] = """
    select * from likes where drinker='nan'
    """
    return {"test": test, "test1": test1}

def doqueries():
    print "executing queries and updates"
    from gfclient import gfclient
    import sys
    machine = socket.gethostname()
    conn = gfclient("admin", PORT, PW, machine)
    cursor = conn.cursor()
    for q in admin_queries:
        print;print;print q;print
        try:
            cursor.execute(q)
        except:
            print "exception in execute"
            print sys.exc_type
            v = sys.exc_value
            from types import TupleType, ListType
            if type(v) in (TupleType, ListType):
               for x in v: print x
            else:
               print v
        else:
            print "executed"
            #print q
            print "description"
            print cursor.description
            print "results"
            try:
                r = cursor.fetchall()
                if r is None:
                    print "no results"
                else:
                    for x in r:
                        print x
            except:
                print "exception in results"
                print sys.exc_type, sys.exc_value
                print dir(cursor)
    # try dumpwork
    print; print; print "dumpwork"; print
    cursor.execute_prepared("dumpwork")
    for x in cursor.fetchall():
        print x
    # try dynamic parameters
    stat = """
    select distinct drinker
    from likes l, serves s
    where l.beer = s.beer and s.bar=?
    """
    print; print stat; print "dynamic query ?=cheers"
    cursor.execute(stat, ("cheers",))
    for x in cursor.fetchall():
        print x
            
admin_queries = [
"""select count(*) from work""",
"""select * from frequents""",
"""select count(*) from frequents""",
"""select count(drinker) from frequents""",
"""insert into frequents(drinker, bar, perweek)
     values ('sally', 'cheers', 2)""",
"""select * from frequents""",
"""select syntax error from work""",
"""select drinker, count(bar) from frequents
   group by drinker""",
]

def dosimple(command, pw):
    print "attempting remote %s (%s) for server on local machine" % (command, pw)
    from gfclient import gfclient
    machine = socket.gethostname()
    conn = gfclient("admin", PORT, pw, machine)
    action = getattr(conn, command)
    print action()

if __name__=="__main__":
    main()