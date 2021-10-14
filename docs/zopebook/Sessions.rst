Session Management
##################

Sessions in Zope have historically been server side. They are simple to use, 
and (usually) only rely on one cookie that contains the browser id. However, 
server side sessions require additional work to scale in horizontal deployments 
where you are using ZEO, or have many Zope servers with read only ZODBs.

If you need only very few small session values, consider using cookies as a
replacement for a full session management system. The API for that would be 
``REQUEST.cookies.get("cookie_name", "default_value_if_cookie_not_set")`` and 
``RESPONSE.setCookie("cookie_name", "cookie_value")``. Plone has 
`a bit more documentation on how to work with cookies <https://docs.plone.org/develop/plone/sessions/cookies.html>`_.

The simplest session management is offered by the Zope add-on products
``Products.Sessions`` in conjunction with ``Products.TemporaryFolder``. It
stores session data in RAM memory, which means it is bound to a single Zope
process. It is suitable for small deployments, such as single Zope processes
without ZEO or ZEO deployments with a single ZEO client. The rest of this
chapter uses this simple session management implementation. It was written for
Zope 2, but still relevant to explain how the built in server side sessions
work.

.. note::

    The main difference between sessioning in Zope 2 and Zope 4 and higher is
    the fact that sessioning is no longer built-in. You need to install the
    add-on packages ``Products.Sessions`` and ``Products.TemporaryFolder``
    and then manually instantiate the Zope objects once that used to be put
    into the ZODB automatically.

To use the simple sessioning as described in this document, follow these steps
after installing ``Products.Sessions`` and ``Products.TemporaryFolder``:

- Add or uncomment the following temporary storage database definition in your
  Zope configuration file ``zope.conf``::

    <zodb_db temporary>
        <temporarystorage>
          name Temporary database (for sessions)
        </temporarystorage>
        mount-point /temp_folder
        container-class Products.TemporaryFolder.TemporaryContainer
    </zodb_db>

- Restart Zope and visit the Zope Management interface at the root of the site

- Select `ZODB Mount Point` from the list of addable items at the top right,
  then select the ``temp_folder`` line and click `Create selected mount
  points`.

- Visit the Session Data Manager object at ``/session_data_manager`` in the
  Zope Management Interface - this will create the session data container at
  ``/temp_folder/session_data``

If you need session management for larger or high-traffic deployments, see the
section `Alternative Server Side Session Backends for Zope 4 and higher`_.


Terminology
===========

Key terms used within this document
+++++++++++++++++++++++++++++++++++

Web session
  a series of HTTP requests from the same browser to the same server during
  that browser's execution life-span.

Browser Id
  the string or integer used to represent a single anonymous visitor to the
  part of the Zope site managed by a single browser id manager. E.g.
  "12083789728".

Browser Id Name
  the name which is looked for in places enumerated by the currently configured
  browser id namespaces. E.g. "_ZopeId".

Browser Id Namespaces
  the browser id name will be found in one of three possible places
  ("namespaces"): in form elements and/or query strings (aka "form"), in a
  cookie, or in the URL.

Session Data Object
  an transient data object that is found by asking a session data container for
  the item with a key that is the current browser id value.

Session Id
  the identifier for a session data object. This is different than the browser
  id. Instead of representing a single - *visitor*- , it represents a single -
  *visit*- .

Session Managers
================

Web browsers communicate with Web Servers using HTTP. HTTP does not provide
tools that can track users and data in the context of a web session. Zope's
session management works around the problem: it provides methods able to track
site visitor activity. Applications like "shopping carts" use session
management for this reason.

Zope's session management makes use of name-spaces like cookies, HTTP form
elements, and/or parts of URLs "in the background" to keep track of user
sessions. Which of these name-spaces are used is configurable using the
browser_id manager (described later).

Session data is valid for the duration of a **configurable inactivity** timeout
value or browser shut-down, which ever comes first. Zope's session management
keeps track of anonymous users as well as those who have Zope login accounts.

.. warning::

    Data maintained by Zope's session management is no more secure than
    HTTP itself. A session is secure if and only if:

    - the connection between a browser and Zope uses strong encryption

    - precautions specific to the security exposure are taken.

It's clear that you should not store sensitive information like credit card
numbers in a session container unless you understand the vulnerabilities. See
the section entitled `Security Considerations`_ near the end of this document.

It is advisable to use sessions only on pages where they are necessary because
of a performance impact on your application. The severity varies depending on
usage and configuration. A good "rule of thumb" is to account for a 5% - 10%
speed-of-execution penalty.

Some hints:

- Do not use ``SESSION`` to store ``REQUEST`` variables. They are already
  available in the ``REQUEST``.

- Do not store any data in ``SESSION`` that you can get from the Zope API. It's
  faster and more secure to get user Id from Zope's Security Manager than it
  is from the ``SESSION`` object.

Session Manager Components
==========================

Browser Id Manager
++++++++++++++++++

This component determines a remote client's "browser id", which uniquely
identifies a particular browser. The browser id is encoded in a
form/querystring variable, a cookie variable, or as part of the URL. The
browser id manager examines cookies, form and querystring elements, and URLs
to determine the client's browser id. It can also modify cookies and URLs
automatically in order to differentiate users between requests.

There may be more than one browser id manager in a Zope installation, but
commonly there will only be one. Application developers will generally not
talk directly to a browser id manager. Instead, they will use the Transient
Data Object (``REQUEST.SESSION``) which delegates some calls to a browser_id
manager.

Browser id managers have "fixed" Zope ids so they can be found via
acquisition by session data managers. Browser id managers also have
interfaces for encoding a URL with browser id information and performing
other utility functions.

The default sessioning configuration provides a Browser Id Manager as the
``browser_id_manager`` object in the root of the ZODB.

Session Data Manager
++++++++++++++++++++

This component is responsible for handing out session data to callers. When
session data is required, the session data manager:

* talks to a browser id manager to determine the current browser id

* creates a new session data object or hands back an existing session data
  object based on the browser id.

Developers generally do not directly use methods of session data managers to
obtain session data objects. Instead, they rely on the built-in
``REQUEST.SESSION`` object, which represents *the current session data object
related to the user's browser id*.

