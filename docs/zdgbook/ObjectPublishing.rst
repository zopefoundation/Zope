#################
Object Publishing
#################

.. note::

  Previously, this document contained information about access by
  **FTP** and **WebDAV**. As those functionalities were provided by the
  now removed **ZServer**, the related information also has been removed.

  Please directly refer to the **ZServer** package for further
  information.


Introduction
============

Zope puts your objects on the web. This is called **object
publishing**. One of Zope's unique characteristics is the way it
allows you to walk up to your objects and call methods on them with
simple URLs. In addition to HTTP, Zope makes your objects available
via XML-RPC.

In this chapter you'll find out exactly how Zope publishes objects.
You'll learn all you need to know in order to design your objects for
web publishing.


HTTP Publishing
===============

Zope 4 no longer ships with a builtin web server, so when you want
to interact with Zope via browser you have to setup a WSGI server.


.. note::

    For usage on a production server you will probably want to setup a
    reverse proxy in front of the WSGI server.


The WSGI server receives the request and hands it over to Zope, where
it is processed by *ZPublisher*, which is Zope's object publisher.
**ZPublisher** is a kind of light-weight ORB (Object Request
Broker). It takes the request and locates an object to handle the
request. The publisher uses the request URL as a map to locate the
published object. Finding an object to handle the request is called
**traversal**, since the publisher moves from object to object as it
looks for the right one. Once the published object is found, the
publisher calls a method on the published object, passing it
parameters as necessary. The publisher uses information in the
request to determine which method to call and what parameters to
pass. The process of extracting parameters from the request is called
**argument marshalling**. The published object then returns a response,
which is passed back to the WSGI server. Finally, the WSGI server
passes the response back to your web browser.


The publishing process is summarized in [2-1]

.. figure:: Figures/2-1.png

   2.1 Object publishing


Typically the published object is a persistent object that the
published module loads from the ZODB. See Chapter 6 for more
information on the ZODB.


This chapter will cover all the steps of object publishing in detail.


To summarize, object publishing consists of the main steps:

1. A request is sent to the publisher.

2. The publisher locates the published object using the request
   URL as a map.

3. The publisher calls the published object with arguments from
   the request.

4. The publisher interprets the results and passes them back.

The chapter will also cover all the technical details, special cases
and extra-steps that this list glosses over.


URL Traversal
-------------

Traversal is the process the publisher uses to locate the published
object. Typically the publisher locates the published object by
walking along the URL. Take for example a collection of objects::

      class Classification:
          ...

      class Animal:
          ...

          def screech(self, ...):
              ...

      vertebrates=Classification(...)
      vertebrates.mammals=Classification(...)
      vertebrates.reptiles=Classification(...)
      vertebrates.mammals.monkey=Animal(...)
      vertebrates.mammals.dog=Animal(...)
      vertebrates.reptiles.lizard=Animal(...)


This collection of objects forms an object hierarchy. Using Zope you
can publish objects with URLs. For example, the URL
http://zope/vertebrates/mammals/monkey/screech will traverse the
object hierarchy, find the *monkey* object and call its *screech*
method.

.. figure:: Figures/2-2.png

   2.2 Traversal path through an object hierarchy

The publisher starts from the root object and takes each step in the
URL as a key to locate the next object. It moves to the next object
and continues to move from object to object using the URL as a guide.

Typically the next object is a sub-object of the current object that
is named by the path segment. So in the example above, when the
publisher gets to the *vertebrates* object, the next path segment is
*mammals*, and this tells the publisher to look for a sub-object of
the current object with that name. Traversal stops when Zope comes to
the end of the URL. If the final object is found, then it is
published, otherwise an error is returned.

Now let's take a closer look at traversal.


Publishable Object Requirements
-------------------------------

Zope has few restrictions on publishable objects. The basic rule is
that the object must have a doc string. This requirement goes for
methods, too.

Another requirement is that a publishable object must not have a name
that begins with an underscore. These two restrictions are designed to
keep private objects from being published.

Finally, published objects cannot be Python modules.


Traversal Methods
-----------------

During traversal, *ZPublisher* cuts the URL into path elements
delimited by slashes, and uses each path element to traverse from the
current object to the next object. *ZPublisher* locates the next
object in one of three ways:

1. Using ``__bobo_traverse__``.

2. Using ``getattr``.

3. Using dictionary access.

First, the publisher attempts to call the traversal hook method
``__bobo_traverse__``. If the current object has this method it is
called with the request and the current path element. The method
should return the next object or ``None`` to indicate that a next
object can't be found. You can also return a tuple of objects from
``__bobo_traverse__`` indicating a sequence of sub-objects. This
allows you to add additional parent objects into the request. This is
almost never necessary.


Here's an example of how to use ``__bobo_traverse__``::

          def __bobo_traverse__(self, request, key):
              """Return subobjects depending on cookie contents."""
              if request.cookies.has_key('special'):
                  return self.special_subobjects.get(key, None)
              return self.normal_subobjects.get(key, None)


This example shows how you can examine the request during the
traversal process.

If the current object does not define a ``__bobo_traverse__`` method,
then the next object is searched for using ``getattr``. This locates
subobjects in the normal Python sense.

If the next object can't be found with ``getattr``, *ZPublisher* calls
on the current object as though it were a dictionary. Note: the path
element will be a string, not an integer, so you cannot traverse
sequences using index numbers in the URL.

For example, suppose ``a`` is the current object, and ``next`` is the
name of the path element. Here are the three things that *ZPublisher*
will try in order to find the next object:

  1. ``a.__bobo_traverse__("next")``

  2. ``a.next``

  3. ``a["next"]``
  

Publishing Methods
------------------

Once the published object is located with traversal, Zope *publishes*
it in one of three possible ways:

- Calling the published object -- If the published object is a
  function or method or other callable object, the publisher calls it.
  Later in the chapter you'll find out how the publisher figures out
  what arguments to pass when calling.

- Calling the default method -- If the published object is not
  callable, the publisher uses the default method. For HTTP *GET* and
  *POST* requests the default method is 'index_html'. For other HTTP
  requests such as *PUT* the publisher looks for a method named by the
  HTTP method. So for an HTTP *HEAD* request, the publisher would
  call the *HEAD* method on the published object.

