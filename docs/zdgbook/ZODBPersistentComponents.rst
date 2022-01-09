##########################
ZODB Persistent Components
##########################

.. include:: includes/zope2_notice.rst

Most Zope components live in the Zope Object DataBase (ZODB).
Components that are stored in ZODB are said to be *persistent*.
Creating persistent components is, for the most part, a trivial
exercise, but ZODB does impose a few rules that persistent components
must obey in order to work properly.  This chapter describes the
persistence model and the interfaces that persistent objects can use
to live inside the ZODB.

Persistent Objects
==================

Persistent objects are Python objects that live for a long time. Most
objects are created when a program is run and die when the program
finishes. Persistent objects are not destroyed when the program ends,
they are saved in a database.

A great benefit of persistent objects is their transparency.  As a
developer, you do not need to think about loading and unloading the
state of the object from memory.  Zope's persistent machinery handles
all of that for you.

This is also a great benefit for application designers; you do not
need to create your own kind of "data format" that gets saved to a
file and reloaded again when your program stops and starts.  Zope's
persistence machinery works with *any* kind of Python objects (within
the bounds of a few simple rules) and as your types of objects grow,
your database simply grows transparently with it.

Persistence Example
-------------------

Here is a simple example of using ZODB outside of Zope.  If all you
plan on doing is using persistent objects with Zope, you can skip
this section if you wish.

The first thing you need to do to start working with ZODB is to
create a "root object".  This process involves first opening a
"storage" , which is the actual backend storage location for your
data.

ZODB supports many pluggable storage back-ends, but for the purposes
of this article we're going to show you how to use the 'FileStorage'
back-end storage, which stores your object data in a file.  Other
storages include storing objects in relational databases, Berkeley
databases, and a client to server storage that stores objects on a
remote storage server.


To set up a ZODB, you must first install it.  ZODB comes with Zope,
so the easiest way to install ZODB is to install Zope and use the
ZODB that comes with your Zope installation.  For those of you who
don't want all of Zope, but just ZODB, see its page on PyPI at
https://pypi.org/project/ZODB/.