The session data object has an identifier distinct from the browser id. This
identifier represents a single user session with the server (unlike the
browser id, which represents a single browser). Many session data managers
can use one browser id manager. Many session data managers can be
instantiated in a single Zope installation. Different session data managers
can implement different policies related to session data object storage (e.g.
to which session data container the session data objects are stored).

The default sessioning configuration provides a Session Data Manager named
``session_data_manager`` in the root of the ZODB.

Transient Object Container
++++++++++++++++++++++++++

Also known as Session Data Containers, these components actually hold
information related to sessions.

Currently, a Transient Object Container is used to hold a special "transient
data object" instance for each ongoing session. Developers will generally not
interact with transient data containers. Transient data containers are
responsible for expiring the session data objects which live within them.

The default sessioning configuration provides a Transient Object Container at
``/temp_folder/session_data``. The session data objects in the default
``session_data`` Transient Object container are stored in RAM memory and thus
lost each time Zope is restarted.

Transient Data Object
+++++++++++++++++++++

Also known as the Session Data Object. These are the objects which are stored
in session data containers and managed by transient data managers.

Developers interact with a transient data object after obtaining one via
``REQUEST.SESSION`` or from a session data manager directly. A single transient
data object actually stores the useful information related to a single user's
session.

Transient data objects can be expired automatically by transient data
containers as a result of inactivity, or they can be manually invalidated in
the course of a script.

Using Session Data
==================

You will typically access session data through the ``SESSION`` attribute of the
``REQUEST`` object. Session data objects are like Python dictionaries, they
can hold almost any kind of object as a key or a value. It's likely you will
almost always use "normal" Python objects such as lists, dictionaries, strings,
and numbers.

Here's an example of how to work with a session using a Python Script::

  ## Script (Python) "sessionTest"
  secs_per_day = 24*60*60
  session = context.REQUEST.SESSION

  if 'last view' in session:
      # The script has been viewed before, since the 'last view'
      then = session['last view']
      now = context.ZopeTime()
      session['last view'] = now # reset last view to now
      return 'Seconds since last view %.2f' % ((now - then) * secs_per_day)

  # The script hasn't been viewed before, since there's no 'last view' 
  session['last view'] = context.ZopeTime()
  return 'This is your first view'

This example shows how to access ``SESSION`` data. But it is not a "best
practice" example. If performance is an issue, you should not attempt to keep
last-accessed time in this manner in a production application because it might
slow your application down dramatically and cause problems under high load.

Create a script with this body named ``sessionTest`` in your root folder and
then click its `Test` tab. While viewing the output, reload the frame a few
times. Note that the script keeps track of when you last viewed it and
calculates how long it has been since you last viewed it. Notice that if you
quit your browser and come back to the script it forgets you were ever there.
However, if you simply visit some other pages and then return within 20 minutes
or so, it still remembers the last time you viewed it.

See the `Concepts and Caveats`_ section at the end of this document for things
to watch out for while accessing Zope's Session Manager "naively".

You can use sessions in Page Templates and DTML Documents, too. For example,
here's a template snippet that displays the users favorite color (as stored in
a session)::

  <p tal:content="request/SESSION/favorite_color">Blue</p>

Sessions have additional configuration parameters and usage patterns detailed
below.

Default Configuration
=====================

If you install the Zope add-on ``Products.Sessions`` and followed the steps at
the top of this document you end up with a default sessioning configuration:

The Zope "default" browser id manager lives in the root folder and is named
``browser_id_manager``.

The Zope "default" session data manager lives in the root folder and is named
``session_data_manager``.

A "default" transient data container (session data container) is created as
``/temp_folder/session_data`` when Zope starts up.

The ``temp_folder`` object is a "mounted, nonundoing" database that keeps
information in RAM, so "out of the box", Zope stores session information in
RAM. The temp folder is a "nonundoing" storage (meaning you cannot undo
transactions which take place within it) because accesses to transient data
containers are very write-intensive, and undoability adds unnecessary overhead.

A transient data container stores transient data objects. The default
implementation of the transient data object shipped with the Zope add-on
``Products.Sessions`` is engineered to reduce the potential inherent in the
ZODB for "conflict errors" related to the ZODB's "optimistic concurrency"
strategy.

You needn't change any of the default options to use sessioning under Zope
unless you want to customize your setup. However, if you have custom needs, you
can create your own session data managers, browser id managers, temporary
folders, and transient object containers by choosing these items from Zope's
"add" list in the place of your choosing.

Advanced Development Using Sessioning
=====================================

Overview
++++++++

When you work with the ``REQUEST.SESSION`` object, you are working with a
"session data object" that is related to the current site user.

Session data objects have methods of their own, including methods which allow
developers to get and set data. Session data objects are also "wrapped" in the
acquisition context of their session data manager, so you may additionally call
any method on a session data object that you can call on a session data
manager.

Obtaining A Session Data Object
+++++++++++++++++++++++++++++++

The session data object associated with the browser id in the current request
may be obtained via ``REQUEST.SESSION``. If a session data object does not
exist in the session data container, one will be created automatically when you
reference ``REQUEST.SESSION``::

  <dtml-let data="REQUEST.SESSION">
      The 'data' name now refers to a new or existing session data object.
  </dtml-let>

You may also use the ``getSessionData()`` method of a session data manager to
do the same thing::

  <dtml-let data="session_data_manager.getSessionData()">
      The 'data' name now refers to a new or existing session data object.
  </dtml-let>

A reference to ``REQUEST.SESSION`` or a call to ``getSessionData()``
implicitly creates a new browser id if one doesn't exist in the current
request. These mechanisms also create a new session data object in the session
data container if one does not exist related to the browser id in the current
request. To inhibit this behavior, use the `create=0` flag to the
``getSessionData()`` method. In ZPT::

  <span tal:define="data python:context.session_data_manager.getSessionData(create=0)">

.. note:: 

    ``create=0`` means return a reference to the session or None.
    ``create=1`` means return a reference if one exists or create a new
    Session object and the reference.

Modifying A Session Data Object
+++++++++++++++++++++++++++++++

Once you've used ``REQUEST.SESSION`` or
``session_data_manager.getSessionData()`` to obtain a session data object,
you can set key/value pairs of that session data object. In ZPT::

  <span tal:define="data python: request.SESSION">
      <tal:block define="temp python: data.set('foo','bar')">
          <p tal:content="python: data.get('foo')">bar will print here"</p>
      </tal:block>
  </span>

