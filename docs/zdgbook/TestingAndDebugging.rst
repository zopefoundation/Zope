#####################
Testing and Debugging
#####################

.. include:: includes/zope2_notice.rst

As you develop Zope applications you may run into problems.  This
chapter covers debugging and testing techniques that can help you.
The Zope debugger allow you to peek inside a running process and find
exactly what is going wrong.  Unit testing allows you to automate the
testing process to ensure that your code still works correctly as you
change it.  Finally, Zope provides logging facilities which allow you
to emit warnings and error messages.


Debugging
=========

Zope provides debugging information through a number of sources.  It
also allows you a couple avenues for getting information about Zope
as it runs.

Product Refresh Settings
------------------------

As of Zope 2.4 there is a *Refresh* view on all Control Panel
Products.  Refresh allows you to reload your product's modules as you
change them, rather than having to restart Zope to see your changes.
The *Refresh* view provides the same debugging functionality
previously provided by Shane Hathaway's Refresh Product.

To turn on product refresh capabilities place a 'refresh.txt' file in
your product's directory.  Then visit the *Refresh* view of your
product in the management interface.  Here you can manually reload
your product's modules with the *Refresh this product* button.  This
allows you to immediately see the effect of your changes, without
restarting Zope.  You can also turn on automatic refreshing which
causes Zope to frequently check for changes to your modules and
refresh your product when it detects that your files have changed.
Since automatic refresh causes Zope to run more slowly, it is a good
idea to only turn it on for a few products at a time.

Debug Mode
----------

Normally, debug mode is set using the '-D' switch when starting Zope.
This mode reduces the performance of Zope a little bit.  Debug model
has a number of wide ranging effects:

- Tracebacks are shown on the browser when errors are raised.

- External Methods and DTMLFile objects are checked to see if they
  have been modified every time they are called.  If modified, they
  are reloaded.

- Zope will not fork into the background in debug mode, instead, it
  will remain attached to the terminal that started it and the main
  logging information will be redirected to that terminal.

By using debug mode and product refresh together you will have little
reason to restart Zope while developing.

The Python Debugger
-------------------

Zope is integrated with the Python debugger (pdb).  The Python
debugger is pretty simple as command line debuggers go, and anyone
familiar with other popular command line debuggers (like gdb) will
feel right at home in pdb.

For an introduction to pdb see the standard `pdb documentation
<https://docs.python.org/library/pdb.html>`_ .

There are a number of ways to debug a Zope process:

  o You can shut down the Zope server and simulate a request on the
    command line.

  o You can run a special ZEO client that debugs a running server.

  o You can run Zope in debug model and enter the debugger
    through Zope's terminal session.

The first method is an easy way to debug Zope if you are not running
ZEO.  First, you must first shut down the Zope process.  It is not
possible to debug Zope in this way and run it at the same time.
Starting up the debugger this way will by default start Zope in
single threaded mode.

For most Zope developer's purposes, the debugger is needed to debug
some sort of application level programming error.  A common scenario
is when developing a new product for Zope.  Products extend Zope's
functionality but they also present the same kind of debugging
problems that are commonly found in any programming environment.  It
is useful to have an existing debugging infrastructure to help you
jump immediately to your new object and debug it and play with it
directly in pdb.  The Zope debugger lets you do this.

In reality, the "Zope" part of the Zope debugger is actually just a
handy way to start up Zope with some pre-configured break points and
to tell the Python debugger where in Zope you want to start
debugging.

Simulating HTTP Requests
~~~~~~~~~~~~~~~~~~~~~~~~

