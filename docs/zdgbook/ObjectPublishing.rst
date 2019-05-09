#################
Object Publishing
#################

.. attention::

  This document is currently being reviewed and edited for the
  upcoming release of Zope 4.

.. note::

  Previously, this document contained information about access by
  FTP and WebDAV. As those functionalities were provided by the now
  removed ZServer, the related information also has been removed.

  Please directly refer to the ZServer package for further
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

The publisher marshals form data from GET and POST requests. Simple
form fields are made available as Python strings. Multiple fields
such as form check boxes and multiple selection lists become sequences
of strings. File upload fields are represented with **FileUpload**
objects. **FileUpload** objects behave like normal Python file objects
and additionally have a **filename** attribute which is the name of the
file and a **headers** attribute which is a dictionary of file upload
headers.

The publisher also marshals arguments from CGI environment variables
and cookies. When locating arguments, the publisher first looks in
CGI environment variables, then other request variables, then form
data, and finally cookies. Once a variable is found, no further
searching is done. So for example, if your published object expects
to be called with a form variable named ``SERVER_URL``, it will fail,
since this argument will be marshalled from the CGI environment first,
before the form data.

The publisher provides a number of additional special variables such
as ``URL``, ``URLn``, ``BASEn`` and others, which are derived from the
request.

Unfortunately, there is no current documentation for those variables.


Argument Conversion
-------------------

The publisher supports argument conversion. For example consider this
function::

        def one_third(number):
            """returns the number divided by three"""
            return number / 3.0

This function cannot be called from the web because by default the
publisher marshals arguments into strings, not numbers. This is why
the publisher provides a number of converters. To signal an argument
conversion you name your form variables with a colon followed by a
type conversion code.

For example, to call the above function with 66 as the argument you
can use this URL ``one_third?number:int=66`` The publisher supports
many converters:

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

- **required** -- Raises an exception if the variable is not present or
  is an empty string.

- **ignore_empty** -- Excludes a variable from the request if the
  variable is an empty string.

- **date** -- Converts a string to a **DateTime** object. The formats
  accepted are fairly flexible, for example ``10/16/2000``, ``12:01:13
  pm``.

- **date_international** -- Converts a string to a **DateTime** object,
  but especially treats ambiguous dates as "days before month before
  year". This useful if you need to parse non-US dates.

- **list** -- Converts a variable to a Python list of values, even if
  there is only one value.

- **tuple** -- Converts a variable to a Python tuple of values, even if
  there is only one value.

- **lines** -- Converts a variable to a Python list of native strings
  by splitting the string on line breaks. Also converts list/tuple of
  variables to list/tuple of native strings.

- **tokens** -- Converts a variable to a Python list of native strings
  by splitting the variable on spaces.

- **text** -- Converts a variable to a native string with normalized line
  breaks. Different browsers on various platforms encode line
  endings differently, so this converter makes sure the line endings
  are consistent, regardless of how they were encoded by the browser.

- **ulines**, **utokens**, **utext** -- like **lines**, **tokens**,
  **text**, but always converts into unicode strings.

If the publisher cannot coerce a request variable into the type
required by the type converter it will raise an error. This is useful
for simple applications, but restricts your ability to tailor error
messages. If you wish to provide your own error messages, you should
convert arguments manually in your published objects rather than
relying on the publisher for coercion.

.. note::
  Client-side validation with HTML 5 and/or JavaScript may improve
  the usability of the application, but it is never a replacement for
  server side validation.

You can combine type converters to a limited extent. For example you
could create a list of integers like so::

        <input type="checkbox" name="numbers:list:int" value="1">
        <input type="checkbox" name="numbers:list:int" value="2">
        <input type="checkbox" name="numbers:list:int" value="3">

In addition to the mentioned type converters, the publisher also supports
both method and record arguments and specifying character encodings.


Character Encodings for Arguments
---------------------------------

The publisher needs to know what character encoding was used by the
browser to encode the submitted form fields. In the past, this could
have been a complicated topic.

Nowadays, as UTF-8 is the de facto standard for encoding on the
Internet, things are much simpler.

**Best practice**

If you are using Python 3 and set the the ``charset`` meta tag to
``utf-8``, the publisher takes ``utf-8`` as the default encoding, and
thus you do not have to set it manually.


.. note::

    Further information on how to set the charset:

    https://developer.mozilla.org/de/docs/Web/HTML/Element/meta#attr-charset


.. attention::

    The encoding also can be set by the web server, which would take
    precedence over the meta tag.

**Special cases**