An essentially arbitrary set of key/value pairs can be placed into a session
data object. Keys and values can be any kinds of Python objects (note: see
`Concepts and Caveats`_ section below for exceptions to this rule). The session
data container which houses the session data object determines its expiration
policy. Session data objects will be available across client requests for as
long as they are not expired.

Clearing A Session Data Object
++++++++++++++++++++++++++++++

You can clear all keys and values from a ``SESSION`` object by simply calling
its ``clear()`` method. In ZPT::

  <span tal:define="dummy python:request.SESSION.clear()"></span>

Manually Invalidating A Session Data Object
+++++++++++++++++++++++++++++++++++++++++++

Developers can manually invalidate a session data object. When a session data
object is invalidated, it will be flushed from the system.

There is a caveat. If you invalidate the session object in a script then you
**must** obtain a fresh copy of the session object by calling
``getSessionData`` and not by reference (``REQUEST.SESSION``).

Here is an example using DTML::

  <!-- set a SESSION key and value -->
  <dtml-let data="REQUEST.SESSION">
  <dtml-call "data.set('foo','bar')      

  <!-- Now invalidate the SESSION -->
  <dtml-call "data.invalidate()">

  <!-- But REQUEST.SESSION gives us stale data which is bad.
  The next statement will still show 'foo' and 'bar'
  <dtml-var "REQUEST.SESSION>
  </dtml-let>

  <!-- Heres the work-around: -->
  <dtml-let data="session_data_manager.getSessionData()">

  <!-- Now we get a fresh copy and life is good as 'foo' and 'bar' have gone away as expected -->
  <dtml-var data>

  </dtml-let>

Manual invalidation of session data is useful when you need a "fresh" copy of a
session data object.

If an `onDelete` event is defined for a session data object, the configured
method will be called before the data object is invalidated. See the section
`Using Session onAdd and onDelete Events`_ for information about session data
object `onDelete` and `onAdd` events.

Manually Invalidating A Browser Id Cookie
+++++++++++++++++++++++++++++++++++++++++

Invalidating a session data object does not invalidate the browser id cookie
stored on the user's browser. Developers may manually invalidate the cookie
associated with the browser id. To do so, they can use the
``flushBrowserIdCookie()`` method of a browser id manager. For example::

  <dtml-call "REQUEST.SESSION.getBrowserIdManager().flushBrowserIdCookie()">

If the ``cookies`` namespace isn't a valid browser id key namespace when this
call is performed, an exception will be raised.

Using Session Data with TAL
+++++++++++++++++++++++++++

Here's an example of using the session data object with TAL::

  <span tal:define="a python:request.SESSION;
                    dummy python:a.set('zopetime',context.ZopeTime())">
      <p tal:content="python: a.get('zopetime')"></p>
  </span>

Using Session Data From Python
++++++++++++++++++++++++++++++

Here's an example of using a session data manager and session data object from
a set of Python external methods::

  import time

  def setCurrentTime(self):
      a = self.REQUEST.SESSION
      a.set('thetime', time.time())

  def getLastTime(self):
      a = self.REQUEST.SESSION
      return a.get('thetime')

Calling ``setCurrentTime`` will set the value of the current session's
"thetime" key to an integer representation of the current time. Calling
``getLastTime`` will return the integer representation of the last
known value of "thetime".

Interacting with Browser Id Data
++++++++++++++++++++++++++++++++

You can obtain the browser id value associated with the current request::

  <dtml-var "REQUEST.SESSION.getBrowserIdManager().getBrowserId()">

Another way of doing this, which returns the same value is::

  <dtml-var "REQUEST.SESSION.getContainerKey()">

If no browser id exists for the current request, a new browser id is created
implicitly and returned.

If you wish to obtain the current browser id value without implicitly creating
a new browser id for the current request, you can ask the
``browser_id_manager`` object explicitly for this value with the `create=0`
parameter::

  <dtml-var "browser_id_manager.getBrowserId(create=0)">

This snippet will print a representation of the None value if there isn't a
browser id associated with the current request, or it will print the browser id
value if there is one associated with the current request. Using `create=0` is
useful if you do not wish to cause the sessioning machinery to attach a new
browser id to the current request, perhaps if you do not wish a browser id
cookie to be set.

The browser id is either a string or an integer and has no special meaning. In
your code, you should not rely on the browser id value composition, length, or
type as a result, as it is subject to change.

Determining Which Namespace Holds The Browser Id
++++++++++++++++++++++++++++++++++++++++++++++++

For some applications, it is advantageous to know from which namespace (
`cookies`, `form`, or `url`) the browser id has been gathered.

It should be noted that you can configure the ``browser_id_manager`` (in the
Zope root by default) so that it searches whatever combination of namespaces you
select.

There are three methods of browser id managers which allow you to accomplish
this::

  <dtml-if "REQUEST.SESSION.getBrowserIdManager().isBrowserIdFromCookie()">
      The browser id came from a cookie.
  </dtml-if>

  <dtml-if "REQUEST.SESSION.getBrowserIdManager().isBrowserIdFromForm()">
      The browser id came from a form.
  </dtml-if>

  <dtml-if "REQUEST.SESSION.getBrowserIdManager().isBrowserIdFromUrl()">
      The browser id came from the URL.
  </dtml-if>

The ``isBrowserIdFromCookie()`` method will return true if the browser id in
the current request comes from the ``REQUEST.cookies`` namespace. This is true
if the browser id was sent to the Zope server as a cookie.

The ``isBrowserIdFromForm()`` method will return true if the browser id in the
current request comes from the ``REQUEST.form`` namespace. This is true if the
browser id was sent to the Zope server encoded in a query string or as part of
a form element.

The ``isBrowserIdFromUrl()`` method will return true if the browser id in the
current request comes from elements of the URL.

If a browser id doesn't actually exist in the current request when one of these
methods is called, an error will be raised.

During typical operations, you shouldn't need to use these methods, as you
shouldn't care from which namespace the browser id was obtained. However, for
highly customized applications, this set of methods may be useful.

