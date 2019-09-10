Zope Services
=============

.. include:: includes/zope2_notice.rst

Some Zope objects are *service* objects.  *Service* objects provide
various kinds of support to your "domain-specific" content, logic,
and presentation objects.  They help solve fundamental problems that
many others have experienced when writing applications in Zope.

Access Rule Services
--------------------

*Access Rules* make it possible to cause an action to happen any
time a user "traverses" a Folder in your Zope site.  When a user's
browser submits a request for a URL to Zope which has a Folder's
name in it, the Folder is "looked up" by Zope during object
publishing.  That action (the lookup) is called *traversal*.
Access Rules are arbitrary bits of code which effect the
environment in some way during Folder traversal.  They are easiest
to explain by way of an example.

.. note:::

   The Access Service section needs an explanation of how to suppress
   an access rule. For the baffled among us, you can set an environmental
   variable 'SUPPRESS_ACCESSRULE' ( I add a line in my 'start' script to
   do this ) or include '_SUPPRESS_ACCESSRULE' to the URL at a point AFTER
   the folder/container in question.
   SITEROOT works the same way, just replace ACCESSRULE with SITEROOT in
   the above explanation.

In your Zope site, create a Folder named "accessrule_test".
Inside the accessrule_test folder, create a Script (Python) object
named 'access_rule' with two parameters: 'container' and
'request'.  Give the 'access_rule' Script (Python) the following
body::

  useragent = request.get('HTTP_USER_AGENT', '')
  if useragent.find('Windows') != -1:
      request.set('OS', 'Windows')
  elif useragent.find('Linux') != -1:
      request.set('OS', 'Linux')
  else:
      request.set('OS', 'Non-Windows, Non-Linux')

This Script causes the traversal of the accessrule_test folder to
cause a new variable named 'OS' to be entered into the REQUEST,
which has a value of 'Windows', 'Linux', or 'Non-Windows,
Non-Linux' depending on the user's browser.

Save the 'access_rule' script and revisit the accessrule_test
folder's *Contents* view.  Choose *Set Access Rule* from the add
list.  In the 'Rule Id' form field, type 'access_rule'.  Then
click *Set Rule*.  A confirmation screen appears claiming that
"'access_rule' is now the Access Rule for this object".  Click
"OK".  Notice that the icon for the 'access_rule' Script (Python)
has changed, denoting that it is now the access rule for this
Folder.

Create a page template named 'test' in the accessrule_test folder
with the following text::

  <html>
  <body>
    <pre tal:content="context/REQUEST">request details</pre>
  </body>
  </html>

Save the 'test' page template and click its "View" tab.  You will
see a representation of all the variables that exist in the
REQUEST.  Note that in the **other** category, there is now a
variable named "OS" with (depending on your browser platform)
either 'Windows', 'Linux' or 'Non-Linux, Non-Windows').

Revisit the accessrule_test folder and again select *Set Access
Rule* from the add list.  Click the *No Access Rule* button.  A
confirmation screen will be displayed stating that the object now
has no Access Rule.

Visit the 'test' script you created previously and click its
*View* tab.  You will notice that there is now no "OS" variable
listed in the request because we've turned off the Access Rule
capability for 'access_rule'.

Temporary Storage Services
--------------------------

Temporary Folders are Zope folders that are used for storing
objects temporarily.  Temporary Folders acts almost exactly like a
regular Folder with two significant differences:

1. Everything contained in a Temporary Folder disappears when you
   restart Zope.  (A Temporary Folder's contents are stored in
   RAM).

2. You cannot undo actions taken to objects stored a Temporary
   Folder.

By default there is a Temporary Folder in your root folder named
*temp_folder*.  You may notice that there is an object entitled,
"Session Data Container" within *temp_folder*. This is an object
used by Zope's default sessioning system configuration.  See the
"Using Sessions" section later in this chapter for more
information about sessions.

Temporary folders store their contents in RAM rather than in the
Zope database. This makes them appropriate for storing small
objects that receive lots of writes, such as session data.
However, it's a bad idea use temporary folders to store large
objects because your computer can potentially run out of RAM as
a result.

Caching Services
----------------

A *cache* is a temporary place to store information that you
access frequently.  The reason for using a cache is speed.  Any
kind of dynamic content, like a a Script (Python),
must be evaluated each time it is called.  For simple pages or
quick scripts, this is usually not a problem.  For very complex
scripts that do a lot of computation or call remote
servers, accessing that page or script could take more than a
trivial amount of time.  Scripts can get this
complex, especially if you use lots of looping (such as the
Python 'for' loop) or if you call lots of scripts, that
in turn call lots of scripts, and so on.  Computations that take a
lot of time are said to be *expensive*.