- Stringifying the published object -- If the published object isn't
  callable, and doesn't have a default method, the publisher
  publishes it using the Python ``str`` function to turn it into a
  string.


After the response method has been determined and called, the
publisher must interpret the results.


Character Encodings for Responses
---------------------------------

If the published method returns an object of type *binary*, the
publisher will use it directly as the body of the response.

Things are different if the published method returns a unicode string,
because the publisher has to apply some character encoding. The
published method can choose which character encoding it uses by
setting a *Content-Type* response header which includes a *charset*
property (setting response headers is explained later in this
chapter). A common choice of character encoding is UTF-8, which is
also the default encoding.

If the *Content-Type* header does not include a charset or is not set
at all, the default encoding is set.

If you want to manually set a *Content-Type* header you have to set a
value like ``text/html; charset=UTF-8``.


HTTP Responses
--------------

Usually, the published method returns a string which is considered
the body of the HTTP response. The response headers can be controlled
by calling methods on the response object, which is described later in
the chapter.

.. note::

  When the return value is empty, e.g. an empty list, instead of
  returning an empty page, Zope issues a header with a 204 status code.

  Depending on the used client, it looks like nothing happens.


Optionally, the published method can return a tuple with
the title and the body of the response. In this case, the publisher
returns a generated HTML page, with the first item of the tuple used
for the value of the HTML ``title`` tag of the page, and the second
item as the content of the HTML ``body`` tag.


For example a response of::

  ("my_title", "my_text")


is turned into this HTML page::

  <html>
  <head><title>my_title</title></head>
  <body>my_text</body>
  </html>


Controlling Base HREF
---------------------

When you publish an object that returns HTML relative links should
allow you to navigate between methods.

Consider this example::

  class Example:
      """example class"""

      def one(self):
          """render page one"""
          return """<html>
                    <head><title>one</title></head>
                    <body>
                    <a href="two">two</a>
                    </body>
                    </html>"""

      def two(self):
          """render page two"""
          return """<html>
                    <head><title>two</title></head>
                    <body>
                    <a href="one">one</a>
                    </body>
                    </html>"""


However, the default method ``index_html`` presents a problem. Since
you can access ``index_html`` without specifying the method name in
the URL, relative links returned by ``index_html`` won't work right.

For example::

            class Example:
                """example class""""

                 def index_html(self):
                     """render default view"""
                    return """<html>
                              <head><title>one</title></head>
                              <body>
                              <a href="one">one</a><br>
                              <a href="two">two</a>
                              </body>
                              </html>"""
                 ...

If you publish an instance of the *Example* class with the URL
'http://zope/example', then the relative link to method ``one`` will
be 'http://zope/one', instead of the correct link,
'http://zope/example/one'.


Zope solves this problem for you by inserting a *base* tag between the
*head* tags in the HTML output of ``index_html`` when it is accessed
as the default method. You will probably never notice this, but if you
see a mysterious *base* tag in your HTML output, you know where it
came from. You can avoid this behavior by manually setting your own
base with a *base* tag in your ``index_html`` method output.


Response Headers
----------------

The publisher and the web server take care of setting response headers
such as *Content-Length* and *Content-Type*. Later in the chapter
you'll find out how to control these headers and also how exceptions
are used to set the HTTP response code.


Pre-Traversal Hook
------------------

The pre-traversal hook allows your objects to take special action
before they are traversed. This is useful for doing things like
changing the request. Applications of this include special
authentication controls and virtual hosting support.

If your object has a method named ``__before_publishing_traverse__``,
the publisher will call it with the current object and the request
before traversing your object. Most often your method will change the
request. The publisher ignores anything you return from the
pre-traversal hook method.

The ``ZPublisher.BeforeTraverse`` module contains some functions that
help you register pre-traversal callbacks. This allows you to perform
fairly complex callbacks to multiple objects when a given object is
about to be traversed.


Traversal and Acquisition
-------------------------

.. note::

  Simply put, acquisition means that a Zope object can acquire any
  attribute of its parents.

  For detailed information about acquisition please refer to chapter 7.

Acquisition affects traversal in several ways. The most obvious
way is in locating the next object in a path. As we discussed earlier,
the next object during traversal is often found using ``getattr``.
Since acquisition affects ``getattr``, it will affect traversal. The
upshot is that when you are traversing objects that support implicit
acquisition, you can use traversal to walk over acquired objects.

Consider the the following object hierarchy::

        from Acquisition import Implicit

        class Node(Implicit):
            ...

        fruit=Node()
        fruit.apple=Node()
        fruit.orange=Node()
        fruit.apple.strawberry=Node()
        fruit.orange.banana=Node()

When publishing these objects, acquisition can come into play. For
example, consider the URL */fruit/apple/orange*. The publisher would
traverse from *fruit*, to *apple*, and then using acquisition, it
would traverse to *orange*.

Mixing acquisition and traversal can get complex. In general you
should limit yourself to constructing URLs which use acquisition to
acquire along containment, rather than context lines.

It's reasonable to publish an object or method that you acquire from
your container, but it's probably a bad idea to publish an object or
method that your acquire from outside your container.

For example::

        from Acquisition import Implicit

        class Basket(Implicit):
            ...
            def number_of_items(self):
                """Returns the number of contained items."""
                ...

        class Vegetable(Implicit):
            ...
            def texture(self):
                """Returns the texture of the vegetable."""

        class Fruit(Implicit):
            ...
            def color(self):
                """Returns the color of the fruit."""

         basket=Basket()
         basket.apple=Fruit()
         basket.carrot=Vegetable()