After installing ZODB, you can start to experiment with it right from
the Python command line interpreter.  If you've installed Zope,
before running this set of commands, shut down your Zope server, and
"cd" to the "lib/python" directory of your Zope instance.  If you're
using a "standalone" version of ZODB, you likely don't need to do
this, and you'll be able to use ZODB by importing it from a standard
Python package directory.  In either case, try the following set of
commands::

  chrism@saints:/opt/zope/lib/python$ python
  Python 2.1.1 (#1, Aug  8 2001, 21:17:50) 
  [GCC 2.95.2 20000220 (Debian GNU/Linux)] on linux2
  Type "copyright", "credits" or "license" for more information. 
  >>> from ZODB import FileStorage, DB
  >>> storage = FileStorage.FileStorage('mydatabase.fs')
  >>> db = DB( storage )
  >>> connection = db.open()
  >>> root = connection.root()

Here, you create storage and use the 'mydatabse.fs' file to store the
object information.  Then, you create a database that uses that
storage.


Next, the database needs to be "opened" by calling the 'open()'
method.  This will return a connection object to the database.  The
connection object then gives you access to the 'root' of the database
with the 'root()' method.

The 'root' object is the dictionary that holds all of your persistent
objects.  For example, you can store a simple list of strings in the
root object::

      root['employees'] = ['Bob', 'Mary', 'Jo']

Now, you have changed the persistent database by adding a new object,
but this change is so far only temporary.  In order to make the
change permanent, you must commit the current transaction::

      get_transaction().commit()

Transactions are ways to make a lot of changes in one atomic
operation.  In a later article, we'll show you how this is a very
powerful feature.  For now, you can think of committing transactions
as "checkpoints" where you save the changes you've made to your
objects so far.  Later on, we'll show you how to abort those changes,
and how to undo them after they are committed.

If you had used a relational database, you would have had to issue a
SQL query to save even a simple python list like the above example.
You would have also needed some code to convert a SQL query back into
the list when you wanted to use it again.  You don't have to do any
of this work when using ZODB.  Using ZODB is almost completely
transparent, in fact, ZODB based programs often look suspiciously
simple!

Working with simple python types is useful, but the real power of
ZODB comes out when you store your own kinds of objects in the
database.  For example, consider a class that represents a employee::

  from Persistence import Persistent

  class Employee(Persistent):

      def setName(self, name):
          self.name = name


Calling 'setName' will set a name for the employee.  Now, you can put
Employee objects in your database::

  for name in ['Bob', 'Mary', 'Joe']:
      employee = Employee()
      employee.setName(name)
      root['employees'].append(employee)

  get_transaction().commit()

Don't forget to call 'commit()', so that the changes you have made so
far are committed to the database, and a new transaction is begun.

Persistent Rules
================

There are a few rules that must be followed when your objects are
persistent.

- Your objects, and their attributes, must be "pickleable".

- Your object cannot have any attributes that begin with '_p_'.

- Attributes of your object that begin with '_v_' are "volatile" and
  are not saved to the database (see next section).

- You must explicitly signal any changes made to mutable attributes
  (such as instances, lists, and dictionaries) or use persistent
  versions of mutable objects, like 'ZODB.PersistentMapping' (see
  below for more information on 'PersistentMapping'.)

In this section, we'll look at each of these special rules one by
one.

The first rules says that your objects must be pickleable.  This
means that they can be serialized into a data format with the
"pickle" module.  Most python data types (numbers, lists,
dictionaries) can be pickled.  Code objects (method, functions,
classes) and file objects (files, sockets) *cannot* be pickled.
Instances can be persistent objects if:

- They subclass 'Persistence.Persistent'

- All of their attributes are pickleable

The second rule is that none of your objects attributes can begin
with '_p_'.  For example, '_p_b_and_j' would be an illegal object
attribute.  This is because the persistence machinery reserves all of
these names for its own purposes.

The third rule is that all object attributes that begin with '_v_'
are "volatile" and are not saved to the database.  This means that as
long as the persistent object is in Zope memory cache, volatile
attributes can be used.  When the object is deactivated (removed from
memory) volatile attributes are thrown away.

Volatile attributes are useful for data that is good to cache for a
while but can often be thrown away and easily recreated.  File
connections, cached calculations, rendered templates, all of these
kinds of things are useful applications of volatile attributes. You
must exercise care when using volatile attributes.  Since you have
little control over when your objects are moved in and out of memory,
you never know when your volatile attributes may disappear.

The fourth rule is that you must signal changes to mutable types.
This is because persistent objects can't detect when mutable types
change, and therefore, doesn't know whether or not to save the
persistent object or not.

For example, say you had a list of names as an attribute of your
object called 'departments' that you changed in a method called
'addDepartment'::

  class DepartmentManager(Persistent):

      def __init__(self):
          self.departments = []

      def addDepartment(self, department):
          self.departments.append(department)

When you call the 'addDepartment' method you change a mutable type,
'departments' but your persistent object will not save that change.

There are two solutions to this problem.  First, you can assign a
special flag, '_p_changed'::

  def addDepartment(self, department):
      self.department.append(department)
      self._p_changed = 1

Remember, '_p_' attributes do something special to the persistence
machinery and are reserved names. Assigning 1 to '_p_changed' tells
the persistence machinery that you changed the object, and that it
should be saved.

Another technique is to use the mutable attribute as though it were
immutable. In other words, after you make changes to a mutable
object, reassign it::

  def addDepartment(self, department):
      departments = self.departments
      departments.append(department)
      self.department = departments

Here, the 'self.departments' attribute was re-assigned at the end of
the function to the "working copy" object 'departments'.  This
technique is cleaner because it doesn't have any explicit
'_p_changed' settings in it, but this implicit triggering of the
persistence machinery should always be understood, otherwise use the
explicit syntax.

A final option is to use persistence-aware mutable attributes such as
'PersistentMapping', and 'IOBTree'. 'PersistentMapping' is a mapping
class that notifies ZODB when you change the mapping. You can use
instances of 'PersistentMapping' in place of standard Python
dictionaries and not worry about signaling change by reassigning the
attribute or using '_p_changed'. Zope's Btree classes are also
persistent-aware mutable containers. This solution can be cleaner
than using mutable objects immutably, or signaling change manually
assuming that there is a persistence-aware class available that meets
your needs.

Transactions and Persistent Objects
===================================

When changes are saved to ZODB, they are saved in a *transaction*.
This means that either all changes are saved, or none are saved.  The
reason for this is data consistency.  Imagine the following scenario:

1. A user makes a credit card purchase at the sandwich.com website.

2. The bank debits their account.

3. An electronic payment is made to sandwich.com.

Now imagine that an error happens during the last step of this
process, sending the payment to sandwich.com.  Without transactions,
this means that the account was debited, but the payment never went
to sandwich.com!  Obviously this is a bad situation.  A better
solution is to make all changes in a transaction:

1. A user makes a credit card purchase at the sandwich.com website.

2. The transaction begins

3. The bank debits their account.

4. An electronic payment is made to sandwich.com.

5. The transaction commits

Now, if an error is raised anywhere between steps 2 and 5, *all*
changes made are thrown away, so if the payment fails to go to
sandwich.com, the account won't be debited, and if debiting the
account raises an error, the payment won't be made to sandwich.com,
so your data is always consistent.

When using your persistent objects with Zope, Zope will automatically
*begin* a transaction when a web request is made, and *commit* the
transaction when the request is finished.  If an error occurs at any
time during that request, then the transaction is *aborted*, meaning
all the changes made are thrown away.

If you want to *intentionally* abort a transaction in the middle of a
request, then just raise an error at any time.  For example, this
snippet of Python will raise an error and cause the transaction to
abort::

  raise SandwichError('Not enough peanut butter.')

A more likely scenario is that your code will raise an exception when
a problem arises. The great thing about transactions is that you
don't have to include cleanup code to catch exceptions and undo
everything you've done up to that point. Since the transaction is
aborted the changes made in the transaction will not be saved.

Because Zope does transaction management for you, most of the time
you do not need to explicitly begin, commit or abort your own
transactions.  For more information on doing transaction management
manually, see the links at the end of this chapter that lead to more
detailed tutorials of doing your own ZODB programming.


Subtransactions
---------------

Zope waits until the transaction is committed to save all the changes
to your objects.  This means that the changes are saved in memory.
If you try to change more objects than you have memory in your
computer, your computer will begin to swap and thrash, and maybe even
run you out of memory completely.  This is bad. The easiest solution
to this problem is to not change huge quantities of data in one
transaction.

If you need to spread a transaction out of lots of data, however, you
can use subtransactions.  Subtransactions allow you to manage Zope's
memory usage yourself, so as to avoid swapping during large
transactions.

Subtransactions allow you to make huge transactions. Rather than
being limited by available memory, you are limited by available disk
space.  Each subtransaction commit writes the current changes out to
disk and frees memory to make room for more changes.

To commit a subtransaction, you first need to get a hold of a
transaction object.  Zope adds a function to get the transaction
objects in your global namespace, 'get_transaction', and then call
'commit(1)' on the transaction::

  get_transaction().commit(1)

You must balance speed, memory, and temporary storage concerns when
deciding how frequently to commit subtransactions. The more
subtransactions, the less memory used, the slower the operation, and
the more temporary space used. Here's and example of how you might
use subtransactions in your Zope code::

  tasks_per_subtransaction = 10
  i = 0
  for task in tasks:
      process(task)
      i = i + 1
      if i % tasks_per_subtransaction == 0:
          get_transaction().commit(1)

This example shows how to commit a subtransaction at regular
intervals while processing a number of tasks.

Threads and Conflict Errors
---------------------------

Zope is a multi-threaded server.  This means that many different
clients may be executing your Python code in different threads.  For
most cases, this is not an issue and you don't need to worry about
it, but there are a few cases you should look out for.

The first case involves threads making lots of changes to objects and
writing to the database.  The way ZODB and threading works is that
each thread that uses the database gets its own *connection* to the
database.  Each connection gets its own *copy* of your object.  All
of the threads can read and change any of the objects.  ZODB keeps
all of these objects synchronized between the threads. The upshot is
that you don't have to do any locking or thread synchronization
yourself. Your code can act as though it is single threaded.

However, synchronization problems can occur when objects are changed
by two different threads at the same time.

Imagine that thread 1 gets its own copy of object A, as does thread
2.  If thread 1 changes its copy of A, then thread 2 will not see
those changes until thread 1 commits them.  In cases where lots of
objects are changing, this can cause thread 1 and 2 to try and commit
changes to object 1 at the same time.

When this happens, ZODB lets one transaction do the commit (it
"wins") and raises a 'ConflictError' in the other thread (which
"looses"). The looser can elect to try again, but this may raise yet
another 'ConflictError' if many threads are trying to change object
A. Zope does all of its own transaction management and will retry a
losing transaction three times before giving up and raising the
'ConflictError' all the way up to the user.


Resolving Conflicts
-------------------

If a conflict happens, you have two choices. The first choice is that
you live with the error and you try again. Statistically, conflicts
are going to happen, but only in situations where objects are
"hot-spots".  Most problems like this can be "designed away"; if you
can redesign your application so that the changes get spread around
to many different objects then you can usually get rid of the hot
spot.


Your second choice is to try and *resolve* the conflict. In many
situations, this can be done. For example, consider the following
persistent object::

  class Counter(Persistent):

      self.count = 0

      def hit(self):
          self.count = self.count + 1

This is a simple counter.  If you hit this counter with a lot of
requests though, it will cause conflict errors as different threads
try to change the count attribute simultaneously.

But resolving the conflict between conflicting threads in this case
is easy.  Both threads want to increment the self.count attribute by
a value, so the resolution is to increment the attribute by the sum
of the two values and make both commits happy; no 'ConflictError' is
raised.


To resolve a conflict, a class should define an '_p_resolveConflict'
method. This method takes three arguments.

'oldState' -- The state of the object that the changes made by the
current transaction were based on. The method is permitted to modify
this value.

'savedState' -- The state of the object that is currently stored in
the database. This state was written after 'oldState' and reflects
changes made by a transaction that committed before the current
transaction. The method is permitted to modify this value.

'newState' -- The state after changes made by the current
transaction.  The method is *not* permitted to modify this
value. This method should compute a new state by merging changes
reflected in 'savedState' and 'newState', relative to 'oldState'.

The method should return the state of the object after resolving the
differences.

Here is an example of a '_p_resolveConflict' in the 'Counter' class::

  class Counter(Persistent):

      self.count = 0

      def hit(self):
          self.count = self.count + 1

      def _p_resolveConflict(self, oldState, savedState, newState):

          # Figure out how each state is different:
          savedDiff= savedState['count'] - oldState['count']
          newDiff= newState['count']- oldState['count']

          # Apply both sets of changes to old state:
          oldState['count'] = oldState['count'] + savedDiff + newDiff

          return oldState

In the above example, '_p_resolveConflict' resolves the difference
between the two conflicting transactions.

Threadsafety of Non-Persistent Objects
======================================

ZODB takes care of threadsafety for persistent objects. However, you
must handle threadsafey yourself for non-persistent objects which are
shared between threads.

Mutable Default Arguments
-------------------------

One tricky type of non-persistent, shared objects are mutable default
arguments to functions, and methods.  Default arguments are useful
because they are cached for speed, and do not need to be recreated
every time the method is called.  But if these cached default
arguments are mutable, one thread may change (mutate) the object when
another thread is using it, and that can be bad.  So, code like::

        def foo(bar=[]):
            bar.append('something')


Could get in trouble if two threads execute this code because lists
are mutable.  There are two solutions to this problem:

- Don't use mutable default arguments. (Good)

- If you use them, you cannot change them.  If you want to change
  them, you will need to implement your own locking. (Bad)

We recommend the first solution because mutable default arguments are
confusing, generally a bad idea in the first place.

Shared Module Data
------------------

Objects stored in modules but not in the ZODB are not persistent and
not-thread safe. In general it's not a good idea to store data (as
opposed to functions, and class definitions) in modules when using
ZODB.