Obtaining the Browser Id Name/Value Pair and Embedding It Into A Form
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You can obtain the browser id name from a browser id manager instance. We've
already determined how to obtain the browser id itself. It is useful to also
obtain the browser id name if you wish to embed a browser id name/value pair as
a hidden form field for use in POST requests. Here's a TAL example::

    <span tal:define="idManager python:request.SESSION.getBrowserIdManager()">
        <form action="thenextmethod">
            <input type=submit name="submit" value=" GO ">
            <input type="hidden" name="name" value="value"
                   tal:attributes="name python: idManager.getBrowserIdName();
                                   value python: idManager.getBrowserId()">
        </form>
    </span>

A convenience function exists for performing this action as a method of a
browser id manager named ``getHiddenFormField``::

  <html>
  <body>
    <form action="thenextmethod">
      <input type="submit" name="submit" value=" GO ">
      <dtml-var "REQUEST.SESSION.getBrowserIdManager().getHiddenFormField()">
    </form>
  </body>
  </html>

When the above snippets are rendered, the resulting HTML will look something
like this::

  <html>
  <body>
    <form action="thenextmethod">
      <input type="submit" name="submit" value=" GO ">
      <input type="hidden" name="_ZopeId" value="9as09a7fs70y1j2hd7at8g">
    </form>
  </body>
  </html>

Note that to maintain state across requests when using a form submission, even
if you've got "Automatically Encode Zope-Generated URLs With a Browser Id"
checked off in your browser id manager, you'll either need to encode the form
"action" URL with a browser id (see `Embedding A Browser Id Into An HTML Link`_
below) or embed a hidden form field.

Using formvar-based sessioning.
+++++++++++++++++++++++++++++++

To use formvar-based sessioning, you need to encode a link to its URL with the
browser id by using the browser id manager's ``encodeUrl()`` method.

Determining Whether A Browser Id is "New"
+++++++++++++++++++++++++++++++++++++++++

A browser id is "new" if it has been set in the current request but has not yet
been acknowledged by the client. "Not acknowledged by the client" means it has
not been sent back by the client in a response. This is the case when a new
browser id is created by the sessioning machinery due to a reference to
``REQUEST.SESSION`` or similar as opposed to being received by the sessioning
machinery in a browser id name namespace. You can use the ``isBrowserIdNew()``
method of a browser id manager to determine whether the session is new::

  <dtml-if "REQUEST.SESSION.getBrowserIdManager().isBrowserIdNew()">
      Browser id is new.
  <dtml-else>
      Browser id is not new.
  </dtml-if>

This method may be useful in cases where applications wish to prevent or detect
the regeneration of new browser ids when the same client visits repeatedly
without sending back a browser id in the request. This may be the case when
a visitor has cookies disabled in their browser and the browser id manager
only uses cookies.

If there is no browser id associated with the current request, this method will
raise an error.

You shouldn't need to use this method during typical operations, but it may be
useful in advanced applications.


Determining Whether A Session Data Object Exists For The Browser Id Associated With This Request
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you wish to determine whether a session data object with a key that is the
current request's browser id exists in the session data manager's associated
session data container, you can use the ``hasSessionData()`` method of the
session data manager. This method returns true if there is
session data associated with the current browser id::

  <dtml-if "session_data_manager.hasSessionData()">
    The sessiondatamanager object has session data for the browser id
    associated with this request.
  <dtml-else>
    The sessiondatamanager object does not have session data for
    the browser id associated with this request.
  </dtml-if>

The ``hasSessionData()`` method is useful in highly customized applications,
but is probably less useful otherwise. It is recommended that you use
``REQUEST.SESSION`` instead, allowing the session data manager to determine
whether or not to create a new data object for the current request.

Embedding A Browser Id Into An HTML Link
++++++++++++++++++++++++++++++++++++++++

You can embed the browser id name/value pair into an HTML link for use during
HTTP GET requests. When a user clicks on a link with a URL encoded with the
browser id, the browser id will be passed back to the server in the
``REQUEST.form`` namespace. If you wish to use formvar-based session tracking,
you will need to encode all of your "public" HTML links this way. You can use
the ``encodeUrl()`` method of browser id managers to perform this encoding::

  <html>
  <body>
    <a href="<dtml-var "REQUEST.SESSION.getBrowserIdManager().encodeUrl('/amethod')">">
      Here
    </a>
    is a link.
  </body>
  </html>

The above dtml snippet will encode the URL "/amethod" (the target of the word
"Here") with the browser id name/value pair appended as a query string. The
rendered output of this DTML snippet would look something like this::

  <html>
  <body>
    <a href="/amethod?_ZopeId=7HJhy78978979JHK">Here</a>
    is a link.
  </body>
  </html>

You may successfully pass URLs which already contain query strings to the
``encodeUrl()`` method. It will preserve the existing query string and append
its own name/value pair.

You may choose to encode the browser id into the URL using an "inline" style if
you're checking for browser ids in the URL (e.g. if you've checked "URLs"
in the `Look for Browser Id in` form element of your browser id manager)::

  <html>
  <body>
    <a href="<dtml-var "REQUEST.SESSION.getBrowserIdManager().encodeUrl('/amethod', style='inline')">">Here</a>
    is a link.
  </body>
  </html>

The above dtml snippet will encode the URL "/amethod" (the target of the word
"Here") with the browser id name/value pair embedded as the first two elements
of the URL itself. The rendered output of this DTML snippet would look
something like this::

  <html>
  <body>
    <a href="/_ZopeId/7HJhy78978979JHK/amethod">Here</a>
    is a link.
  </body>
  </html>

Using Session onAdd and onDelete Events
+++++++++++++++++++++++++++++++++++++++

The configuration of a Transient Object Container (aka a session data
container) allows a method to be called when a session data object is created
(`onAdd`) or when it is invalidated or timed out (`onDelete`).

The events are independent of each other. You might want an `onAdd` method but
not an `onDelete` method. You may define one, both or none of these event
methods.

Here are examples of the kinds of things Session `onAdd` and `onDelete`
methods are used to do:

- The `onAdd` method can be used to populate a session data object with
  "default" values before it's used by application code.

- The `onDelete` method can write the contents of a session data object out to
  a permanent data store before it is timed out or invalidated.

.. warning::

    The `onAdd` and `onDelete` events do not raise exceptions if logic in the
    method code fails. Instead, an error is logged in the Zope event log.

You can manually configure the `onAdd` and `onDelete` methods. Click the
"management" tab of ``/temp_folder/session_data``. Enter a ZODB path to
either an External Method or Python Script.