If you are still on Python 2 or your pages use a different encoding,
such as ``Windows-1252`` or ``ISO-8859-1``, which was the default
encoding for HTML 4, you have to add the encoding, eg ``:cp1252``, for
all argument type converts, such as follows::

    <input type="text" name="name:cp1252:ustring">
    <input type="checkbox" name="numbers:list:int:cp1252" value="1">
    <input type="checkbox" name="numbers:list:int:cp1252" value="1">

.. note::

    For a full list of supported encodings, please have a look at:

    https://docs.python.org/3.7/library/codecs.html#standard-encodings

If your pages all use a character encoding which has ASCII as a subset,
such as Latin-1, UTF-8, etc., then you do not need to specify any
character encoding for boolean, int, long, float and date types.

.. note::

    The **form submission encoding** can be overridden by the
    ``accept-charset`` attribute of the ``form`` tag:

    https://www.w3.org/TR/html5/sec-forms.html#selecting-a-form-submission-encoding


Method Arguments
----------------

Sometimes you may wish to control which object is published based on
form data. For example, you might want to have a form with a select
list that calls different methods depending on the item chosen.
Similarly, you might want to have multiple submit buttons which invoke
a different method for each button.

The publisher provides a way to select methods using form variables
through the use of the ``method`` argument type. The method type allows
the request variable ``PATH_INFO`` to be augmented using information
from a form item's name or value.

If the name of a form field is ``:method``, then the value of the field
is added to ``PATH_INFO``. For example, if the original ``PATH_INFO``
is ``foo/bar`` and the value of a ``:method`` field is ``x/y``, then
``PATH_INFO`` is transformed to ``foo/bar/x/y``. This is useful when
presenting a select list. Method names can be placed in the select
option values.

If the name of a form field **ends** in ``:method`` then the part of
the name before ``:method`` is added to ``PATH_INFO``. For example, if
the original ``PATH_INFO`` is ``foo/bar`` and there is a ``x/y:method``
field, then ``PATH_INFO`` is transformed to ``foo/bar/x/y``. In this
case, the form value is ignored. This is useful for mapping submit
buttons to methods, since submit button values are displayed and
should therefore not contain method names.


Record Arguments 
----------------

Sometimes you may wish to consolidate form data into a structure
rather than pass arguments individually. **Record arguments** allow you
to do this.

The ``record`` type converter allows you to combine multiple form
variables into a single input variable. For example::

  <input name="date.year:record:int">
  <input name="date.month:record:int">
  <input name="date.day:record:int">

This form will result in a single variable, ``date``, with the
attributes ``year``, ``month``, and ``day``.

You can skip empty record elements with the ``ignore_empty`` converter.
For example::

  <input type="text" name="person.email:record:ignore_empty">

When the email form field is left blank the publisher skips over the
variable rather than returning an empty string as its value. When the
record ``person`` is returned it will not have an ``email`` attribute
if the user did not enter one.

You can also provide default values for record elements with the
``default`` converter. For example::

  <input type="hidden"
         name="pizza.toppings:record:list:default" 
         value="All">
  <select multiple name="pizza.toppings:record:list:ignore_empty">
    <option>Cheese</option>
    <option>Onions</option>
    <option>Anchovies</option>
    <option>Olives</option>
    <option>Garlic<option>
  </select>

The ``default`` type allows a specified value to be inserted when the
form field is left blank. In the above example, if the user does not
select values from the list of toppings, the default value will be
used. The record ``pizza`` will have the attribute ``toppings`` and its
value will be the list containing the word "All" (if the field is
empty) or a list containing the selected toppings.

You can even marshal large amounts of form data into multiple records
with the ``records`` type converter. Here's an example::

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

Please note, that records do not work with input fields of type radio as you
might expect, as all radio fields with the same name are considered as one
group - even if they are in different records. That means, activating one radio
button will also deactivate all other radio buttons from the other records.

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
---------------------------

When Zope receives a request it begins a transaction. Then it begins
the process of traversal. Zope automatically commits the transaction
after the published object is found and called. So normally each web
request constitutes one transaction which Zope takes care of for you.
See Chapter 4. for more information on transactions.

If an unhandled exception is raised during the publishing process,
Zope aborts the transaction. As detailed in Chapter
4. Zope handles 'ConflictErrors' by re-trying the request up to three
times. This is done with the 'zpublisher_exception_hook'.

In addition, the error hook is used to return an error message to the
user. In Zope the error hook creates error messages by calling the
'raise_standardErrorMessage' method. This method is implemented by
'SimpleItem.Item'. It acquires the 'standard_error_message' DTML
object, and calls it with information about the exception.