A cache can add a lot of speed to your site by calling an
expensive page or script once and storing the result of that call
so that it can be reused.  The very first person to call that page
will get the usual "slow" response time, but then once the value
of the computation is stored in the cache, all subsequent users to
call that page will see a very quick response time because they
are getting the *cached copy* of the result and not actually going
through the same expensive computation the first user went
through.

To give you an idea of how caches can improve your site speed,
imagine that you are creating *www.zopezoo.org*, and that the very
first page of your site is very complex.  Let's suppose this page
has complex headers, footers, queries several different database
tables, and calls several special scripts that parse the results
of the database queries in complex ways.  Every time a user comes
to *www.zopezoo.org*, Zope must render this very complex page.
For the purposes of demonstration, let's suppose this complex page
takes one-half of a second, or 500 milliseconds, to compute.

Given that it takes a half of a second to render this fictional
complex main page, your machine can only really serve 120 hits per
minute.  In reality, this number would probably be even lower than
that, because Zope has to do other things in addition to just
serving up this main page.  Now, imagine that you set this page up
to be cached.  Since none of the expensive computation needs to be
done to show the cached copy of the page, many more users could
see the main page.  If it takes, for example, 10 milliseconds to
show a cached page, then this page is being served *50 times
faster* to your website visitors.  The actual performance of the
cache and Zope depends a lot on your computer and your
application, but this example gives you an idea of how caching can
speed up your website quite a bit.  There are some disadvantages
to caching however:

Cache lifetime
  If pages are cached for a long time, they may
  not reflect the most current information on your site.  If you
  have information that changes very quickly, caching may hide the
  new information from your users because the cached copy contains
  the old information.  How long a result remains cached is called
  the *cache lifetime* of the information.

Personal information
  Many web pages may be personalized for
  one particular user.  Obviously, caching this information and
  showing it to another user would be bad due to privacy concerns,
  and because the other user would not be getting information
  about *them*, they'd be getting it about someone else.  For this
  reason, caching is often never used for personalized
  information.

Zope allows you to get around these problems by setting up a *cache
policy*.  The cache policy allows you to control how content gets
cached.  Cache policies are controlled by *Cache Manager* objects.

Adding a Cache Manager
~~~~~~~~~~~~~~~~~~~~~~

Cache managers can be added just like any other Zope object.
Currently Zope comes with two kinds of cache managers:

HTTP Accelerated Cache Manager
  An HTTP Accelerated Cache Manager allows you to control an HTTP cache
  server that is external to Zope, for example,
  `Squid <http://www.squid-cache.org/>`_.  HTTP Accelerated Cache Managers
  do not do the caching themselves, but rather set special HTTP headers
  that tell an external cache server what to cache.  Setting up an external
  caching server like Squid is beyond the scope of this book, see the Squid
  site for more details.

(RAM) Cache Manager
  A RAM Cache Manager is a Zope cache manager that caches the content of
  objects in your computer memory.  This makes it very fast, but also
  causes Zope to consume more of your computer's memory.  A RAM Cache
  Manager does not require any external resources like a Squid server, to
  work.

For the purposes of this example, create a RAM Cache Manager in
the root folder called *CacheManager*.  This is going to be the
cache manager object for your whole site.

Now, you can click on *CacheManager* and see its configuration
screen.  There are a number of elements on this screen:

Title
  The title of the cache manager.  This is optional.

REQUEST variables
  This information is used to store the
  cached copy of a page.  This is an advanced feature, for now,
  you can leave this set to just "AUTHENTICATED_USER".

Threshold Entries
  The number of objects the cache manager
  will cache at one time.

Cleanup Interval
  The lifetime of cached results.

For now, leave all of these entries as is, they are good,
reasonable defaults.  That's all there is to setting up a cache
manager!

There are a couple more views on a cache manager that you may find
useful.  The first is the *Statistics* view.  This view shows you
the number of cache "hits" and "misses" to tell you how effective
your caching is.

There is also an *Associate* view that allows you to associate a
specific type or types of Zope objects with a particular cache
manager.  For example, you may only want your cache manager to
cache Scripts.  You can change these settings on the
*Associate* view.

At this point, nothing is cached yet, you have just created a
cache manager.  The next section explains how you can cache the
contents of actual documents.

Caching an Object
~~~~~~~~~~~~~~~~~