.. note::

    This configuration is only good until the next Zope shutdown because
    ``/temp_folder/session_data`` is in a RAM database.
    See `Setting the default Transient Object Container Parameters`_
    further down to learn how to set this configuration permanently on the
    ``session_data_manager`` object.


Writing onAdd and onDelete Methods
++++++++++++++++++++++++++++++++++

Session data objects optionally call a Zope method when they are created and
when they are timed out or invalidated.

Specially-written Script (Python) scripts can be written to serve the purpose
of being called on session data object creation and invalidation.

The Script (Python) should define two arguments, ``sdo`` and ``toc``. ``sdo``
represents the session data object being created or terminated, and ``toc``
represents the transient object container in which this object is stored.

For example, to create a method to handle a session data object `onAdd` event
which prepopulates the session data object with a ``DateTime`` object, you might
write a Script (Python) named ``onAdd`` which had function parameters
``sdo`` and ``toc`` and a body of::

  sdo['date'] = context.ZopeTime()

If you set the path to this method as the `onAdd` event, before any application
handles the new session data object, it will be prepopulated with a key ``date``
that has the value of a ``DateTime`` object set to the current time.

To create a method to handle a session `onDelete` event which writes a log
message, you might write an External Method with the following body::

  from zLOG import LOG, WARNING

  def onDelete(sdo, toc):
      logged_out = sdo.get('logged_out', None)
      if logged_out is None:
          LOG('session end', WARNING,
              'session ended without user logging out!')

If you set the path to this method as the `onDelete` event, a message will be
logged if the ``logged_out`` key is not found in the session data object.

Note that for `onDelete` events, there is no guarantee that the `onDelete` event
will be called in the context of the user who originated the session! Due to
the "expire-after-so-many-minutes-of-inactivity" behavior of session data
containers, a session data object `onDelete` event initiated by one user may be
called while a completely different user is visiting the application. Your
`onDelete` event method should not naively make any assumptions about user state.
For example, the result of the Zope call ``getSecurityManager().getUser()`` in an
`onDelete` session event method will almost surely *not* be the user who
originated the session.

The session data object `onAdd` method will always be called in the context of
the user who starts the session.

For both `onAdd` and `onDelete` events, it is almost always desirable to set
proxy roles on event methods to replace the roles granted to the executing user
when the method is called because the executing user will likely not be the user
for whom the session data object was generated. For more information about proxy
roles, see the chapter entitled `Users and Security <Security.html>`_.

For additional information about using session `onDelete` events in combination
with data object timeouts, see the section entitled
`Session Data Object Expiration Considerations`_ in the Concepts and Caveats
section below.


Configuration and Operation
===========================

Setting the default Transient Object Container Parameters
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Click on ``/temp_folder/session_data`` in the Zope Management Interface and
you'll see options to control inactivity timeouts and the maximum
allowable number of Session objects. You can even include paths to Python
Scripts that handle a Session's after-add and before-delete events.

Because ``/temp_folder/session_data`` is stored in a RAM database, it
disappears and is recreated after each restart of your Zope server. This means
that any changes to parameters will be lost the next time you restart your Zope
server.

If you need to permanently alter the default Transient Object Container's
configuration you must visit the session data manager object at
``/session_data_manager`` and set the defaults at the bottom of its `Settings`
ZMI page. The configuration values you assign there will be applied whenever
Zope restarts and ``/temp_folder/session_data`` is recreated.

Note that additional Transient Object Containers can be instantiated in
permanent storage. They are rarely needed. This case is covered in
detail later in this document.

Instantiating Multiple Browser Id Managers (Optional)
+++++++++++++++++++++++++++++++++++++++++++++++++++++

Transient data objects depend on a session data manager, which in turn depends
on a browser id manager. A browser id manager doles out and otherwise manages
browser ids. All session data managers need to talk to a browser id manager to
get browser id information.

You needn't create a browser id manager to use sessioning. One is already
created as a result of the initial Zope installation. If you've got special
needs, you may want to instantiate more than one browser id manager. Having
multiple browser id managers may be useful in cases where you have a "secure"
section of a site and an "insecure" section of a site, each using a different
browser id manager with respectively restrictive security settings.

In the container of your choosing, select "Browser Id Manager" from the add
drop-down list in the Zope management interface. When you add a new browser id
manager, the form options available are:

Id
  You cannot choose an id for your browser id manager. It must always be
  "browser_id_manager". Additionally, you cannot rename a browser id manager.
  This is required in the current implementation so that session data managers
  can find session id managers via Zope acquisition.

Title
  the browser id manager title.

Browser Id Name
  the name used to look up the value of the browser id. This will be the name
  looked up in the `cookies` or `form` REQUEST namespaces when the browser id
  manager attempts to find a cookie, form variable, or URL with a browser id in
  it.

Look for Browser Id Name In
  choose the request elements to look in when searching for the browser id
  name. You may choose `cookies`, `Forms and Query Strings`, and `URLs`.

Automatically Encode Zope-Generated URLs With A Browser Id
  if this option is checked, all URLs generated by Zope (such as URLs obtained
  via the ``absolute_url`` method of all Zope objects) will have a browser id
  name/value pair embedded within them. This typically only make sense if
  you've also got the `URLs` setting of "Look for Browser Id in" checked off.

Cookie Path
  this is the `path` element which should be sent in the browser id cookie.

Cookie Domain
  this is the "domain" element which should be sent in the browser id cookie.
  Leaving this form element blank results in no domain element in the cookie.
  If you change the cookie domain here, the value you enter must have at least
  two dots (as per the cookie spec).

Cookie Lifetime In Days
  browser id cookies sent to browsers will last this many days on a remote
  system before expiring if this value is set. If this value is 0, cookies will
  persist on client browsers for only as long as the browser is open.

Only Send Cookie Over HTTPS
  if this flag is set, only send cookies to remote browsers if they're
  communicating with us over HTTPS. The browser id cookie sent under this
  circumstance will also have the `secure` flag set, which the remote
  browser should interpret as a request to refrain from sending the cookie back
  to the server over an insecure (non-HTTPS) connection. If you
  wish to share browser id cookies between HTTPS and non-HTTPS connections from
  the same browser, do not set this flag.