You will almost never need to override the
'raise_standardErrorMessage' method in your own classes, since it is
only needed to handle errors that are raised by other components. For
most errors, you can simply catch the exceptions normally in your code
and log error messages as needed. If you need to, you should be able
to customize application error reporting by overriding the
'standard_error_message' DTML object in your application.

Manual Access to Request and Response
-------------------------------------

You do not need to access the request and response directly most of
the time. In fact, it is a major design goal of the publisher that
most of the time your objects need not even be aware that they are
being published on the web. However, you have the ability to exert
more precise control over reading the request and returning the
response.

Normally published objects access the request and response by listing
them in the signature of the published method. If this is not
possible you can usually use acquisition to get a reference to the
request. Once you have the request, you can always get the response
from the request like so::

  response=REQUEST.RESPONSE

The APIs of the request and response are covered in the API
documentation. Here we'll look at a few common uses of the request
and response.

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
can do this with the 'write' method::

  while 1:
      data=getMoreData() #this call may block for a while
      if not data:
          break
      RESPONSE.write(data)

Here's a final example that shows how to detect if your method is
being called from the web. Consider this function::

  def feedParrot(parrot_id, REQUEST=None):
      ...

      if REQUEST is not None:
          return "<html><p>Parrot %s fed</p></html>" % parrot_id

The 'feedParrot' function can be called from Python, and also from the
web. By including 'REQUEST=None' in the signature you can
differentiate between being called from Python and being called form
the web. When the function is called from Python nothing is returned,
but when it is called from the web the function returns an HTML
confirmation message.

Other Network Protocols
=======================

FTP
---

Zope comes with an FTP server which allows users to treat the Zope
object hierarchy like a file server. As covered in Chapter 3, Zope
comes with base classes ('SimpleItem' and 'ObjectManager') which
provide simple FTP support for all Zope objects. The FTP API is
covered in the API reference.

To support FTP in your objects you'll need to find a way to represent
your object's state as a file. This is not possible or reasonable for
all types of objects. You should also consider what users will do
with your objects once they access them via FTP. You should find out
which tools users are likely to edit your object files. For example,
XML may provide a good way to represent your object's state, but it
may not be easily editable by your users. Here's an example class
that represents itself as a file using RFC 822 format::

  from rfc822 import Message
  from cStringIO import StringIO

  class Person(...):

      def __init__(self, name, email, age):
          self.name=name
          self.email=email
          self.age=age

      def writeState(self):
          "Returns object state as a string"
          return "Name: %s\nEmail: %s\nAge: %s" % (self.name,
                                                   self.email, 
                                                   self.age)
      def readState(self, data):
          "Sets object state given a string"
          m=Message(StringIO(data))
          self.name=m['name']
          self.email=m['email']
          self.age=int(m['age'])

The 'writeState' and 'readState' methods serialize and unserialize the
'name', 'age', and 'email' attributes to and from a string. There are
more efficient ways besides RFC 822 to store instance attributes in a
file, however RFC 822 is a simple format for users to edit with text
editors.

To support FTP all you need to do at this point is implement the
'manage_FTPget' and 'PUT' methods. For example::

  def manage_FTPget(self):
      "Returns state for FTP"
      return self.writeState()

  def PUT(self, REQUEST):
      "Sets state from FTP"
       self.readState(REQUEST['BODY'])

You may also choose to implement a 'get_size' method which returns the
size of the string returned by 'manage_FTPget'. This is only
necessary if calling 'manage_FTPget' is expensive, and there is a more
efficient way to get the size of the file. In the case of this
example, there is no reason to implement a 'get_size' method.

One side effect of implementing 'PUT' is that your object now supports
HTTP PUT publishing. See the next section on WebDAV for more
information on HTTP PUT.

That's all there is to making your object work with FTP. As you'll
see next WebDAV support is similar.

WebDAV
------

WebDAV is a protocol for collaboratively edit and manage files on
remote servers. It provides much the same functionality as FTP, but
it works over HTTP.

It is not difficult to implement WebDAV support for your objects.
Like FTP, the most difficult part is to figure out how to represent
your objects as files.

Your class must inherit from 'webdav.Resource' to get basic DAV
support. However, since 'SimpleItem' inherits from 'Resource', your
class probably already inherits from 'Resource'. For container
classes you must inherit from 'webdav.Collection'. However, since
'ObjectManager' inherits from 'Collection' you are already set so long
as you inherit from 'ObjectManager'.