Caching any sort of cacheable object is fairly straightforward.
First, before you can cache an object you must have a cache
manager like the one you created in the previous section.

To cache a page, create a new page template object in the
root folder called *Weather*.  This object will contain some
weather information.  For example, let's say it contains::

  <html>
  <body>

    <p>Yesterday it rained.</p>

  </body>
  </html>

Now, click on the *Weather* page template and click on its *Cache*
view.  This view lets you associate this page with a cache
manager.  If you pull down the select box at the top of the view,
you'll see the cache manager you created in the previous section,
*CacheManager*.  Select this as the cache manager for *Weather*.

Now, whenever anyone visits the *Weather* page, they will get
the cached copy instead.  For a page as trivial as our
*Weather* example, this is not much of a benefit.  But imagine for
a moment that *Weather* contained some database queries.  For
example::

  <html>
  <body>

    <p>
      Yesterday's weather was
      <tal:yesterday tal:replace="context/yesterdayQuery" />
    </p>

    <p>
      The current temperature is
      <tal:current tal:replace="context/currentTempQuery" />
    </p>

  </body>
  </html>


Let's suppose that *yesterdayQuery* and *currentTempQuery* are
SQL Methods that query a database for yesterdays forecast and
the current temperature, respectively (for more information on
SQL Methods, see the chapter entitled `Relational Database
Connectivity <RelationalDatabases.html>`_.)  Let's also suppose that
the information in the database only changes once every hour.

Now, without caching, the *Weather* document would query the
database every time it was viewed.  If the *Weather* document was
viewed hundreds of times in an hour, then all of those hundreds of
queries would always contain the same information.

If you specify that the page should be cached, however, then
the page will only make the query when the cache expires.  The
default cache time is 300 seconds (5 minutes), so setting this
page up to be cached will save you 91% of your database
queries by doing them only one twelfth as often.  There is a
trade-off with this method, there is a chance that the data may be
five minutes out of date, but this is usually an acceptable
compromise.

Outbound Mail Services
----------------------

Zope comes with an object that is used to send outbound e-mail,
usually in conjunction with a Script (Python).

Mailhosts can be used Python to send an email
message over the Internet.  They are useful as 'gateways' out to
the world.  Each mailhost object is associated with one mail
server, for example, you can associate a mailhost object with
'yourmail.yourdomain.com', which would be your outbound SMTP mail
server.  Once you associate a server with a mailhost object, the
mailhost object will always use that server to send mail.

To create a mailhost object select *MailHost* from the add list.
You can see that the default id is "MailHost" and the default SMTP
server and port are "localhost" and "25".  make sure that either
your localhost machine is running a mail server, or change
"localhost" to be the name of your outgoing SMTP server.

Now you can use the new MailHost object from a Script.

Error Logging Services
----------------------

.. note::

  As of Zope 4, the **Site Error Log** is no longer a a dependency of Zope,
  but has to be installed separately if you want to use it.

  The **Site Error Log** is available as ``Products.SiteErrorLog`` on
  `PyPI <https://pypi.org/project/Products.SiteErrorLog/>`_.

The **Site Error Log** object, typically accessible in the Zope root
under the name `error_log`, provides debugging and error logging
information in real time. When your site encounters an error, it
will be logged in the **Site Error Log***, allowing you to review (and
hopefully fix!) the error.

Available options for the **Site Error Log** instance:

- *Number of exceptions to keep* - This option is set to 20 by default,
  rotating old exceptions out when more than 20 are stored.
  You may set this to a higher or lower number as you like.

- *Copy exceptions to the event log* - If this option is enabled, the
  **Site Error Log** object will copy the text of the received
  exceptions to Zope's event log.
  
- *Ignored exception types* - Here you can add **Exceptions** which you
  want to ignore.
  This means they will be neither shown in the ZMI, nor logged to
  Zope's event log.
  By default `Unauthorized`, `NotFound` and `Redirect` are set.

Virtual Hosting Services
------------------------

For detailed information about using virtual hosting services in
Zope, see the chapter entitled `Virtual Hosting Services
<VirtualHosting.html>`_.

Searching and Indexing Services
-------------------------------

For detailed information about using searching and indexing services in Zope to
index and search a collection of documents, see the chapter entitled
`Searching and Categorizing Content <SearchingZCatalog.html>`_.

Sessioning Services
-------------------

For detailed information about using Zope's "sessioning" services
to "keep state" between HTTP requests for anonymous users, see the
chapter entitled `Sessions <Sessions.html>`_.