After reviewing and changing these options, click the "Add" button to
instantiate a browser id manager. You can change any of a browser id manager's
initial settings by visiting it in the management interface.

Instantiating A Session Data Manager (Optional)
+++++++++++++++++++++++++++++++++++++++++++++++

After instantiating at least one browser id manager, it's possible to
instantiate a session data manager. You don't need to do this in order to begin
using Zope's sessioning machinery, as a default session data manager is created
as ``/session_data_manager``

You can place a session data manager in any Zope container,as long as a browser
id manager object named ``browser_id_manager`` can be acquired from that
container. The session data manager will use the first acquired browser id
manager.

Choose "Session Data Manager" within the container you wish to house the
session data manager from the "Add" drop-down box in the Zope management
interface.

The session data manager add form displays these options:

Id
  choose an id for the session data manager

Title
  choose a title for the session data manager

Transient Object Container Path
  enter the Zope path to a Transient Object Container in this text box in order
  to use it to store your session data objects.

  .. warning::

    Session managers should not share transient object paths!

After reviewing and changing these options, click the "Add" button to
instantiate a session data manager.

You can manage a session data manager by visiting it in the management
interface. You may change all options available during the add process by doing
this.

Instantiating a Transient Object Container
++++++++++++++++++++++++++++++++++++++++++

The default transient object container at ``/temp_folder/session_data``
stores its objects in RAM, so these objects and their data disappear when you
restart Zope.

If you want your session data to persist across server reboots, or if you have
a very large collection of session data objects, or if you'd like to share
sessions between ZEO clients, you will want to instantiate a transient data
container in a more permanent storage.

A heavily-utilized transient object container **should be instantiated inside a
database which is nonundoing**! Although you may instantiate a transient data
container in any storage, if you make heavy use of an external session data
container in an undoing database (such as the default Zope database which is
backed by `FileStorage`, an undoing and versioning storage), your database will
grow in size very quickly due to the high-write nature of session tracking,
forcing you to pack very often. You can "mount" additional storages within the
`zope.conf` file of your Zope instance. The default `temp_folder` is mounted
inside a `TemporaryStorage` , which is nonundoing and RAM-based.

Here are descriptions of the add form of a Transient Object Container, which
may be added by selecting "Transient Object Container" for the Zope Add list.:

.. note::

  When you add a transient object container to a non-RAM-based
  storage, unlike the the default transient objects in ``/temp_folder``,
  these instances of TOC maintain their parameter settings between Zope
  Restarts.

Id
  the id of the transient object container

Title (optional)
  the title of the transient object container

Data object timeout in minutes
  enter the number of minutes of inactivity which causes a contained transient
  object be be timed out. "0" means no expiration.

Maximum number of subobjects
  enter the maximum number of transient objects that can be added to this
  transient object container. This value helps prevent "denial of service"
  attacks to your Zope site by effectively limiting the number of concurrent
  sessions.

Script to call upon object add (optional)
  when a session starts, you may call an External Method or Script (Python).
  This is the Zope path to the External Method or Script (Python) object to be
  called. If you leave this option blank, no `onAdd` function will be called. An
  example of a method path is ``/afolder/amethod``.

Script to call upon object delete (optional)
  when a session ends, you may call an External Method or Script (Python). This
  is the Zope path to the External Method or Script (Python) object to be
  called. If you leave this option blank, no `onDelete` function will be called.
  An example of a method path is ``/afolder/amethod``.


Multiple session data managers can make use of a single transient object
container to the extent that they may share the session data objects placed in
the container between them. This is not a recommended practice, however, as it
has not been tested at all.

The `data object timeout in minutes` value is the number of minutes that
session data objects are to be kept since their last-accessed time before they
are flushed from the data container. For instance, if a session data object is
accessed at 1:00 pm, and if the timeout is set to 20 minutes, if the session
data object is not accessed again by 1:19:59, it will be flushed from the data
container at 1:20:00 or a time shortly thereafter. "Accessed", in this
terminology, means "pulled out of the container" by a call to the session data
manager's ``getSessionData()`` method or an equivalent (e.g. a reference to
``REQUEST.SESSION``). See `Session Data Object Expiration Considerations`_ in the
`Concepts and Caveats`_ section below for details on session data expiration.

Configuring Sessioning Permissions
++++++++++++++++++++++++++++++++++

You need only configure sessioning permissions if your requirements deviate
substantially from the norm. In this case, here is a description of the
permissions related to sessioning.

Permissions related to browser id managers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add Browser Id Manager
  allows a role to add browser id managers. By default, enabled for `Manager`.

Change Browser Id Manager
  allows a role to change an instance of a browser id manager. By default,
  enabled for `Manager`.

Access contents information
  allows a role to obtain data about browser ids. By default, enabled for
  `Manager` and `Anonymous`.


Permissions related to session data managers:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add Session Data Manager
  allows a role to add session data managers. By default, enabled for
  `Manager`.

Change Session Data Manager
  allows a role to call management-related methods of a session data manager.
  By default, enabled for `Manager`.

Access session data
  allows a role to obtain access to the session data object related to the
  current browser id. By default, enabled for `Manager` and `Anonymous`. You
  may wish to deny this permission to roles who have DTML or Web-based Python
  scripting capabilities who should not be able to access session data.

Access arbitrary user session data
  allows a role to obtain and otherwise manipulate any session data object for
  which the browser id is known. By default, enabled for `Manager`.

Access contents information
  allows a role to obtain information about session data. By default, enabled for
  `Manager` and `Anonymous`.

Permissions related to transient object containers:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add Transient Object Container
  allows a role to add transient objects containers. By default, enabled for
  `Manager`.

Change Transient Object Container
  allows a role to make changes to a transient object container.

Access Transient Objects
  allows a role to obtain and otherwise manipulate the transient object related
  to the current browser id.

Concepts and Caveats
====================

Security Considerations
+++++++++++++++++++++++

Sessions are insecure by their very nature. If an attacker gets a hold of
someone's browser id, and if they can construct a cookie or use form elements
or URL elements to pose as that user from their own browser, they will have
access to all information in that user's session. Sessions are not a
replacement for authentication for this reason.

