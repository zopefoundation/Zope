"""Demonstration of the Remote View protocol for adding
   specially implemented Views in an application."""
from gadfly import gadfly

# create the database
g = gadfly()
g.startup("dbtest", "dbtest")	# assume directory "dbtest" exists

# define a remote view class
import gfintrospect

class myTable(gfintrospect.RemoteView):

    """A remote view must define self.column_names
       to return a (fixed) list of string column names and
       self.listing() to return a possibly varying
       list of row values.  If there is a single column
       the listing() list must return a list of values,
       but for multiple columns it must return a list
       of tuples with one entry for each column.
       
       The remote view implementation may optionally
       redefine __init__ also, please see gfintrospect.py
    """

    # static: don't reconstruct internal structure for each query
    # for more interesting views static will generally be 0
    static = 1
   
    def __init__(self, column_names=None, rowlist=None):
        """do whatever needed for initialization"""
        if column_names is None:
            column_names = ['a', 'b', 'c']
        if rowlist is None:
            rowlist = [(1,2,3), (4,5,6), (7,8,9)]
        self.column_names = column_names
        self.rowlist = rowlist
       
    def listing(self):
        """return list of tuples of right sizes to match column_names.
           for more interesting views this will do something more
           complex ;).
        """
        return self.rowlist
    
# create a table using default cols and rows
### Python code adding ANY remote views must be EXECUTED
### EACH TIME THE DATABASE LOADS!

g.add_remote_view("test", myTable())

# create a table using specified cols and rows
# NOTE: for single column give list of values
#   NOT list of tuples of values!
g.add_remote_view("test2", myTable(["x"], [1,6,7]))

print g.database

c = g.cursor()

c.execute("select * from test")
print "test::"
print c.pp()
print
c.execute("select * from test2")
print "test2::"
print c.pp()
print
c.execute("select * from test, test2 where x=a")
print "join"
print c.pp()
print

g.add_remote_view("test3", myTable(["z", "w"], [(2,3), (7,8), (4,6)]))
c.execute("select * from test3")
print "test3::"
print c.pp()
print

c.execute(
 "select * from test, test2, test3 where x=a and z=b and w=c")
print "join 2::"
print c.pp()
print