The URL */basket/apple/number_of_items* uses acquisition along
containment lines to publish the ``number_of_items`` method (assuming
that *apple* doesn't have a ``number_of_items`` attribute). However,
the URL */basket/carrot/apple/texture* uses acquisition to locate the
``texture`` method from the *apple* object's context, rather than from
its container. While this distinction may be obscure, the guiding
idea is to keep URLs as simple as possible. By keeping acquisition
simple and along containment lines your application increases in
clarity, and decreases in fragility.

A second usage of acquisition in traversal concerns the request. The
publisher tries to make the request available to the published object
via acquisition. It does this by wrapping the first object in an
acquisition wrapper that allows it to acquire the request with the
name 'REQUEST'.

This means that you can normally acquire the request
in the published object like so::

        request=self.REQUEST  # for implicit acquirers

or like so::

        request=self.aq_acquire('REQUEST')  # for explicit acquirers

Of course, this will not work if your objects do not support
acquisition, or if any traversed objects have an attribute named
'REQUEST'.

Finally, acquisition has a totally different role in object
publishing related to security which we'll examine next.


Traversal and Security
----------------------

As the publisher moves from object to object during traversal it makes
security checks. The current user must be authorized to access each
object along the traversal path. The publisher controls access in a
number of ways. For more information about Zope security, see chapter
8 "Security".


Basic Publisher Security
------------------------

The publisher imposes a few basic restrictions on traversable objects.
These restrictions are the same of those for publishable objects. As
previously stated, publishable objects must have doc strings and must
not have names beginning with underscore.

The following details are not important if you are using the Zope
framework. However, if your are publishing your own modules, the rest
of this section will be helpful.

The publisher checks authorization by examining the ``__roles__``
attribute of each object as it performs traversal. If present, the
``__roles__`` attribute should be ``None`` or a list of role names. If
it is ``None``, the object is considered public. Otherwise the access to
the object requires validation.

Some objects such as functions and methods historically did not support
creating attributes. Consequently, if the object has no ``__roles__``
attribute, the publisher will look for an attribute on the object's
parent with the name of the object followed by ``__roles__``.
For example, a function named ``getInfo`` would store its roles in its
parent's ``getInfo__roles__`` attribute.

If an object has a ``__roles__`` attribute that is not empty and not
``None``, the publisher tries to find a user database to authenticate
the user. It searches for user databases by looking for an
``__allow_groups__`` attribute, first in the published object, then in
the previously traversed object, and so on until a user database is
found.

When a user database is found, the publisher attempts to validate the
user against the user database. If validation fails, then the
publisher will continue searching for user databases until the user
can be validated or until no more user databases can be found.

The user database may be an object that provides a validate
method::

  validate(request, http_authorization, roles)

where ``request`` is a mapping object that contains request information,
``http_authorization`` is the value of the *HTTP Authorization* header
or ``None`` if no authorization header was provided, and ``roles`` is a
list of user role names.

The validate method returns a user object if succeeds, and ``None`` if
it cannot validate the user. See Chapter 8 for more information on
user objects. Normally, if the validate method returns ``'None``, the
publisher will try to use other user databases, however, a user
database can prevent this by raising an exception.

If validation fails, Zope will return an HTTP header that causes your
browser to display a user name and password dialog.

If validation succeeds the publisher assigns the user object to the
request variable ``AUTHENTICATED_USER``. The publisher places no
restrictions on user objects.


Zope Security
-------------

The publisher uses acquisition to locate user folders and perform
security checks.
The upshot of this is that your published objects must inherit from
``Acquisition.Implicit`` or ``Acquisition.Explicit``.


.. note::
  For more information on *Acquisition*, visit one of the following
  resources:

  - chapter 7 "Acquisition" of this Zope Developer's Guide
  - chapter 8
    `"Acquisition" <https://zope.readthedocs.io/en/latest/zopebook/Acquisition.html>`_
    of *The Zope Book*
  - the excellent
    `readme <https://github.com/zopefoundation/Acquisition>`__
    of the "Acquisition" package

Also, when traversing, each object must be returned in an acquisition
context.
This is done automatically when traversing via ``getattr``, but you
must wrap traversed objects manually when using ``__getitem__`` and
``__bobo_traverse__``.


For example::

          class Example(Acquisition.Explicit):
              ...

              def __bobo_traverse__(self, name, request):
                  ...
                  next_object=self._get_next_object(name)
                  return  next_object.__of__(self)


Finally, traversal security can be circumvented with the
``__allow_access_to_unprotected_subobjects__`` attribute as described
in Chapter 8, "Security".


Calling the Published Object
----------------------------

The publisher marshals arguments from the request and automatically
makes them available to the published object. This allows you to
accept parameters from web forms without having to parse the
forms. Your objects usually don't have to do anything special to be
called from the web.


Consider this function::

      def greet(name):
          """Greet someone by name."""
          return "Hello, %s!" % name

You can provide the ``name`` argument to this function by calling it
with a **URL** like ``greet?name=World``. You can also call it with a **HTTP
POST request** which includes ``name`` as a form variable.

In the next sections we'll take a closer look at how the publisher
marshals arguments.


Marshalling Arguments from the Request
--------------------------------------

Zope responds to requests, specified via URL, request headers
and an optional request body. A URL consists of
various parts, among them a *path* and a *query*, see
`RFC 2396 <https://www.ietf.org/rfc/rfc2396.txt>`_ for details.

Zope uses the *path* to locate the published object
and *query* - if present - as a specification for
request parameters. Additionally, request parameters can come from
the optional request body.

Zope preprocesses the incoming request information and makes
the result available in the so called *request* object.
This way, the response generation code can access all relevant request
information in an easy and natural (pythonic) way.
Preprocessing transforms the *request parameters* into
*form variables*, a special kind of *request variables*.
They are made available via the request object's ``form`` attribute
(a ``dict``).

*Request variables* can come from various sources. If a request
variable is looked up, those sources are asked in turn
whether they know the variable; the lookup stops with the first
success. This way, a variable defined by a source
is hidden by a variable of the same name defined by a source
asked earlier.
Sources are asked in the following order:

* the lookup for ``REQUEST`` gives the request object

* the request attribute ``other`` -- it contains 
  request variables explicitly set with the method
  ``request.set``. In addition it is used as
  cache for special and lazy variables. Finally, the request
  preprocessing puts some additional variables there,
  e.g. ``URL`` (the current URL), ``PUBLISHED`` (the published object),
  ``AUTHENTICATED_USER`` (the user object, if authentication was
  successful), ``SERVER_URL`` (the initial URL part, identifying
  the server).

* special variables

   - the URL variables whose names are defined by the
     regular expressions ``URL(PATH)?([0-9]+)``
     and ``BASE(PATH)?([0-9]+)``, e.g. ``URL0``, ``URL1``, ``URLPATH0``,
     ``URL2``, ``BASE1``, ``BASEPATH1``. Their value is a prefix of the
     current URL or URL path (if the name contains ``PATH``),
     respectively. ``URL0`` gives the full URL
     and each successive *i* in ``URL``\ *i* removes a further
     path segment from the end. ``BASE1`` represents
     the URL of the "Zope root object";  each successive *i* in ``BASE``\ *i*
     adds a further path segment form the current URL.

     .. note::

        The value of the URL variables with ``PATH`` in their name
	starts with ``/``. It represents an "abs_path" "relativeURI"
	in
	`URI spec terminology
	<https://tools.ietf.org/html/rfc2396#section-5>`_.
	The URL variables without ``PATH`` in their name have
	"absoluteURI"s as values.

     .. note::

        ``BASE0`` removes the last path element from ``BASE1``
        (if any, otherwise it is ``BASE0``). It is rarely useful.

   - ``BODY`` and ``BODYFILE`` (for requests with a body).
     Their value is the request body, either as a
     (binary) string or as a file, respectively.
     
* the request attribute ``environ`` -- it contains the
  CGI environment variables and other information
  from the request headers.

* the request attribute ``common`` -- it contains variables
  defined by the request class (not the individual request).

* so called *lazy variables* -- these are "expensive"
  variables created only on first access and then
  put into ``other``. An example is ``SESSION``, representing
  Zope's session object.

* the request attribute ``form`` -- it contains the form
  variables, i.e. the result of the request parameter processing.

* the request attribute ``cookies`` -- it contains the cookies
  provided with the request.

The object publisher can use all (visible) request variables
as arguments for the published object.

.. note::
  ``str(request)`` returns a description of the request object as HTML text.
  You can use this to "view" the result of request preprocessing, e.g.
  by defining
  a ``DTML Method`` with body ``<dtml-var "str(REQUEST)">``
  (or a ``Script (Python)`` with body ``return str(container.REQUEST)``)
  and calling it via the Web or using it as form action.

The request parameters from the *query* have the form
*name*\ ``=``\ *value* and are separated by ``&``;
request parameters from a request body can have different forms
and can be separated in different ways dependent on the
request ``Content-Type``, but they, too, have a *name* and a *value*.

All request parameter names and values are strings.
A parameter value, however, often designates a value of a specific type,
e.g. an integer or a datetime. The response generating code can
be simplified significantly when it does not need to make the
type conversion itself. In addition, in some cases the request parameters
are not independent from one another but related. In those
cases it can help if the related parameters
are aggregated into a single object. Zope supports both cases but it needs
directives to guide the process. It uses *name* suffixes of the form
``:``\ *directive* to specify such directives. For example,
the parameter ``i:int=1`` tells Zope to convert the value ``'1'`` to an
integer and use it as value for form variable ``i``; the parameter sequence
``x.name:record=Peter&x.age:int:record=10`` tells Zope to construct
a record ``x`` with attributes ``name`` and ``age`` and respective values
``'Peter'`` and ``10``. There are different kinds of directives:
converter, aggregator and encoding directives.



Converters
~~~~~~~~~~

The publisher supports argument conversion via
converter directives. For example consider this
function::

        def one_third(number):
            """returns the number divided by three"""
            return number / 3.0

Calling this function will only succeed, if *number* is a number; it
will fail for a string. This is why
the publisher provides a number of converters. To signal an argument
conversion you use a converter directive.

For example, to call the above function with 66 as the argument you
can use the URL ``one_third?number:int=66``.

Some converters employ special logic for the conversion.
For example, both ``tokens`` as well as ``lines`` convert to
a list of strings but ``tokens`` splits the input at whitespace, ``lines``
at newlines.

The publisher supports many converters:

- **boolean** -- Converts a variable to ``True`` or ``False``.
  Variables that are  0, None, an empty string, or an empty sequence
  are ``False``, all others are ``True``.

- **int** -- Converts a variable to a Python integer. Also converts a
  list/tuple of variables to a list/tuple of integers.

- **long** -- Converts a variable to a Python integer. Strips the
  trailing "L" symbol at the end of the value. Also converts a
  list/tuple of variables to a list/tuple of integers.

- **float** -- Converts a variable to a Python floating point number.
  Also converts a list/tuple of variables to a list/tuple of floats.

- **string** -- Converts a variable to a native string. So the result
  is ``str``, no matter which Python version you are on.

- **ustring** -- Converts a variable to a Python unicode string.

- **bytes** -- Converts a variable to a Python bytes object/string.
  Currently, there is no way to specify the output encoding; "latin1"
  is used.

- **required** -- Raises an exception if the variable is an empty string.

- **date** -- Converts a string to a **DateTime** object. The formats
  accepted are fairly flexible, for example ``10/16/2000``, ``12:01:13
  pm``.

- **date_international** -- Converts a string to a **DateTime** object,
  but especially treats ambiguous dates as "days before month before
  year". This is useful if you need to parse non-US dates.

- **lines** -- Converts a variable to a Python list of native strings
  by splitting the string on line breaks. Also converts list/tuple of
  variables to list/tuple of native strings.

- **tokens** -- Converts a variable to a Python list of native strings
  by splitting the variable on whitespace.

- **text** -- Converts a variable to a native string with normalized line
  breaks. Different browsers on various platforms encode line
  endings differently, so this converter makes sure the line endings
  are consistent, regardless of how they were encoded by the browser.

- **ulines**, **utokens**, **utext** -- like **lines**, **tokens**,
  **text**, but always converts into unicode strings.

The full list of supported converters can be found
in ``ZPublisher.Converters.type_converters``.

If the publisher cannot convert a request parameter into the type
required by the type converter it will raise an exception.

.. note::
  Client-side validation with HTML 5 and/or JavaScript may improve
  the usability of the application, but it is never a replacement for
  server side validation.

You can combine a type converter with other directives. For example you
could create a list of integers like so::

        <input type="checkbox" name="numbers:int:list" value="1">
        <input type="checkbox" name="numbers:int:list" value="2">
        <input type="checkbox" name="numbers:int:list" value="3">


Aggregators
~~~~~~~~~~~

Aggregator directives tell Zope how to process parameters with the same or
similar names. There are aggregators with tell Zope to
aggregate parameter values into a sequence or a record
and aggregators which mark the value for a particular use, e.g.
"to be used as default value".

A request parameter can have several aggregator directives.
They are applied in turn from left to right. For example,
``x.a:int:list:record=1&x.a:int:list:record=2`` creates the
form variable ``x`` of type ``record`` with attribute ``a`` with
the list ``[1, 2]`` as value;
``x.a:int:record:list=1&x.a:int:record:list=2`` creates the form variable
``x``; its value is the list of two ``record``\ s of which the
``a`` attributes  have the value ``1`` and ``2``, respectively.
As another example,
``x:default:list=1&x:default:list=2&x:list=3`` creates request
variable ``x`` with value ``['1', '3']`` -- the ``x:default:list=2``
was replaced by ``x:list=3``. On the other hand,
``x:list:default=1&x:list:default=2&x:list=3`` creates
``x`` with value ``['3']`` -- processing the first two parameters
has created the default value ``['1', '2']`` which was replaced
by the non default ``['3']`` from the processing of the third
parameter.

.. note::

  Technically, an aggregator transforms a triple *name*, *value*
  and *aggs* into another such triple (or ``None``).
  *name* is the parameter name, *value* the parameter value
  and *aggs* the sequence of aggregators still to apply.
  Thus, an aggregator can change the parameter name, its value
  and what aggregators should still be applied.
  The aggregators are applied successively until *aggs* becomes
  empty. The final *name* and *value* is used to "update"
  the form variable collection. This "update" can be
  complex, is often recursive and is affected by the types and marks
  of the encountered values.


.. note::
  While aggregators have the purpose to aggregate
  (in the sense of coordinate) several parameters with
  similar names into a single form variable, they do not
  perform this aggregation themselves. Instead, they
  produce a wrapped value representing an isolated
  parameter. The wrapped value uses appropriate types and marks
  to achieve the desired aggregation when the final *name*, *value*
  (after the application of all aggregators) updates the form
  variable collection.
  During this update, the form variable collection
  representing the result of the aggregation of the previously
  processed parameters is recursively updated with the information
  for the current parameter. In this process, *target* subvalues from
  the collection are *updated* with corresponding
  *source* subvalues from the current parameter.
  When we use the terms "updating", "target" and "source" below,
  we reference this recursive subvalue update.

Sequence aggregators
++++++++++++++++++++

All sequence aggregators produce a sequence value -- typically
with a single element (exception **empty**: its result value
has no elements). For some sequence aggregators, the input
value must already have been a sequence.

- **list** -- Wrap *value* into a ``list`` sequence. This is typically used to
  collect all parameters with the same name into a list.

  "Updating" a target sequence with a source sequence requires that
  the source sequence has a single element, *source_value*. 
  If the source sequence is marked as "to be used in **append mode**",
  then *source_value* is appended to the target sequence.
  Otherwise (the default), it is tried to "update or replace"
  the last component of the target sequence (if any) with *source_value*;
  should this fail, *source_value* is appended to the target list.

  .. note::

    If there are two or more simple (i.e. top level and not structured)
    parameters with
    the same name they are by default collected into an
    implicitly constructed list.
    For simple parameters, the **list** aggregator is mainly used to ensure
    that the parameter leads to a list value even in the case that
    there is only one of them.

- **tuple** -- Wrap *value* into a tuple. Otherwise, it works like **list**.

- **empty** -- Transform *value* (a sequence) into an empty sequence.

  An empty sequence can be useful e.g. as default value for
  a multi select control.

- **append** -- Mark *value* (a sequence) as "to be used in **append mode**".

  **append** is used to force that the source value is appended
  to the target sequence. Without
  the **append**, the value might instead be used to "update or replace"
  the last element of the target sequence.

Record aggregator
+++++++++++++++++

The record aggregator **record** requires that *name* contains ``.``
and splits it at the last ``.`` into *var*\ ``.``\ *attr*.
It returns as name *var* and as value the record with attribute *attr* with
value *value*.

**record** is typically used to aggregate the parameters whose
name starts with *var.* into a single record variable *var*.

"Updating" a target record with a source record requires that
the source record has a single attribute *attr*; denote its value by
*attr_value*. If the target record still lacks the attribute *attr*,
add it with value *attr_value*; otherwise, try to "update or replace"
its value with *attr_value*; if this fails, the updating fails.

A related aggregator is **records**. **records** is actually
a synonym for the aggregator sequence **record** **list**.


Value marking aggregators
+++++++++++++++++++++++++

These aggregators mark their value as
to be used in a special way. A value can have at most one
mark. A value without mark is called a "normal" value.

Zope supports the following marking aggregators:

- **default** -- mark as a default value.

  "Updating" a target default value with a "normal" (source) value
  replaces the target value. "Updating" with another default value
  fails.

  This means:
  a default value can be replaced by a following "normal"
  value but not by another default value.

- **conditional** -- mark as a conditional value.

  "Updating" with a conditional source value has no effect
  if there is already a target value; "Updating"
  a conditional target value behaves identically to
  the update of a default value.

  This means:
  A conditional value is ignored if there exists already a value;
  otherwise, it behaves like a default
  value.

  .. note:

    **conditional**, like **default**, indicates some kind of
    default value. With **conditional**, the default can come
    before or after the "normal" value; with **default** it
    must come before the "normal" value (if any).

  The use of **conditional** can be indicated e.g. for
  default values from button controls: visual aspects
  can prevent you to put a button before another control

- **replace** -- mark as a replacement value.

  "Updating" with a source replacement value always replaces
  the target value. "Updating" a target replacement value
  behaves like updating a normal value.

  This means:
  a replacement value unconditionally replaces an existing value.
  After the replacement, it behaves like a normal value.

  A replacement value replaces an implicitly constructed sequence
  as a whole.

Miscellaneous aggregators
+++++++++++++++++++++++++

- **ignore_empty** -- this directive causes Zope to ignore the parameter
  if its value is empty.



Detailed examples
+++++++++++++++++

Sometimes you may wish to consolidate form data into a structure
rather than pass arguments individually. **Record arguments** allow you
to do this.

The **record** directive allows you to combine the values
of multiple form controls
into a single form variable. For example::

  <input name="date.year:record:int">
  <input name="date.month:record:int">
  <input name="date.day:record:int">

This form will result in a single variable, ``date``, with the
attributes ``year``, ``month``, and ``day``.

You can skip empty record elements with the **ignore_empty** directive.
For example::

  <input type="text" name="person.email:record:ignore_empty">

When the email form field is left blank the publisher skips over the
variable rather than returning an empty string as its value. When the
record ``person`` is returned it will not have an ``email`` attribute
if the user did not enter one.

You can also provide default values for record elements with the
**default** directive. For example::

  <input type="hidden"
         name="pizza.toppings:list:default:record" 
         value="All">
  <select multiple name="pizza.toppings:list:record">
    <option>Cheese</option>
    <option>Onions</option>
    <option>Anchovies</option>
    <option>Olives</option>
    <option>Garlic<option>
  </select>

The **default** directive allows a specified value to be inserted when the
form field is left blank. In the above example, if the user does not
select values from the list of toppings, the default value will be
used. The record ``pizza`` will have the attribute ``toppings`` and its
value will be the list containing the word "All" (if the field is
empty) or a list containing the selected toppings.

You can even marshal large amounts of form data into multiple records
with the **records** directive.

Here's an example::

  <h2>Member One</h2>
  Name:
  <input type="text" name="members.name:records"><br>
  Email:
  <input type="text" name="members.email:records"><br>
  Age:
  <input type="text" name="members.age:int:records"><br>

  <h2>Member Two</h2>
  Name:
  <input type="text" name="members.name:records"><br>
  Email:
  <input type="text" name="members.email:records"><br>
  Age:
  <input type="text" name="members.age:int:records"><br>

This form data will be marshalled into a list of records named
``members``. Each record will have a ``name``, ``email``, and ``age``
attribute.

Record marshalling provides you with the ability to create complex
forms. However, it is a good idea to keep your web interfaces as
simple as possible.

.. note::

  Records do not work with input fields of type radio as you might
  expect, as all radio fields with the same name are considered as one
  group - even if they are in different records. That means, activating
  one radio button will also deactivate all other radio buttons from
  the other records.

.. note::

    When using records please note that a checkbox
    produces a request parameter only when it is checked.
    This can seriously confuse the aggregation of request
    parameters into a list of records when the checkbox
    is the first element.

    If you want a checkbox as the first form field, you can work
    around the problem by using a hidden input field which
    provides a default value.

    **Code example with applied workaround**::

      <form action="records_parse">
          <p>
          <input type="hidden" name="index.enabled:boolean:default:records" value="" />
          <input type="checkbox" name="index.enabled:boolean:records" value="1" checked="checked" />
          <input type="text" name="index.name:records" value="index 1" />
          <p>
          <input type="hidden" name="index.enabled:boolean:default:records" value="" />
          <input type="checkbox" name="index.enabled:boolean:records" value="1" />
          <input type="text" name="index.name:records" value="index 2" />
          <p>
          <input type="submit" name="submit" value="send" />
      </form>


Specifying argument character encodings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An encoding directive specifies the encoding
of the parameter value. For example, ``x:latin1=``\ *value* tells Zope
that *value* is a ``latin1`` encoded sequence of bytes.
Typical encodings are e.g. "utf8" or  "latin1".
You can use any Python supported encoding which decodes bytes into
text.

.. note::

  Under Python 2, a form variable value is by default an ``str``
  using Zope's default encoding. However, if the parameter
  has an encoding (but not also a converter) directive, then 
  its value is ``unicode``.

HTML5 specifies how a browser can inform the server about
the encoding used for the submission of a form: if the
form contains a hidden control with name ``_charset_``, then
the browser uses its form submission encoding as value for this control.
Zope supports this feature: if it processes a ``_charset_``
parameter and its value is a Python supported encoding, then
all following parameters (names and values) are assumed
to use this encoding by default. This works only for
an "ASCII compatible" encoding (not checked).
Zope starts the overall request parameter processing with its default encoding.

HTML5 replaces characters not encodable by the encoding
used for the form submission by character references
of the form ``&#``\ *unicode code number*\ ``;``.
Zope dereferences those character references. For Python 2,
it tries to use the same approach to represent characters
not encodable by its default encoding.
This works well in page templates but might confuse at other places.


**Special cases**

If Zope's default encoding is ASCII compatible (true e.g. for "utf-8"
(the default for Zope's default encoding) and for the "ISO-8859-\*"
encoding family and their Windows equivalents),
then forms submitted from pages generated by Zope
typically do not need special encoding handling.
Exceptions are only pages which use their own encoding (different
from Zope's default encoding). In those cases or when
the form was generated from a foreign server, then Zope might
need to be informed about the applied encoding.
The easiest way is to use the ``_charset_`` feature described above::

    <input type="hidden" name="_charset_" value="cp1252">
    <input type="text" name="name:ustring">
    <input type="checkbox" name="numbers:list:int" value="1">
    <input type="checkbox" name="numbers:list:int" value="1">

.. note::

    For a full list of supported encodings, please have a look at:

    https://docs.python.org/3.7/library/codecs.html#standard-encodings


.. note::

    The **form submission encoding** can be overridden by the
    ``accept-charset`` attribute of the ``form`` tag:

    https://www.w3.org/TR/html5/sec-forms.html#selecting-a-form-submission-encoding


Method Arguments
~~~~~~~~~~~~~~~~

Normally, a request parameter is transformed into a form variable
and made available via the ``form`` attribute of the request object.
A request parameter with a
*method* directive, however, tells Zope to extend the
path used for traversal rather than to create a form variable.
Thus you can use a request parameter with method directive
to control which object is published
based on form data. For example, you might want to have a form with a select
list that calls different methods depending on the item chosen.
Similarly, you might want to have multiple submit buttons which invoke
a different method for each button.

Zope supports the following method directives:
**method** (synonym **action**), and **default_method**
(synonym **default_action**). A path extension specified by a
**default_method** directive is overridden by a
**method** directive.

The extension for the traversal path can come either
from the parameter value or the parameter name.
It comes from the parameter value, if the parameter name consists
only of directives; otherwise it is the remaining part of the
name. For example, the parameters ``:method=``\ *path*
and *path*\ ``:method=``\ *value* both extend the traversal
path by *path*.

There is special handling for HTML's image controls.
For such a control, the browser generates a pair of consecutive
request parameters with names *name*\ ``.x`` and *name*\ ``.y``
(where *name* is the name of the control) and the x and y coordinates
of the click position as values. For example, if such
a control has the name *path*\ ``:method``, then the browser
will create the two request parameters *path*\ ``:method.x=`` *x*
and *path*\ ``:method.y=`` *y*.
Zope treads this special case correctly. In the example above,
the traversal path will be extended by *path*. Note that
for an image control with method directive the traversal
extension cannot come from the parameter value (because there
are two values).

.. note::

    Technically, the method directives are implemented
    as aggregators.
    Those aggregators define a variable ``__method__``.
    The directive ``:default_method``
    is actually a synonym for ``:method:conditional``.
    If the request parameter processing gives ``__method__``
    a list value, then its last component is used
    to extend the traversal path.

    For most directives, it makes no sense to combine them
    with a method directive.


Errors during request parameter processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Errors during request parameter processing are signaled by
raising an appropriate exception. However, request
parameter processing happens at a very early stage when
application specific error handling configuration is
not yet effective. Therefore, exceptions are not reported directly;
instead, a *post traverse hook* it set up
to report them after the traversal by
raising a ``ZPublisher.interfaces.RequestParameterError``
exception. Its ``args[0]`` is
the list describing the errors
gathered during request parameter processing. Its elements are triples
*name*, *value*, *exc_info* giving the parameter name, parameter
value and the exception info (provided by ``sys.exc_info()``)
of the corresponding error.

Error analysis often uses the ``event_log`` object.
To facilitate its use in the analysis of request parameter processing
errors, the list of errors is made available as
``request.other["__request_parameter_errors__"]``.

The handling of request parameter processing errors described above
is a heuristics to ensure that in most cases the errors
are reported in an application specific way. Of course, it is
possible that those errors were sufficiently grave to 
hamper the following traversal and lead to secondary exceptions.
In those cases, appliciation specific error handling might still not
bave been set up.


Processing model for request parameter processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This section describes the processing model in some detail.
You may skip it unless you have need for an in depth understanding.

Zope processes the request parameters in
``ZPublisher.HTTPRequest.HTTPRequest.processInputs``
and ``ZPublisher.HTTPRequest.request_params.process_parameters``.


In a preliminary step the request parameters are collected
from the "query" and the optional
request body and normalized. The result is a sequence of
*name*\ /\ *value* pairs, each describing a single request parameter.
*name* is always a native string; *value* is a native string or
a ``FileUpload`` instance.

.. note::

    For Python 3, the native strings at this place are
    actually "latin1" decoded byte sequences.

Zope then sets up some variables:

``form``
  as target for the collected form variables

``form_encoding``
  the encoding used to decode parameter names
  and values. A parameter can use an
  encoding directive to override the encoding
  used to decode its value.
  ``form_encoding`` is initialized with Zope's default encoding. 

It then loops over the request parameter sequence.


For each request parameter, the processing consists of the following steps:

1. For Python 3, the parameter name is decoded using the
   current ``form_encoding``, character references are replaced.
   For Python 2, the parameter name is used as given.

2. If the name is ``_charset_`` and its value is a recognized
   encoding, then ``form_encoding`` is set to this encoding.

3. The name is split into a *key* and *directives*.
   The special names automatically created for image controls by the browser 
   are recognized and properly handled.
   The directive recognition proceeds from right to left
   and stops as soon as a directive is not recognized.
   This allows to use ``:`` as part of form variable names
   (if the following part is not recognized as a directive).

4. A ``PrimaryValue`` is constructed as initial *value* from the
   parameter value and, if present, a converter and/or an
   encoding from *directives*.

5. The aggregators from *directives* are applied from right to left.
   Each aggregator can transform *key*, *value* and/or *aggs* (i.e.
   the sequence of aggregators still to apply). Alternatively,
   it can indicate that the parameter should be ignored.
   ``form`` is (recursively) updated with the final *key* and *value* (if any).

   .. note::

      The actual implementation works with a reversed aggregator list.
      Nevertheless, the aggregators are effectively applied from left
      to right.

   The intermediate values are all ``FlexValue`` instances.
   ``FlexValue`` is a wrapper class for real values which supports
   defaults, update and aggregation. ``PrimaryValue``,
   ``SequenceValue`` and ``RecordValue`` are subclasses.

After all request parameters have been processed,
``form`` is recursively *instantiated*. This transforms all ``FlexValue``
values into "normal" values.

If the instantiated ``form`` contains a ``__method__`` variable,
it is removed and its value is used to extend the traversal path.

If the request parameter processing has encountered errors,
a "post traversal hook" is registered to report those errors
after traversal.

As a security measure, mainly for DTML use, form variables
are not only made available in the request attribute ``form``.
If a form variable contains in its name or value HTML fragments,
then a secured variant thereof is made available via
the request attribute ``taintedform``. In this variant
strings containing HTML fragments are replaced by ``TaintedString``
instances. 
DTML will automatically quote those values to give some
protection against cross site scripting attacks via HTML injection.
With the more modern page templates, all values (not only tainted ones)
are quoted by default. They typically do not use the tainted
form of the form variables.

Known issues and caveats
~~~~~~~~~~~~~~~~~~~~~~~~

1. Limitations and surprises with the construction of structured values

   Zope uses heuristics to determine whether to "update or replace" an
   existing value or whether to create a new value. The heuristics
   were chosen to do the right thing in most cases - but there
   are cases for which the heuristics fail.

   For example, updating a ``SequenceValue`` with an additional
   value first tries to "update or replace" the last existing
   component in the sequence and only if this fails appends the
   additional value to the list.

   As another example, constructing a sequence of records
   can give surprises. In this case, updating the sequence
   with an *attr* and *value* tries to "update or replace"
   the last record in the sequence. Only if this fails 
   a new record is created and appended to the list.
   This can cause problems if consecutive records do not have
   the same attribute sets - in this case, attributes destined for
   the following record may wrongly be associated with the preceeding
   one. Even if the attribute sets are equal, values are wrongly
   associated if the first attribute has a sequence value.

   You can use the **append** and **replace** directives
   to override Zope's heuristics.

2. Zope can only use an ASCII compatible encoding as form encoding
   (this includes Zope's default encoding - used as initial form encoding).
   This is not checked: if the restriction is violated, Zope
   will simply not recognize the request parameters reliably.

3. There is no way to specify the output encoding for the **bytes**
   converter directive. It uses ``latin1`` when it converts text to bytes
   (which is the case for Python 2 if the parameter
   also has an encoding directive and always for Python 3).


Exceptions
----------

When the object publisher catches an unhandled exception, it tries to
match it with a set of predifined exceptions coming from the
**zExceptions** package, such as **HTTPNoContent**, **HTTPNotFound**,
**HTTPUnauthorized**.

If there is a match, the exception gets upgraded to the matching
**zException**, which then results in a proper response returned to the
browser, including an appropriate HTTP status code.

.. note::

     For a full list of exceptions please directly refer to the
     implemented exception classes within the
     `zExceptions package
     <https://github.com/zopefoundation/zExceptions/blob/master/src/zExceptions/__init__.py>`_.


.. attention::

    When you create a custom exception, please make sure not to inherit
    from **BaseException**, but from **Exception** or one of its child
    classes, otherwise you'll run into an exception in waitress.

.. note::

    Beginning with Zope 4, a standard installation no longer comes with
    a ``standard_error_message``.

    There are two ways to catch and render an exception:

    - create a ``standard_error_message``, which can be a **DTML Method**, **DTML Document**, **Script (Python)** or **Page Template**
    - create an ``exception view``, see blog post `Catching and rendering exceptions <https://blog.gocept.com/2017/10/24/zope4-errorhandling/>`_

If the exception is not handled, it travels up the WSGI stack.

What happens then depends entirely on the possibly installed WSGI
middleware or the WSGI server. By default Zope uses **waitress**
and by default **waitress** returns an error message as follows::

  Internal Server Error

  The server encountered an unexpected internal server error

  (generated by waitress)

.. note:: **Further information:**

    `Debugging Zope applications under WSGI
    <https://zope.readthedocs.io/en/latest/wsgi.html#debugging-zope-applications-under-wsgi>`_


Exceptions and Transactions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When Zope receives a request it begins a transaction. Then it begins
the process of traversal. Zope automatically commits the transaction
after the published object is found and called. So normally each web
request constitutes one transaction which Zope takes care of for you.

If an unhandled exception is raised during the publishing process,
Zope aborts the transaction.
When a **ConflictError** occurs, Zope retries the request up to three
times by default. You can change that number in the **zope.conf** by
adding a ``max_conflict_retries`` directive.

.. note::

  For further information on transactions please refer to chapter 6
  `ZODB Persistent Components <https://zope.readthedocs.io/en/latest/zdgbook/ZODBPersistentComponents.html>`_.


Manual Access to Request and Response
-------------------------------------

Normally published objects access the request and response by listing
them in the signature of the published method. If this is not
possible you can usually use acquisition to get a reference to the
request. Once you have the request, you can always get the response
from the request like so::

  response=REQUEST.RESPONSE

The APIs of request and response can be looked up in the source code.

We'll look at a few common uses of the request and response. If you
need access to the complete API, please directly refer to the source
code.

One reason to access the request is to get more precise information
about form data. As we mentioned earlier, argument marshalling comes
from a number of places including cookies, form data, and the CGI
environment. For example, you can use the request to differentiate
between form and cookie data::

  cookies = REQUEST.cookies # a dictionary of cookie data
  form = REQUEST.form # a dictionary of form data

One common use of the response object is to set response headers.
Normally the publisher in concert with the web server will take care
of response headers for you. However, sometimes you may wish manually
control headers::

  RESPONSE.setHeader('Pragma', 'No-Cache')

Another reason to access the response is to stream response data. You
can do this with the ``write`` method::

  while 1:
      data=getMoreData() #this call may block for a while
      if not data:
          break
      RESPONSE.write(data)

Here's a final example that shows how to detect if your method is
being called from the web. Consider this function::

  def calculate(data, REQUEST=None):
      ...
      result = ...
      if REQUEST is not None:
          return "<html><p>Result: %s </p></html>" % result
      return result

The ``calculate`` function can be called from Python, and also from
the web. By including ``REQUEST=None`` in the signature you can
differentiate between being called from Python and being called form
the web.


Other Network Protocols
=======================

XML-RPC
-------

.. note::

  Code examples are valid for Python 3 only.

  If you want to use Python 2, please refer to the
  `offcial documentation <https://docs.python.org/2/library/xmlrpclib.html>`_

**XML-RPC** is a light-weight remote procedure call (RPC) protocol
that uses **XML** to encode its calls and **HTTP** as a transport
mechanism.

All objects in Zope support XML-RPC publishing. Generally you will
select a published object as the end-point and select one of its
methods as the method. For example you can call the ``getId`` method
on a Zope folder at ``http://example.com/myfolder`` like so::

  from xmlrpc.client import ServerProxy as proxy
  folder = proxy("http://example.com/myfolder")
  folder_id = folder.getId()

You can also do traversal via a dot notation.

For example::

  from xmlrpc.client import ServerProxy as proxy

  # traversal via dotted method name
  app = proxy("http://example.com/app")
  id1 = app.folderA.folderB.getId()

  # walking directly up to the published object
  folderB = proxy("http://example.com/app/folderA/folderB")
  id2 = folderB.getId()

  print(id1 == id2)

This example shows different routes to the same object publishing
call.

XML-RPC supports marshalling of basic Python types for both publishing
requests and responses. The upshot of this arrangement is that when
you are designing methods for use via XML-RPC you should limit your
arguments and return values to simple values such as Python strings,
lists, numbers and dictionaries. You should not accept or return Zope
objects from methods that will be called via XML-RPC.

.. note::

  **XML-RPC** does not support keyword arguments.


Summary
=======

Object publishing is a simple and powerful way to bring objects to the
web. Two of Zope's most appealing qualities is how it maps objects to
URLs, and you don't need to concern yourself with web plumbing. If
you wish, there are quite a few details that you can use to customize
how your objects are located and published.