Ideally, you'd like to make certain that nobody but the user it's intended for
gets hold of his browser id. To take steps in this direction, and if you're
truly concerned about security, you will ensure that you use cookies to
maintain browser id information, and you will secure the link between your
users and your site using HTTPS. In this configuration, it is more difficult to
"steal" browser id information as the browser id will not be evident in the URL
and it will be very difficult for attackers to "tap" the encrypted link between
the browser and the Zope site.

There are significant additional risks to user privacy in employing sessions in
your application, especially if you use URL-based or formvar-based browser ids.
Commonly, a browser id is embedded into a form/querystring or a URL in order to
service users who don't have cookies enabled.

For example, this kind of bug was present until recently in a lot of webmail
applications: if you sent a mail to someone that included a link to a site
whose logs you could read, and the user clicked on the link in his webmail
page, the full URL of the page, including the authentication (stored as session
information in the URL) would be sent as a HTTP REFERER to your site.

Nowadays all serious webmail applications either choose to store at least some
of the authentication information outside of the URL (in a cookie for
instance), or process all the user-originated URLs included in the mail to make
them go through a redirection that sanitizes the HTTP REFERER.

The moral of the story is: if you're going to use sessions to store sensitive
information, and you link to external sites within your own site, you're best
off using *only* cookie-based browser ids.

Browser Id (Non-)Expiration
+++++++++++++++++++++++++++

A browser id will last as long as the browser id cookie persists on the client,
or for as long as someone uses a bookmarked URL with a browser id encoded into
it.

The same id will be obtained by a browser id manager on every visit by that
client to a site - potentially indefinitely depending on which conveyance
mechanisms you use and your configuration for cookie persistence.

The transient object container implements a policy for data object expiration.
If asked for a session data object related to a particular browser id which has
been expired by a session data container, a session data manager will a return
a new session data object.

Session Data Object Expiration Considerations
+++++++++++++++++++++++++++++++++++++++++++++

Session data objects expire after the period between their last access and
"now" exceeds the timeout value provided to the session data container which
hold them. No special action needs be taken to expire session data objects.

However, because Zope has no scheduling facility, the sessioning machinery
depends on the continual exercising of itself to expire session data objects.
If the sessioning machinery is not exercised continually, it's possible that
session data objects will stick around longer than the time specified by their
data container timeout value. For example:

- User A exercises application machinery that generates a session data object.
  It is inserted into a session data container which advertises a 20-minute
  timeout.

- User A "leaves" the site.

- 40 minutes go by with no visitors to the site.

- User B visits 60 minutes after User A first generated his session data
  object, and exercises app code which hands out session data objects. - *User
  A's session is expired at this point, 40 minutes "late".*

As shown, the time between a session's onAdd and onDelete is not by any means
*guaranteed* to be anywhere close to the amount of time represented by the
timeout value of its session data container. The timeout value of the data
container should only be considered a "target" value.

Additionally, even when continually exercised, the sessioning machinery has a
built in error potential of roughly 20% with respect to expiration of session
data objects to reduce resource requirements. This means, for example, if a
transient object container timeout is set to 20 minutes, data objects added to
it may expire anywhere between 16 and 24 minutes after they are last accessed.

Sessioning and Transactions
+++++++++++++++++++++++++++

Sessions interact with Zope's transaction system. If a transaction is aborted,
the changes made to session data objects during the transaction will be rolled
back.

Mutable Data Stored Within Session Data Objects
+++++++++++++++++++++++++++++++++++++++++++++++

If you mutate an object stored as a value within a session data object, you'll
need to notify the sessioning machinery that the object has changed by calling
`set` or `__setitem__` on the session data object with the new object value.
For example::

  session = self.REQUEST.SESSION
  foo = {}
  foo['before'] = 1
  session.set('foo', foo)

  # mutate the dictionary

  foo['after'] = 1

  # performing session.get('foo') 10 minutes from now will likely
  # return a dict with only 'before' within!

You'll need to treat mutable objects immutably, instead. Here's an example that
makes the intent of the last example work by doing so::

  session = self.REQUEST.SESSION
  foo = {}
  foo['before'] = 1
  session.set('foo', foo)

  # mutate the dictionary
  foo['after'] = 1

  # tickle the persistence machinery
  session.set('foo', foo)

An easy-to-remember rule for manipulating data objects in session storage:
always explicitly place an object back into session storage whenever you change
it. For further reference, see the "Persistent Components" chapter of the Zope
Developer's Guide at https://zope.readthedocs.io/en/latest/zdgbook/index.html.

session.invalidate() and stale references to the session object
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This Python Script illustrates an issue with using the ``invalidate`` method
of a session object::

  request = container.REQUEST
  session = request.SESSION
  session.set('foo','bar')
  session.invalidate() 
  # ............................................
  # we expect that invalidate() flushes the session 
  # ............................................
  print('after invalidate()',session.get('foo')) # 'bar' still prints!

  # ............................................
  # Even this isn't enough
  # ............................................
  session = request.SESSION
  print('after invalidate()', session.get('foo')) # 'bar' still prints!

  # ............................................
  # Here's the work-around
  # ............................................
  session = context.session_data_manager.getSessionData()
  print('after getSessionData', session.get('foo')) # 'bar' is GONE
  return printed

In short, after using the ``invalidate`` method of a session object, the next
reference to the session object you obtain should be through ``getSessionData``
rather than ``REQUEST.SESSION``.

Session Data Object Keys
++++++++++++++++++++++++

A session data object has essentially the same restrictions as a Python
dictionary. Keys within a session data object must be hashable (strings,
tuples, and other immutable basic Python types; or instances which have a
``__hash__`` method). This is a requirement of all Python objects that are to be
used as keys to a dictionary. For more information, see the associated Python
documentation at
https://docs.python.org/3/library/stdtypes.html#mapping-types-dict.

In-Memory Session Data Container RAM Utilization
++++++++++++++++++++++++++++++++++++++++++++++++

Each session data object which is added to an "internal" (RAM-based) session
data container will consume at least 2K of RAM.

Mounted Transient Object Container Caveats
++++++++++++++++++++++++++++++++++++++++++

Persistent objects which have references to other persistent objects in the
same database cannot be committed into a mounted database because the ZODB does
not currently handle cross-database references.