If you decide to use module data which can change you'll need to
protect it with a lock to ensure that only one thread at a time can
make changes.


For example::

  from threading import Lock
  queue=[]
  l=Lock()

  def put(obj):
      l.acquire()
      try:
          queue.append(obj)
      finally:
          l.release()

  def get():
      l.acquire()
      try:
          return queue.pop()
      finally:
          l.release()

Note, in most cases where you are tempted to use shared module data,
you can likely achieve the same result with a single persistent
object. For example, the above queue could be replaced with a single
instance of this class::

  class Queue(Persistent):

      def __init__(self):
          self.list=[]

      def put(self, obj):
          self.list=self.list + [obj]

      def get(self):
          obj=self.list[-1]
          self.list=self.list[0:-1]
          return obj

Notice how this class uses the mutable object 'self.list'
immutably. If this class used 'self.list.pop' and 'self.list.append',
then the persistence machinary would not notice that 'self.list' had
changed.

Shared External Resources
=========================

A final category of data for which you'll need to handle
thread-safety is external resources such as files in the filesystem,
and other processes. In practice, these concerns rarely come up.

Other ZODB Resources
====================

This chapter has only covered the most important features of ZODB
from a Zope developer's perspective. Check out some of these sources
for more in depth information:

- The main ZODB documentation site at https://zodb.org/.

- `ZODB UML
  Model <https://old.zope.dev/Documentation/Developer/Models/ZODB/>`_ has
  the nitty gritty details on ZODB.

Summary
=======

The ZODB is a complex and powerful system. However using persistent
objects is almost completely painless. Seldom do you need to concern
yourself with thread safety, transactions, conflicts, memory
management, and database replication. ZODB takes care of these things
for you. By following a few simple rules you can create persistent
objects that just work.