Now for an example. Remember, for this example to work, you *must*
shut down Zope.  Go to your Zope's 'lib/python' directory and fire up
Python and import 'Zope' and 'ZPublisher'::

  $ cd lib/python
  $ python
  Python 1.5.2 (#0, Apr 13 1999, 10:51:12) [MSC 32 bit (Intel)] on win32
  Copyright 1991-1995 Stichting Mathematisch Centrum, Amsterdam
  >>> import Zope, ZPublisher
  >>>

Here you have run the Python interpreter (which is where using the
debugger takes place) and imported two modules, 'Zope' and
'ZPublisher'.  If Python complains about an 'ImportError' and not
being able to find either module, then you are probably in the wrong
directory, or you have not compiled Zope properly.  If you get this
message::

  ZODB.POSException.StorageSystemError: Could not lock the database
  file.  There must be another process that has opened the file.

This tells you that Zope is currently running.  Shutdown Zope and try
again.

The 'Zope' module is the main Zope application module.  When you
import 'Zope' it sets up Zope.  'ZPublisher' is the Zope ORB.  See
Chapter 2 for more information about 'ZPublisher'.

You can use the 'ZPublisher.Zope' function to simulate an HTTP
request.  Pass the function a URL relative the your root Zope object.
Here is an example of how to simulate an HTTP request from the
debugger::

  >>> ZPublisher.Zope('')
  Status: 200 OK
  X-Powered-By: Zope (www.zope.dev), Python (www.python.org)
  Content-Length: 1238
  Content-Type: text/html

  <HTML><HEAD><TITLE>Zope</TITLE>

    ... blah blah...

  </BODY></HTML>
  >>>

If you look closely, you will see that the content returned is
*exactly* what is returned when you call your root level object
through HTTP, including all the HTTP headers.

Keep in mind that calling Zope this way does NOT involve a web
server.  No ports are opened.
In fact, this is just an interpreter front end to the same
application code the WSGI server *does* call.

Interactive Debugging
~~~~~~~~~~~~~~~~~~~~~

Debugging involves publishing a request up to a point where you think
it's failing, and then inspecting the state of your variables and
objects.  The easy part is the actual inspection, the hard part is
getting your program to stop at the right point.

So, for the sake our example, let's say that you have a 'News' object
which is defined in a Zope Product called 'ZopeNews', and is located
in the 'lib/python/Products/ZopeNews' directory.  The class that
defines the 'News' instance is also called 'News', and is defined in
the 'News.py' module in your product.

Therefore, from Zope's perspective the fully qualified name of your
class is 'Products.ZopeNews.News.News'.  All Zope objects have this
kind of fully qualified name.  For example, the 'ZCatalog' class can
be found in 'Products.ZCatalog.ZCatalog.ZCatalog' (The redundancy is
because the product, module, and class are all named 'ZCatalog').

Now let's create an example method to debug.  You want your news
object to have a 'postnews' method, that posts news::

  class News(...):

      ...

      def postnews(self, news, author="Anonymous"):
          self.news = news

      def quote(self):
          return '%s said, "%s"' % (self.author, self.news)

You may notice that there's something wrong with the 'postnews'
method.  The method assigns 'news' to an instance variable, but it
does nothing with 'author'.  If the 'quote' method is called, it will
raise an 'AttributeError' when it tries to look up the name
'self.author'.  Although this is a pretty obvious goof, we'll use it
to illustrate using the debugger to fix it.

Running the debugger is done in a very similar way to how you called
Zope through the python interpreter before, except that you introduce
one new argument to the call to 'Zope'::

  >>> ZPublisher.Zope('/News/postnews?new=blah', d=1)
  * Type "s<cr>c<cr>" to jump to beginning of real publishing process.
  * Then type c<cr> to jump to the beginning of the URL traversal
    algorithm.
  * Then type c<cr> to jump to published object call.
  > <string>(0)?()
  pdb>

Here, you call Zope from the interpreter, just like before, but there
are two differences.  First, you call the 'postnews' method with an
argument using the URL, '/News/postnews?new=blah'.  Second, you
provided a new argument to the Zope call, 'd=1'.  The 'd' argument,
when true, causes Zope to fire up in the Python debugger, pdb.
Notice how the Python prompt changed from '>>>' to 'pdb>'.  This
indicates that you are in the debugger.

When you first fire up the debugger, Zope gives you a helpful message
that tells you how to get to your object.  To understand this
message, it's useful to know how you have set Zope up to be debugged.
When Zope fires up in debugger mode, there are three breakpoints set
for you automatically (if you don't know what a breakpoint is, you
need to read the python `debugger documentation
<https://docs.python.org/library/pdb.html>`_).

The first breakpoint stops the program at the point that ZPublisher
(the Zope ORB) tries to publish the application module (in this case,
the application module is 'Zope').  The second breakpoint stops the
program right before ZPublisher tries to traverse down the provided
URL path (in this case, '/News/postnews').  The third breakpoint will
stop the program right before ZPublisher calls the object it finds
that matches the URL path (in this case, the 'News' object).

So, the little blurb that comes up and tells you some keys to press
is telling you these things in a terse way.  Hitting 's' will *step*
you into the debugger, and hitting 'c' will *continue* the execution
of the program until it hits a breakpoint.

Note however that none of these breakpoints will stop the program at
'postnews'.  To stop the debugger right there, you need to tell the
debugger to set a new breakpoint.  Why a new breakpoint?  Because
Zope will stop you before it traverse your objects path, it will stop
you before it calls the object, but if you want to stop it *exactly*
at some point in your code, then you have to be explicit.  Sometimes
the first three breakpoints are convienent, but often you need to set
your own special break point to get you exactly where you want to go.

Setting a breakpoint is easy (and see the next section for an even
easier method).  For example::

  pdb> import Products
  pdb> b Products.ZopeNews.News.News.postnews
  Breakpoint 5 at C:\Program Files\WebSite\lib\python\Products\ZopeNews\News.py:42
  pdb>

First, you import 'Products'.  Since your module is a Zope product,
it can be found in the 'Products' package.  Next, you set a new
breakpoint with the *break* debugger command (pdb allows you to use
single letter commands, but you could have also used the entire word
'break').  The breakpoint you set is
'Products.ZopeNews.News.News.postnews'.  After setting this
breakpoint, the debugger will respond that it found the method in
question in a certain file, on a certain line (in this case, the
fictitious line 42) and return you to the debugger.

Now, you want to get to your 'postnews' method so you can start
debugging it.  But along the way, you must first *continue* through
the various breakpoints that Zope has set for you.  Although this may
seem like a bit of a burden, it's actually quite good to get a feel
for how Zope works internally by getting down the rhythm that Zope
uses to publish your object.  In these next examples, my comments
will begin with '#".  Obviously, you won't see these comments when
you are debugging.  So let's debug::

  pdb> s
  # 's'tep into the actual debugging

  > <string>(1)?()
  # this is pdb's response to being stepped into, ignore it

  pdb> c
  # now, let's 'c'ontinue onto the next breakpoint

  > C:\Program Files\WebSite\lib\python\ZPublisher\Publish.py(112)publish()
  -> def publish(request, module_name, after_list, debug=0,

  # pdb has stopped at the first breakpoint, which is the point where
  # ZPubisher tries to publish the application module.

  pdb> c
  # continuing onto the next breakpoint you get...

  > C:\Program Files\WebSite\lib\python\ZPublisher\Publish.py(101)call_object()
  -> def call_object(object, args, request):

Here, 'ZPublisher' (which is now publishing the application) has
found your object and is about to call it.  Calling your object
consists of applying the arguments supplied by 'ZPublisher' to the
object.  Here, you can see how 'ZPublisher' is passing three
arguments into this process.  The first argument is 'object' and is
the actual object you want to call.  This can be verified by
*printing* the object::

  pdb> p object
  <News instance at 00AFE410>

Now you can inspect your object (with the *print* command) and even
play with it a bit.  The next argument is 'args'.  This is a tuple of
arguments that 'ZPublisher' will apply to your object call.  The
final argument is 'request'.  This is the request object and will
eventually be transformed in to the DTML usable object 'REQUEST'. Now
continue, your breakpoint is next::

  pdb> c
  > C:\Program Files\WebSite\lib\python\Products\ZopeNews\News.py(42)postnews()
  -> def postnews(self, N)

Now you are here, at your method.  To be sure, tell the debugger to
show you where you are in the code with the 'l' command.  Now you can
examine variable and perform all the debugging tasks that the Python
debugger provides.  From here, with a little knowledge of the Python
debugger, you should be able to do any kind of debugging task that is
needed.

Interactive Debugging Triggered From the Web
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are running in debug mode you can set break points in your
code and then jump straight to the debugger when Zope comes across
your break points.  Here's how to set a breakpoint::

  import pdb;pdb.set_trace()

Now start Zope in debug mode and point your web browser at a URL that
causes Zope to execute the method that includes a breakpoint.  When
this code is executed, the Python debugger will come up in the
terminal where you started Zope.  Also note that from your web
browser it looks like Zope is frozen.  Really it's just waiting for
you do your debugging.

From the terminal you are inside the debugger as it is executing your
request.  Be aware that you are just debugging one thread in Zope,
and other requests may be being served by other threads.  If you go
to the *Debugging Info* screen while in the debugger, you can see
your debugging request and how long it has been open.

It is often more convenient to use this method to enter the debugger
than it is to call 'ZPublisher.Zope' as detailed in the last section.

Post-Mortem Debugging
~~~~~~~~~~~~~~~~~~~~~

Often, you need to use the debugger to chase down obscure problems in
your code, but sometimes, the problem is obvious, because an
exception gets raised.  For example, consider the following method on
your 'News' class::

  def quote(self):
      return '%s said, "%s"' % (self.Author, self.news)

Here, you can see that the method tries to substitute 'self.Author'
in a string, but earlier we saw that this should really be
'self.author'.  If you tried to run this method from the command
line, an exception would be raised::

  >>> ZPublisher.Zope('/News/quote')
  Traceback (most recent call last):
    File "<stdin>", line 1, in ?
    File "./News.py", line 4, in test
      test2()
    File "./News.py", line 3, in test2
      return '%s said, "%s"' % (self.Author, self.news)
  NameError: Author
  >>>

Using Zope's normal debugging methods, you would typically need to
start from the "beginning" and step your way down through the
debugger to find this error (in this case, the error is pretty
obvious, but more often than not errors can be pretty obscure!).

Post-mortem debugging allows you to jump *directly* to the spot in
your code that raised the exception, so you do not need to go through
the possibly tedious task of stepping your way through a sea of
Python code.  In the case of our example, you can just pass
'ZPublisher.Zope' call a 'pm' argument that is set to 1::

          >>> ZPublisher.Zope('/News/quote', pm=1)
          Traceback (most recent call last):
            File "<stdin>", line 1, in ?
            File "./News.py", line 4, in test
              test2()
            File "./News.py", line 3, in test2
              return '%s said, "%s"' % (self.Author, self.news)
          NameError: Author
          (pdb)

Here, you can see that instead of taking you back to a python prompt,
the post mortem debugging flag has caused you to go right into the
debugging, *exactly* at the point in your code where the exception is
raised.  This can be verified with the debugger's (l)ist
command. Post mortem debugging offers you a handy way to jump right
to the section of your code that is failing in some obvious way by
raising an exception.

Debugging With ZEO
~~~~~~~~~~~~~~~~~~

ZEO presents some interesting debugging abilities.  ZEO lets you
debug one ZEO client when other clients continue to server requests
for your site.  In the above examples, you have to shut down Zope to
run in the debugger, but with ZEO, you can debug a production site
while other clients continue to serve requests. Using ZEO is beyond
the scope of this chapter. However, once you have ZEO running, you
can debug a client process exactly as you debug a single-process
Zope.


Unit Testing
============

Unit testing allows you to automatically test your classes to make
sure they are working correctly. By using unit tests you can make
sure as you develop and change your classes that you are not breaking
them. Zope's own unit tests are written using the built-in Python
`unittest module <https://docs.python.org/library/unittest.html>`_.


What Are Unit Tests
-------------------

A "unit" may be defined as a piece of code with a single intended
purpose.  A "unit test" is defined as a piece of code which exists
to codify the intended behavior of a unit and to compare its
intended behavior against its actual behavior.

Unit tests are a way for developers and quality assurance engineers
to quickly ascertain whether independent units of code are working as
expected.  Unit tests are generally written at the same time as the
code they are intended to test.  A unit testing framework allows a
collection of unit tests to be run without human intervention,
producing a minimum of output if all the tests in the collection are
successful.

It's a good idea to have a sense of the limits of unit testing.  From
the `Extreme Programming Enthusiast website
<http://wiki.c2.com/?UnitTestsDefined>`_ here is a list of things
that unit tests are *not*:

- Manually operated.

- Automated screen-driver tests that simulate user input (these are
  "functional tests").

- Interactive.  They run "no questions asked."

- Coupled.  They run without dependencies except those native to the
  thing being tested.

- Complicated.  Unit test code is typically straightforward
  procedural code that simulates an event.

Writing Unit Tests
------------------

Here are the times when you should write unit tests:

* When you write new code

* When you change and enhance existing code

* When you fix bugs

It's much better to write tests when you're working on code than to
wait until you're all done and then write tests.

You should write tests that exercise discrete "units" of
functionality.  In other words, write simple, specific tests that
test one capability.  A good place to start is with interfaces and
classes.  Classes and especially interfaces already define units of
work which you may wish to test.

Since you can't possibly write tests for every single capability and
special case, you should focus on testing the riskiest parts of your
code.  The riskiest parts are those that would be the most disastrous
if they failed.  You may also want to test particularly tricky or
frequently changed things.

Here's an example test script that tests the 'News' class defined
earlier in this chapter::

  import unittest
  import News

  class NewsTest(unittest.TestCase):

      def testPost(self):
          n=News()
          s='example news'
          n.postnews(s)
          assert n.news==s

      def testQuote(self):
          n=News()
          s='example news'
          n.postnews(s)
          assert n.quote()=='Anonymous said: "%s"' % s
          a='Author'
          n.postnews(s, a)
          assert n.quote()=='%s said: "%s"' % (a, s)

  def test_suite():
     return unittest.makeSuite(NewsTest, 'news test')

  def main():
     unittest.TextTestRunner().run(test_suite())

  if __name__=="__main__":
      main()

You should save tests inside a 'tests' sub-directory in your
product's directory. Test scripts file names should start with test,
for example 'testNews.py'. You may accumulate many test scripts in
your product's 'tests' directory.  You can run test your product by
running the test scripts.

We cannot cover all there is to say about unit testing here. Take a
look at the `unittest module documentation
<https://docs.python.org/library/unittest.html>`_ for more background on
unit testing.

Zope Test Fixtures
------------------

One issue that you'll run into when unit testing is that you may need
to set up a Zope environment in order to test your products.  You can
solve this problem in two ways.  First, you can structure your
product so that much of it can be tested without Zope (as you did in
the last section).  Second, you can create a test fixture that sets
up a Zope environment for testing.

To create a test fixture for Zope you'll need to:

1. Add Zope's 'lib/python' directory to the Python path.

2. Import 'Zope' and any other needed Zope modules and packages.

3. Get a Zope application object.

4. Do your test using the application object.

5. Clean up the test by aborting or committing the transaction and
   closing the Zope database connection.

Here's an example Zope test fixture that demonstrates how to do each
of these steps::

  import os, os.path, sys, string
  try:
      import unittest
  except ImportError:
      fix_path()
      import unittest

  class MyTest(unittest.TestCase):

      def setUp(self):
          # Get the Zope application object and store it in an
          # instance variable for use by test methods
          import Zope
          self.app=Zope.app()

      def tearDown(self):
          # Abort the transaction and shut down the Zope database
          # connection.
          get_transaction().abort()
          self.app._p_jar.close()

      # At this point your test methods can perform tests using
      # self.app which refers to the Zope application object.

      ...

  def fix_path():
      # Add Zope's lib/python directory to the Python path
      file=os.path.join(os.getcwd(), sys.argv[0])
      dir=os.path.join('lib', 'python')
      i=string.find(file, dir)
      sys.path.insert(0, file[:i+len(dir)])

  def test_suite():
     return unittest.makeSuite(MyTest, 'my test')

  def main():
     unittest.TextTestRunner().run(test_suite())

  if __name__=="__main__":
      fix_path()
      main()

This example shows a fairly complete Zope test fixture.  If your Zope
tests only needs to import Zope modules and packages you can skip
getting a Zope application object and closing the database
transaction.

Some times you may run into trouble if your test assuming that there
is a current Zope request.  There are two ways to deal with this.
One is to use the 'makerequest' utility module to create a fake
request.  For example::

  class MyTest(unittest.TestCase):
      ...

      def setup(self):
          import Zope
          from Testing import makerequest
          self.app=makerequest.makerequest(Zope.app())

This will create a Zope application object that is wrapped in a
request.  This will enable code that expects to acquire a 'REQUEST'
attribute work correctly.

Another solution to testing methods that expect a request is to use
the 'ZPublisher.Zope' function described earlier.  Using this
approach you can simulate HTTP requests in your unit tests.  For
example::

  import ZPublisher

  class MyTest(unittest.TestCase):
      ...

      def testWebRequest(self):
          ZPublisher.Zope('/a/url/representing/a/method?with=a&couple=arguments',
                          u='username:password',
                          s=1,
                          e={'some':'environment', 'variable':'settings'})

If the 's' argument is passed to 'ZPublisher.Zope' then no output
will be sent to 'sys.stdout'.  If you want to capture the output of
the publishing request and compare it to an expected value you'll
need to do something like this::

  f=StringIO()
  temp=sys.stdout
  sys.stdout=f
  ZPublisher.Zope('/myobject/mymethod')
  sys.stdout=temp
  assert f.getvalue() == expected_output

Here's a final note on unit testing with a Zope test fixture: you may
find Zope helpful.  ZEO allows you to test an application while it
continues to serve other users.  It also speeds Zope start up time
which can be a big relief if you start and stop Zope frequently while
testing.

Despite all the attention we've paid to Zope testing fixtures, you
should probably concentrate on unit tests that don't require a Zope
test fixture.  If you can't test much without Zope there is a good
chance that your product would benefit from some refactoring to make
it simpler and less dependent on the Zope framework.

Logging
=======

Zope provides a framework for logging information to Zope's
application log.  You can configure Zope to write the application log
to a file, syslog, or other back-end.

The logging API defined in the 'zLOG' module.  This module provides
the 'LOG' function which takes the following required arguments:

- subsystem -- The subsystem generating the message (e.g. "ZODB")

- severity -- The "severity" of the event.  This may be an integer or
  a floating point number.  Logging back ends may consider the int()
  of this value to be significant.  For example, a back-end may
  consider any severity whose integer value is WARNING to be a
  warning.

- summary -- A short summary of the event

These arguments to the 'LOG' function are optional:

- detail -- A detailed description

- error -- A three-element tuple consisting of an error type, value,
  and traceback.  If provided, then a summary of the error is added
  to the detail.

- reraise -- If provided with a true value, then the error given by
  error is reraised.

You can use the 'LOG' function to send warning and errors to the Zope
application log.

Here's an example of how to use the 'LOG' function to write debugging
messages::

  from zLOG import LOG, DEBUG
  LOG('my app', DEBUG, 'a debugging message')

You can use 'LOG' in much the same way as you would use print
statements to log debugging information while Zope is running.  You
should remember that Zope can be configured to ignore log messages
below certain levels of severity.  If you are not seeing your logging
messages, make sure that Zope is configured to write them to the
application log.

In general the debugger is a much more powerful way to locate
problems than using the logger.  However, for simple debugging tasks
and for issuing warnings the logger works just fine.

Other Testing and Debugging Facilities
======================================

There is a few other testing and debugging techniques and tools not
commonly used to test Zope.  In this section we'll mention several of
them.

Debug Logging
-------------

Zope provides an analysis tool for debugging log output.  This output
allows may give you hints as to where your application may be
performing poorly, or not responding at all.  For example, since
writing Zope products lets your write unrestricted Python code, it's
very possibly to get yourself in a situation where you "hang" a Zope
request, possibly by getting into a infinite loop.

To try and detect at which point your application hangs, use the
*requestprofiler.py* script in the *utilities* directory of your Zope
installation.  To use this script, you must run Zope with the '-M'
command line option.  This will turn on "detailed debug logging" that
is necessary for the *requestprofiler.py* script to run.  The
*requestprofiler.py* script has quite a few options which you can
learn about with the '--help' switch.

In general debug log analysis should be a last resort.  Use it when
Zope is hanging and normal debugging and profiling is not helping you
solve your problem.

HTTP Benchmarking
-----------------

HTTP load testing is notoriously inaccurate.  However, it is useful
to have a sense of how many requests your server can support.  Zope
does not come with any HTTP load testing tools, but there are many
available.  Apache's 'ab' program is a widely used free tool that can
load your server with HTTP requests.

Summary
=======

Zope provides a number of different debugging and testing facilities.
The debugger allows you to interactively test your applications.
Unit tests allow help you make sure that your application is develops
correctly.  The logger allows you to do simple debugging and issue
warnings.