In addition to inheriting from basic DAV classes, your classes must
implement 'PUT' and 'manage_FTPget'. These two methods are also
required for FTP support. So by implementing WebDAV support, you also
implement FTP support.

The permissions that you assign to these two methods will control the
ability to read and write to your class through WebDAV, but the
ability to see your objects is controlled through the "WebDAV access"
permission.

Supporting Write Locking
------------------------

Write locking is a feature of WebDAV that allows users to put lock on
objects they are working on. Support write locking s easy. To
implement write locking you must assert that your lass implements the
'WriteLockInterface'. For example::

  from webdav.WriteLockInterface import WriteLockInterface

  class MyContentClass(OFS.SimpleItem.Item, Persistent):
      __implements__ = (WriteLockInterface,)

It's sufficient to inherit from 'SimpleItem.Item', since it inherits
from 'webdav.Resource', which provides write locking long with other
DAV support.

In addition, your 'PUT' method should begin with calls to dav__init'
and 'dav_simpleifhandler'. For example::

 def PUT(self, REQUEST, RESPONSE):
     """
     Implement WebDAV/HTTP PUT/FTP put method for this object.
     """
     self.dav__init(REQUEST, RESPONSE)
     self.dav__simpleifhandler(REQUEST, RESPONSE)
     ...

Finally your class's edit methods should check to determine whether
your object is locked using the 'ws_isLocked' method. If someone
attempts to change your object when it is locked you should raise the
'ResourceLockedError'. For example::

  from webdav import ResourceLockedError

  class MyContentClass(...):
      ...

      def edit(self, ...):
          if self.ws_isLocked():
              raise ResourceLockedError
          ...

WebDAV support is not difficult to implement, and as more WebDAV
editors become available, it will become more valuable. If you choose
to add FTP support to your class you should probably go ahead and
support WebDAV too since it is so easy once you've added FTP support.

XML-RPC
-------

`XML-RPC <http://www.xmlrpc.com>`_ is a light-weight Remote Procedure
Call protocol that uses XML for encoding and HTTP for transport.
Fredrick Lund maintains a Python <XML-RPC module
<http://www.pythonware.com/products/xmlrpc>`_ .

All objects in Zope support XML-RPC publishing. Generally you will
select a published object as the end-point and select one of its
methods as the method. For example you can call the 'getId' method on
a Zope folder at 'http://example.com/myfolder' like so::

  import xmlrpclib
  folder = xmlrpclib.Server('http://example.com/myfolder')
  ids = folder.getId()

You can also do traversal via a dotted method name. For example::

  import xmlrpclib

  # traversal via dotted method name
  app = xmlrpclib.Server('http://example.com/app')
  id1 = app.folderA.folderB.getId()

  # walking directly up to the published object
  folderB = xmlrpclib.Server('http://example.com/app/folderA/folderB')
  id2 = folderB.getId()

  print id1 == id2

This example shows different routes to the same object publishing
call.

XML-RPC supports marshalling of basic Python types for both publishing
requests and responses. The upshot of this arrangement is that when
you are designing methods for use via XML-RPC you should limit your
arguments and return values to simple values such as Python strings,
lists, numbers and dictionaries. You should not accept or return Zope
objects from methods that will be called via XML-RPC.


XML-RPC does not support keyword arguments. This is a problem if your
method expect keyword arguments. This problem is noticeable when
calling DTMLMethods and DTMLDocuments with XML-RPC. Normally a DTML
object should be called with the request as the first argument, and
additional variables as keyword arguments. You can get around this
problem by passing a dictionary as the first argument. This will
allow your DTML methods and documents to reference your variables with
the 'var' tag. However, you cannot do the following::

  <dtml-var expr="REQUEST['argument']">

Although the following will work::

  <dtml-var expr="_['argument']">

This is because in this case arguments *are* in the DTML namespace,
but they are not coming from the web request.

In general it is not a good idea to call DTML from XML-RPC since DTML
usually expects to be called from normal HTTP requests.

One thing to be aware of is that Zope returns 'false' for published
objects which return None since XML-RPC has no concept of null.

Another issue you may run into is that 'xmlrpclib' does not yet
support HTTP basic authentication. This makes it difficult to call
protected web resources. One solution is to patch 'xmlrpclib'.
Another solution is to accept authentication credentials in the
signature of your published method.

Summary
=======

Object publishing is a simple and powerful way to bring objects to the
web. Two of Zope's most appealing qualities is how it maps objects to
URLs, and you don't need to concern yourself with web plumbing. If
you wish, there are quite a few details that you can use to customize
how your objects are located and published.