Transient object containers are sometimes stored in a "mounted" database
as is currently the case for the default ``/temp_folder/session_data``
TOC. If you use a transient object container that is accessed via a "mounted"
database, you cannot store persistent object instances which have already been
stored in the "main" database as keys or values in a session data object. If
you try to do so, it is likely that an ``InvalidObjectReference``
exception will be raised by the ZODB when the transaction involving the object
attempts to commit. As a result, the transaction will fail and the session data
object (and other objects touched in the same transaction) will fail to be
committed to storage.

If your "main" ZODB database is backed by a nonundoing storage, you can avoid
this condition by storing session data objects in an transient object container
instantiated within the "main" ZODB database. If this is not an option, you
should ensure that objects you store as values or keys in a session data object
held in a mounted session data container are instantiated "from scratch" (via
their constructors), as opposed to being "pulled out" of the main ZODB.

Conflict Errors
+++++++++++++++

This session tracking software stores all session state in Zope's ZODB. The
ZODB uses an optimistic concurrency strategy to maintain transactional
integrity for simultaneous writes. This means that if two objects in the ZODB
are changed at the same time by two different connections (site visitors)
a ``ConflictError`` will be raised. Zope retries requests that raise a
ConflictError at most 3 times. If your site is extremely busy, you may notice
ConflictErrors in the Zope debug log (or they may be printed to the console
from which you run Zope). An example of one of these errors is as follows::

  2009-01-16T04:26:58 INFO(0) Z2 CONFLICT Competing writes at /getData
  Traceback (innermost last):
  File /zope/lib/python/ZPublisher/Publish.py, line 175, in publish
  File /zope/lib/python/Zope/__init__.py, line 235, in commit
  File /zope/lib/python/ZODB/Transaction.py, line 251, in commit
  File /zope/lib/python/ZODB/Connection.py, line 268, in commit
  ConflictError: '\000\000\000\000\000\000\002/'

Errors like this in your debug log (or console if you've not redirected debug
logging to a file) are normal to an extent. If your site is under heavy
load, you can expect to see a ConflictError perhaps every 20 to 30 seconds. The
requests which experience conflict errors will be retried automatically by
Zope, and the end user should **never** see one. Generally, session data objects
attempt to provide application-level conflict resolution to reduce the
limitations imposed by conflict errors.

.. note::

    To take advantage of application-level conflict resolution you must store
    your transient object container in a storage such as FileStorage or
    TemporaryStorage which supports application-level conflict resolution.

Alternative Server Side Session Backends for Zope 4 and higher
==============================================================

To use server side sessions on Zope 4 and up, you have two  ways to go about 
it. You can use a separate session server, most likely using 
`Memcached <https://memcached.org>`_, or place the session storage in either a 
``<filestorage>``, ``<temporarystorage>`` or ``<mappingstorage>`` backed ZODB.

Use of an alternative session server
++++++++++++++++++++++++++++++++++++

There are two projects that enable you to use 
`Memcached <https://memcached.org>`_ in Zope projects. This is the recommended 
way to use server side sessions.

- `Products.mcdutils <https://pypi.org/project/Products.mcdutils/>`_ is a drop 
  in replacement for the Zope 2 session implementation, that allows storing 
  session values in Memcached. This allows to retain all existing API calls to 
  session objects and still works well in e.g. ZEO contexts where multiple Zope 
  Servers need to share session data. Upgrading to it from existing session 
  usage is 
  `quite simple <https://mcdutils.readthedocs.io/en/latest/usage_zmi.html>`_. 

- `collective.beaker <https://pypi.org/project/collective.beaker/>`_ is a 
  plugin that makes makes `Beaker <https://pypi.org/project/Beaker/>`_ available 
  in a Zope context. You can use Beaker for sessions, but of course it has lots 
  of support for caching (with different cache reagions to support different 
  cache timeouts) and support for different backends like 
  `Redis <https://redis.io>`_ 

Use of an internal session server
+++++++++++++++++++++++++++++++++

For development environments or low traffic sites it is possible to just store 
the sessions data in a ZODB. You have to use a different ZODB for this. Example 
config: ::

    <zodb_db temporary>
        # Temporary storage database (for sessions)
        <temporarystorage>
          name temporary storage for sessioning
        </temporarystorage>
        mount-point /temp_folder
        container-class Products.TemporaryFolder.TemporaryContainer
    </zodb_db>
    
This can also work in a ZEO environment where you serve up a shared temporary
storage from a ZEO server. An example ZEO client configuration
could look like this::

    %import ZEO
    
    <zodb_db main>
        <clientstorage>
            server $INSTANCE/var/zeosocket
            storage main
            name zeostorage Data.fs
        </clientstorage>
        mount-point /
    </zodb_db>
    
    <zodb_db temporary>
        <clientstorage>
            server $INSTANCE/var/zeosocket
            storage temporary
            name zeostorage temporary
        </clientstorage>
        mount-point /temp_folder
        container-class Products.TemporaryFolder.TemporaryContainer
    </zodb_db>

The ZEO server configuration could show this::

    %define INSTANCE /path/to/instance/dir
    
    <zeo>
        address $INSTANCE/var/zeosocket
    </zeo>
    
    <filestorage main>
        path $INSTANCE/var/Data.fs
    </filestorage>
    
    <temporarystorage temporary>
      name temporary storage for sessioning
    </temporarystorage>


Even though this works, there are some important caveats when going this route. 
If you use a ZODB ``<filestorage>`` backend, even two parallel requests that 
write to the session can overwrite each other silently, even if they write to 
different session keys. I.e. only one of the writes will succeed - without 
errors. ``<temporarystorage>`` based ZODBs are quite a bit more reliable in this 
regard, but if you use a ``<temporarystorage>`` via ZEO, restarting the ZEO 
server will drop all session data and the Zope frontends will block as they see 
an older transaction number than what they last saw. That means you will need 
to ensure that Zope frontends restart if ZEO backends restart, which is quite a 
PITA.

Given all of this: Production deployments with ZEO should avoid 
``<temporarystorage>``-based sessions. Since ZEO is usually used for performance
``<filestorage>`` based sessions are probably too slow anyway. Also the problem 
of silently dropped sessions writes with parallel requests remains. Use of 
Memcached based sessions is much safer and with 
`Products.mcdutils <https://pypi.org/project/Products.mcdutils/>`_ just a drop 
in replacement for native Zope sessions. For development environments, however,
``<temporarystorage>`` solutions are fine and allow a simpler setup.
