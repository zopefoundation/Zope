########
Security
########

Introduction
============

A typical web application needs to be securely managed.  Different
types of users need different kinds of access to the components that
make up an application. To this end, Zope includes a comprehensive
set of security features.  This chapter's goal is to shed light on
Zope security in the context of Zope Product development.  For a more
fundamental overview of Zope security, you may wish to refer to the
*Zope Book* Chapter `"Users and Security"
<https://zope.readthedocs.io/en/latest/zopebook/Security.html>`_.
Before diving into this
chapter, you should have a basic understanding of how to build Zope
Products as well as an understanding of how the Zope object publisher
works. This is covered in :doc:`ObjectPublishing`.


Security Architecture
=====================

The Zope security architecture is built around a *security policy*,
which you can think of as the "access control philosophy" of
Zope. This policy arbitrates the decisions Zope makes about whether
to allow or deny access to any particular object defined within the
system.


How The Security Policy Relates to Zope's Publishing Machinery
--------------------------------------------------------------

When access to Zope is performed via HTTP or WebDAV, Zope's
publishing machinery consults the security policy in order to
determine whether to allow or deny access to a visitor for a
particular object.  For example, when a user visits the root
``index_html`` object of your site via HTTP, the security policy is
consulted by ``ZPublisher`` to determine whether the user has
permission to view the ``index_html`` object itself.

On top of that, the publisher also defines other rules to determine
which objects can be published. The most important of these is that 
objects which are published must have a docstring.

For more information on this topic, see the chapter on 
:doc:`ObjectPublishing`.


How The Security Policy Relates to Restricted Code
--------------------------------------------------

*Restricted code* is generally any sort of logic that may be edited
remotely (through the Web, via WebDAV or by other means). DTML
Methods, SQLMethods, Python Scripts and Page Templates are examples of
restricted code.

When restricted code runs, any access to objects integrated with Zope
security is arbitrated by the security policy. For example if you
write a bit of restricted code with a line that attempts to
manipulate an object you don't have sufficient permission to use, the
security policy will deny access to the object.  This
is accomplished by raising an ``Unauthorized`` exception, which is a
Python exception caught by the publisher and handed to a user folder,
which will then attempt to get user credentials before continuing with
the request.  The particular code used to attempt to obtain the
credentials is determined by the User Folder "closest" (folder-wise)
to the object being accessed.


``Unauthorized`` Exceptions and Through-The-Web Code
----------------------------------------------------

The security policy infrastructure will raise an ``Unauthorized``
exception automatically when access to an object is denied.  When an
``Unauthorized`` exception is raised within Zope, it is handled in a
sane way by Zope, generally by having the User Folder prompt the user
for login information.  Using this functionality, it's possible to
protect Zope objects through access control, only prompting the user
for authentication when it is necessary to perform an action which
requires privilege.

An example of this behavior can be witnessed within the Zope
Management interface itself.  The management interface prompts you to
log in when visiting, for example, the ``/manage`` method of any Zope
object.  This is due to the fact that an anonymous user is not
generally authorized to use the management
interface.  If you're using Zope in the default configuration with
the default User Folder, it prompts you to provide login information
via an HTTP basic authentication dialog.


How The Security Policy Relates To Unrestricted Code
----------------------------------------------------

There are also types of *unrestricted code* in Zope, where the logic
is not constrained by the security policy. Examples of unrestricted
code are the methods of Python classes that implement the objects in
Python filesystem-based add-on components.  Another example of
unrestricted code can be found in External Method objects (must be
installed separately), which are defined in files on the filesystem.
These sorts of code are allowed to run
`unrestricted` because access to the file system is required to
define such logic.  Zope assumes that code defined on the filesystem
is "trusted", while code defined "through the web" is not.  All
filesystem-based code in Zope is unrestricted code.

We'll see later that while the security policy does not constrain
what your unrestricted code does, it can and should be used to
control the ability to *call* your unrestricted code from within a
restricted-code environment.


Details Of The Default Zope Security Policy
-------------------------------------------

In short, the default Zope security policy ensures the following:

- access to an object which does not have any associated security
  information is always denied.

- access to an object whose name begins with the underscore
  character ``_`` is always denied.

- if the object has a security assertion declaring it *private*, then
  access will be denied.

- if the object has a security assertion declaring it *public* , then
  access will be granted.

- if an object is associated with a permission, access is granted or
  denied based on the user's roles.  If a user has a role which has
  been granted the permission in question, access is granted.  If the
  user does not possess a role that has been granted the permission
  in question, access is denied.

- objects can only be published if they have a doc string. This
  restriction exists outside the security policy itself. 


As we delve further into Zope security within this chapter, we'll see
exactly what it means to associate security information with an
object.


Overview Of Using Zope Security Within Your Product
---------------------------------------------------

Of course, now that we know what the Zope security policy is, we need
to know how our Product can make use of it.  Zope developers leverage
the Zope security policy primarily by making security declarations
related to methods and objects within their Products.  Using security
assertions, developers may deny or allow all types of access to a
particular object or method unilaterally, or they may protect access
to Zope objects more granularly by using permissions to grant or deny
access based on the roles of the requesting user to the same objects
or methods.

For a more fundamental overview of Zope users, roles, and
permissions, see the section titled "Authorization, Roles and
Permissions" in the `Security Chapter of the Zope Book
<https://zope.readthedocs.io/en/latest/zopebook/Security.html>`_.


Security Declarations In Zope Products
--------------------------------------

Zope security declarations allow developers to make security
assertions about a Product-defined object and its methods.
Security declarations come in three basic forms.  These are:

- public -- allow anybody to access the protected object
  or method

- private -- deny anyone access to the protected object or
  method

- protected -- protect access to the object or method with a
  permission

We'll see how to actually define these security assertions a
little later in this chapter.  In the meantime, just know that
security declarations are fundamental to Zope Product security,
and they can be used to protect access to an object by
associating it with a permission.  We will refer to security
declarations as `declarations` and `assertions` interchangeably
within this chapter.


Permissions In Zope Products
============================

A permission is the smallest unit of access to an object in Zope,
roughly equivalent to the atomic permissions on files seen in Windows
NT or UNIX: R (Read), W(Write), X(Execute), etc. However, unlike
these types of mnemonic permissions shared by all sorts of different
file types in an operating system product, in Zope, a permission
usually describes a fine-grained logical operation which takes place
upon an object, such as "View Management Screens" or "Add
Properties".

Zope administrators associate these permissions with *roles*, which
they grant to Zope users.  Thus, declaring a protection assertion on
a method of "View management screens" ensures that only users who
possess roles which have been granted the "View management screens"
permission are able to perform the action that the method defines.

It is important to note that Zope's security architecture dictates
that roles and users remain the domain of administrators, while
permissions remain the domain of developers.  Developers of Products
should not attempt to define roles or users, although they may (and
usually must) define permissions.  Most importantly, a Zope
administrator who makes use of your product should have the "last
word" as regards which roles are granted which permissions, allowing
her to protect her site in a manner that fits her business goals.

Permission names are strings, and these strings are currently
arbitrary.  There is no permission hierarchy, or list of "approved
permissions".  Developers are encouraged to reuse Zope core
permissions (e.g. "View", "Access contents information") where
appropriate, or they may create their own as the need arises.  It is
generally wise to reuse existing Zope permission names unless you
specifically need to define your own.  For a list of existing Zope
core permissions, see :doc:`AppendixA`.

Permissions are often tied to method declarations in Zope.  Any
number of method declarations may share the same permission.  It's
useful to declare the same permission on a set of methods which can
logically be grouped together.  For example, two methods which return
management forms for the object can be provided with the same
permission, "View management screens".  Likewise, two entirely
different objects can share a permission name to denote that the
operation that's being protected is fundamentally similar.  For
instance, most Product-defined objects reuse the Zope "View"
permission, because most Zope objects need to be viewed in a web
browser.  If you create an addable Zope class named `MyObject`, it
doesn't make much sense to create a permission "View MyObject",
because the generic "View" permission may be reused for this action.

There is an exception to the "developers should not try to define
roles" rule inasmuch as Zope allows developers to assign `default
roles` to a permission.  This is primarily for the convenience of the
Zope administrator, as default roles for a permission cause the Zope
security machinery to provide a permission to a role *by default*
when instances of a Product class are encountered during security
operations.  For example, if your Product defines a permission "Add
Poll Objects", this permission may be associated with a set of
default roles, perhaps "Manager".  Default roles in Products should
not be used against roles other than "Manager", "Anonymous", "Owner",
and "Authenticated" (the four default Zope roles), as other roles are
not guaranteed to exist in every Zope installation.

Using security assertions in Zope is roughly analogous to assigning
permission bit settings and ownership information to files in a UNIX
or Windows filesystem.  Protecting objects via permissions allows
developers and administrators to secure Zope objects independently of
statements made in application code.


Implementing Security In Python Products
========================================

Security Assertions
-------------------

You may make several kinds of security assertions at the Python
level.  You do this to declare accessibility of methods and
subobjects of your classes. Three of the most common assertions that
you'll want to make on your objects are:

- this object is **public** (always accessible)

- this object is **private** (not accessible by restricted code or by
  URL traversal)

- this object is **protected** by a specific permission

There are a few other kinds of security assertions that are 
much less frequently used but may be needed in some cases:

- asserting that access to subobjects that do not have explicit
  security information should be allowed rather than denied.

- asserting what sort of protection should be used when determining
  access to an *object itself* rather than a particular method of the
  object

It is important to understand that security assertions made in your
Product code *do not* limit the ability of the code that the
assertion protects.  Assertions only protect *access to this code*.
The code which constitutes the body of a protected, private, or
public method of a class defined in a Zope filesystem-based Product runs
completely unrestricted, and is not subject to security constraints
of any kind within Zope.  An exception to this rule occurs when
filesystem-based-Product code calls a "through the web" method such as a
Python Script or a DTML Method.  In this case, the security
constraints imposed by these objects respective to the current
request are obeyed.


When Should I Use Security Assertions?
--------------------------------------

If you are building an object that will be used from a Page Template or
other restricted code, or that will be accessible directly through the web
(or other remote protocols such as WebDAV) then you need to
define security information for your object.


Making Security Assertions
--------------------------

As a Python developer, you make security assertions in your Python
classes using ``SecurityInfo`` objects. A ``SecurityInfo`` object
provides the interface for making security assertions about an object
in Zope.

The convention of placing security declarations inside Python code
may at first seem a little strange if you're used to "plain old
Python" which has no notion at all of security declarations.  But
because Zope provides the ability to make these security assertions
at such a low level, the feature is ubiquitous throughout Zope,
making it easy to make these declarations once in your code, usable
site-wide without much effort.


Class Security Assertions
=========================

The most common kind of ``SecurityInfo`` you will use as a component
developer is the ``ClassSecurityInfo`` object.  You use
``ClassSecurityInfo`` objects to make security assertions about methods
on your classes.

Classes that need security assertions are any classes that define
methods that can be called "through the web".  This means any methods
that can be called directly with URL traversal, from Page templates, DTML
Methods, or from Python Script objects.


Declaring Class Security
------------------------

When writing the classes in your product, you create a
``ClassSecurityInfo`` instance *within each class that needs to play
with the security model*. You then use the ``ClassSecurityInfo`` object
to make assertions about your class, its subobjects and its methods.

The ``ClassSecurityInfo`` class is defined in the ``AccessControl``
package of the Zope framework. To declare class security information
create a ``ClassSecurityInfo`` class attribute named ``security``.  The
name ``security`` is used for consistency and for the benefit of new
component authors, who often learn from looking at other people's
code. You do not have to use the name ``security`` for the security
infrastructure to recognize your assertion information, but it is
recommended as a convention.

The ``ClassSecurityInfo`` object can be used to declare access in two ways,
as a `function decorator` or by calling the required method explicitly.

For example::

  from AccessControl import ClassSecurityInfo

  class Mailbox(ObjectManager):
    """A mailbox object that contains mail message objects."""

    # Create a SecurityInfo for this class. We will use this 
    # in the rest of our class definition to make security 
    # assertions.
    security = ClassSecurityInfo()

    # Here is an example of a security assertion using a decorator.
    # We are declaring that access to messageCount is public.
    @security.public
    def messageCount(self):
      """Return a count of messages."""
      return len(self._messages)


In the example above we decorated the ``messageCount`` method with the
decorator method ``security.public`` of the ``ClassSecurityInfo`` instance
to declare that access to the ``messageCount`` method be public. To make
security assertions for your object, you just call the appropriate methods
of the ``ClassSecurityInfo`` object, passing the appropriate information for
the assertion you are making.

The ``ClassSecurityInfo`` approach has a number of benefits. A major
benefit is that it is very explicit, it allows your security
assertions to appear in your code near the objects they protect,
which makes it easier to assess the state of protection of your code
at a glance. The ``ClassSecurityInfo`` interface also allows you as a
component developer to ignore the implementation details in the
security infrastructure and protects you from future changes in those
implementation details.

Let's expand on the example above and see how to make the most common
security assertions using the ``SecurityInfo`` interface.

To assert that a method is *public* (anyone may call it) you may
use the ``public`` decorator::

  @security.public
  def myMethod(self):
      ...

To assert that a method is *private* you may use the ``private``
decorator::

  @security.private
  def myMethod(self):
      ...

To assert that a method or subobject is *protected* by a particular
permission, you use the ``protected`` decorator, passing a permission name::

  @security.protected(permissionName)
  def myMethod(self):
      ...

If you have lots of methods you want to protect under the same
permission, you can pass as many methodNames ase you want to a call to
the ``declareProtected`` method::

  security.declareProtected(permissionName, methodName1,
    methodName2, methodName3, ...)

Passing multiple names like this works for all of the non-decorator
``declare`` security methods (``declarePublic``, ``declarePrivate``, and
``declareProtected``).


Deciding To Use Protected vs. Public or Private
-----------------------------------------------

If the method you're making the security declaration against is
innocuous, and you're confident that its execution will not
disclose private information nor make inappropriate changes to
system state, you should declare the method public.

If a method should never be run under any circumstances via
traversal or via through-the-web code, the method should be
declared private.  This is the default if a method has no
security assertion, so you needn't explicitly protect
unprotected methods unless you've used ``setDefaultAccess`` to set
the object's default access policy to ``allow`` (detailed in
*Other Assertions* below).

If the method should only be executable by a certain class of
users, you should declare the method protected.


A Class Security Example
------------------------

Let's look at an expanded version of our 'Mailbox' example that makes
use of each of these types of security assertions::

  from AccessControl import ClassSecurityInfo
  from AccessControl.class_init import InitializeClass


  class Mailbox(ObjectManager):
      """A mailbox object."""

      # Create a SecurityInfo for this class
      security = ClassSecurityInfo()

      security.declareProtected('View management screens', 'manage')
      manage = HTMLFile('mailbox_manage', globals())

      @security.public
      def messageCount(self):
          """Return a count of messages."""
          return len(self._messages)

      # protect 'listMessages' with the 'View Mailbox' permission
      @security.protected('View Mailbox')
      def listMessages(self):
          """Return a sequence of message objects."""
          return self._messages[:]

      @security.private
      def getMessages(self):
          self._messages=GoGetEm()
          return self._messages

  # call this to initialize framework classes, which
  # does the right thing with the security assertions.
  InitializeClass(Mailbox)

Note the last line in the example.  In order for security assertions
to be correctly applied to your class, you must call the global class
initializer ``InitializeClass`` for all classes that have
security information. This is very important - the global initializer
does the "dirty work" required to ensure that your object is
protected correctly based on the security assertions that you have
made. If you don't run it on the classes that you've protected with
security assertions, the security assertions will not be effective.


Deciding Permission Names For Protected Methods
-----------------------------------------------

When possible, you should make use of an existing Zope permission
within ``protected``/``declareProtected`` assertions.  A list of the
permissions which are available in a default Zope installation is available
within :doc:`AppendixA`.  When it's not possible to reuse an existing
permission, you should choose a permission name which is a verb or a
verb phrase.


Object Assertions
-----------------

Often you will also want to make a security assertion on the *object
itself*. This is important for cases where your objects may be
accessed in a restricted environment such as a Page Template or a
Python Script. Consider the example Page Template code::

  <span tal:content="python: some_method(someObject)">Result</span>

Here we are trying to call ``some_method``, passing the object
``someObject``. When this is evaluated in the restricted
environment, the security policy will attempt to validate access to
both ``some_method`` and ``someObject``. We've seen how to make
assertions on methods - but in the case of ``someObject`` we are not
trying to access any particular method, but rather the *object
itself* (to pass it to ``some_method``). Because the security machinery
will try to validate access to ``someObject``, we need a way to let the
security machinery know how to handle access to the object itself in
addition to protecting its methods.

To make security assertions that apply to the *object itself* you
call methods on the ``SecurityInfo`` object that are analogous to the
three that we have already seen::

  security.declareObjectPublic()

  security.declareObjectPrivate()

  security.declareObjectProtected(permissionName)

The meaning of these methods is the same as for the method variety,
except that the assertion is made on the object itself.


An Object Assertion Example
---------------------------

Here is the updated 'Mailbox' example, with the addition of a
security assertion that protects access to the object itself with the
`View Mailbox` permission::

  from AccessControl import ClassSecurityInfo
  from AccessControl.class_init import InitializeClass

  class Mailbox(ObjectManager):
      """A mailbox object."""

      # Create a SecurityInfo for this class
      security = ClassSecurityInfo()

      # Set security for the object itself
      security.declareObjectProtected('View Mailbox')

      security.declareProtected('View management screens', 'manage')
      manage=HTMLFile('mailbox_manage', globals())

      @security.public
      def messageCount(self):
          """Return a count of messages."""
          return len(self._messages)

      # protect 'listMessages' with the 'View Mailbox' permission
      @security.protected('View Mailbox')
      def listMessages(self):
          """Return a sequence of message objects."""
          return self._messages[:]

      @security.private
      def getMessages(self):
          self._messages=GoGetEm()
          return self._messages

  # call this to initialize framework classes, which
  # does the right thing with the security assertions.
  InitializeClass(Mailbox)


Other Assertions
----------------

The ``SecurityInfo`` interface also supports the less common
security assertions noted earlier in this document.

To assert that access to subobjects that do not have explicit
security information should be *allowed* rather than *denied* by
the security policy, use::

  security.setDefaultAccess('allow')

This assertion should be used with caution. It will effectively
change the access policy to "allow-by-default" for all
attributes in your object instance (not just class attributes)
that are not protected by explicit assertions.  By default, the
Zope security policy flatly denies access to attributes and
methods which are not mentioned within a security assertion.
Setting the default access of an object to "allow" effectively
reverses this policy, allowing access to all attributes and
methods which are not explicitly protected by a security
assertion.

``setDefaultAccess`` applies to attributes that are simple Python
types as well as methods without explicit protection. This is
important because some mutable Python types like ``list`` or ``dict``
can then be modified by restricted code. Setting default access to
"allow" also affects attributes that may be defined by the base
classes of your class, which can lead to security holes if you
are not sure that the attributes of your base classes are safe
to access.

Setting the default access to "allow" should only be done if you
are sure that all of the attributes of your object are safe to
access, since the current architecture does not support using
explicit security assertions on non-method attributes.


What Happens When You Make A Mistake Making ``SecurityInfo`` Declarations?
--------------------------------------------------------------------------

It's possible that you will make a mistake when making
``SecurityInfo`` declarations.  For example, it is not legal to
declare two conflicting permissions on a method::

  class Foo(SimpleItem):
      security = ClassSecurityInfo()

      meta_type = 'Foo'

      @security.protected('View foos')
      def index_html(self):
          """ make index_html web-publishable """
          return '<html><body>hi!</body></html>'

  security.declareProtected('View', 'index_html')
  # whoops, declared a conflicting permission on index_html!

When you make a mistake like this, the security machinery will
accept the *first* declaration made in the code and will write
an error to the Zope debug log upon encountering the second and
following conflicting declarations during class initialization.
It's similarly illegal to declare a method both private and
public, or to declare a method both private and protected, or to
declare a method both public and protected. A similar error will
be raised in all of these cases.

Note that Zope *will not* warn you if you misspell the name of
a method in a ``declareProtected``, ``declarePublic``, or
``declarePrivate`` call.  For instance, you try to protect the
``index_html`` method with the ``View`` permission and make a mistake,
spelling the name ``index_html`` as ``inde_html``, like so::

  security.declareProtected('View', 'inde_html')
  # whoops, declared a permission assertion for 'inde_html'
  # when I really wanted it to be 'index_html'!
  def index_html(self):
      """ make index_html web-publishable """
      return '<html><body>hi!</body></html>'

You'll need to track down these kinds of problems yourself.


Setting Default Roles For Permissions
-------------------------------------

When defining operations that are protected by permissions, one thing
you commonly want to do is to arrange for certain roles to be
associated with a particular permission *by default* for instances of
your object.

For example, say you are creating a *News Item* object. You want
``Anonymous`` users to have the ability to view news items by default;
you don't want the site manager to have to explicitly change the
security settings for each *News Item* just to give the ``Anonymous``
role ``View`` permission.

What you want as a programmer is a way to specify that certain roles
should have certain permissions by default on instances of your
object, so that your objects have sensible and useful security
settings at the time they are created. Site managers can always
*change* those settings if they need to, but you can make life easier
for the site manager by setting up defaults that cover the common
case by default.

As we saw earlier, the ``SecurityInfo`` interface provided a way to
associate methods with permissions. It also provides a way to
associate a permission with a set of default roles that should have
that permission on instances of your object.

To associate a permission with one or more roles, use the following::

  security.setPermissionDefault(permissionName, rolesList)

The *permissionName* argument should be the name of a permission that
you have used in your object and *rolesList* should be a sequence
(tuple or list) of role names that should be associated with
*permissionName* by default on instances of your object.

Note that it is not always necessary to use this method. All
permissions for which you did not set defaults using
``setPermissionDefault`` are assumed to have a single default role of
``Manager``.  Notable exceptions to this rule include ``View`` and
``Access contents information``, which always have the default roles
``Manager`` and ``Anonymous``.

The ``setPermissionDefault`` method of the ``SecurityInfo`` object should
be called only once for any given permission name.


An Example of Associating Default Roles With Permissions
--------------------------------------------------------

Here is our ``Mailbox`` example, updated to associate the ``View
Mailbox`` permission with the roles ``Manager`` and ``Mailbox Owner``
by default::

  from AccessControl import ClassSecurityInfo
  from AccessControl.class_init import InitializeClass

  class Mailbox(ObjectManager):
      """A mailbox object."""

      # Create a SecurityInfo for this class
      security = ClassSecurityInfo()

      # Set security for the object itself
      security.declareObjectProtected('View Mailbox')

      security.declareProtected('View management screens', 'manage')
      manage = DTMLFile('mailbox_manage', globals())

      @security.public
      def messageCount(self):
          """Return a count of messages."""
          return len(self._messages)

      @security.protected('View Mailbox')
      def listMessages(self):
          """Return a sequence of message objects."""
          return self._messages[:]

      security.setPermissionDefault('View Mailbox',
                                    ('Manager', 'Mailbox Owner'))

  # call this to initialize framework classes, which
  # does the right thing with the security assertions.
  InitializeClass(Mailbox)


What Happens When You Make A Mistake Declaring Default Roles?
-------------------------------------------------------------

It's possible that you will make a mistake when making default roles
declarations.  For example, it is not legal to declare two
conflicting default roles for a permission::

  class Foo(SimpleItem):
      security = ClassSecurityInfo()

      meta_type = 'Foo'

      @security.protected('View foos')
      def index_html(self):
          """ """
          return '<html><body>hi!</body></html>'

      security.setPermissionDefault('View foos', ('Manager',))

      security.setPermissionDefault('View foos', ('Anonymous',))
      # whoops, conflicting permission defaults!

When you make a mistake like this, the security machinery will accept
the *first* declaration made in the code and will write an error to
the Zope debug log about the second and following conflicting
declarations upon class initialization.


What Can (And Cannot) Be Protected By Class Security Info?
----------------------------------------------------------

It is important to note what can and cannot be protected using the
``ClassSecurityInfo`` interface. First, the security policy relies on
*Acquisition* to aggregate access control information, so any class
that needs to work in the security policy must have either
``Acquisition.Implicit`` or ``Acquisition.Explicit`` in its base class
hierarchy.

The current security policy supports protection of methods and
protection of subobjects that are instances. It does *not* currently
support protection of simple attributes of basic Python types like
``string``, ``int``, ``list`` or ``dict``. For instance::

  from AccessControl import ClassSecurityInfo
  from OFS.ObjectManager import ObjectManager


  # We subclass ObjectManager, which has Acquisition in its
  # base class hierarchy, so we can use SecurityInfo.

  class MyClass(ObjectManager):
      """example class"""

      # Create a SecurityInfo for this class
      security = ClassSecurityInfo()

      # Set security for the object itself
      security.declareObjectProtected('View')

      # This is ok, because subObject is an instance
      security.declareProtected('View management screens', 'subObject')
      subObject = MySubObject()

      # This is ok, because sayHello is a method
      @security.public
      def sayHello(self):
          """Return a greeting."""
          return 'hello!'

      # This will not work, because foobar is not a method
      # or an instance - it is a standard Python type
      security.declarePublic('foobar')
      foobar = 'some string'

Keep this in mind when designing your classes. If you need simple
attributes of your objects to be accessible (say via `TAL` or `DTML`),
then you need to use the ``setDefaultAccess`` method of ``SecurityInfo``
in your class to allow this (see the note above about the security
implications of this). In general, it is always best to expose the
functionality of your objects through methods rather than exposing
attributes directly.

Note also that the actual ``ClassSecurityInfo`` instance you use to
make security assertions is implemented such that it is *never*
accessible from restricted code or through the Web, so no action on the
part of the programmer is required to protect it.


Inheritance And Class Security Declarations
-------------------------------------------

Python inheritance can prove confusing in the face of security
declarations.

If a base class which has already been run through ``InitializeClass``
is inherited by a subclass, nothing special needs to be done to
protect the base class' methods within the subclass unless you wish
to modify the declarations made in the base class.  The security
declarations "filter down" into the subclass.

On the other hand, if a base class hasn't been run through the global
class initializer (``InitializeClass``), you need to proxy its security
declarations in the subclass if you wish to access any of its
methods within through-the-web code or via URL traversal.

In other words, security declarations that you make using
``ClassSecurityInfo`` objects effect instances of the class upon which
you make the declaration. You only need to make security declarations
for the methods and subobjects that your class actually *defines*. If
your class inherits from other classes, the methods of the base
classes are protected by the security declarations made in the base
classes themselves. The only time you would need to make a security
declaration about an object defined by a base class is if you needed
to *redefine* the security information in a base class for instances
of your own class. An example below redefines a security assertion in
a subclass::

  from AccessControl import ClassSecurityInfo
  from AccessControl.class_init import InitializeClass
  from OFS.ObjectManager import ObjectManager

  class MailboxBase(ObjectManager):
      """A mailbox base class."""

      # Create a SecurityInfo for this class
      security = ClassSecurityInfo()

      @security.protected('View Mailbox')
      def listMessages(self):
          """Return a sequence of message objects."""
          return self._messages[:]

      security.setPermissionDefault('View Mailbox',
                                    ('Manager', 'Mailbox Owner'))

  InitializeClass(MailboxBase)


  class MyMailbox(MailboxBase):
      """A mailbox subclass

      Here  we want the security for listMessages to be public instead of
      protected (as defined in the base class).
      """

      # Create a SecurityInfo for this class
      security = ClassSecurityInfo()

      security.declarePublic('listMessages')

  InitializeClass(MyMailbox)


Class Security Assertions In Non-Product Code (External Methods/Python Scripts)
-------------------------------------------------------------------------------

.. note::

    The examples in this section use so-called "External Methods",
    which require installing the ``Products.ExternalMethod`` package.
    Use of that package is discouraged in favor of filesystem-based
    Product code.

Objects that are returned from Python Scripts or External Methods
need to have assertions declared for themselves before they can be
used in restricted code.  For example, assume you have an External
Method that returns instances of a custom ``Book`` class. If you want
to call this External Method from a Page Template, and you'd like your
template to be able to use the returned ``Book`` instances, you will need
to ensure that your class supports ``Acquisition``, and you'll need to make
security assertions on the ``Book`` class and initialize it with the
global class initializer (just as you would with a class defined in a
Product). For example::

  # an external method that returns Book instances

  from AccessControl import ClassSecurityInfo
  from AccessControl.class_init import InitializeClass
  from Acquisition import Implicit

  class Book(Implicit):

      def __init__(self, title):
          self._title = title

      # Create a SecurityInfo for this class
      security = ClassSecurityInfo()
      security.declareObjectPublic()

      @security.public
      def getTitle(self):
          return self._title

  InitializeClass(Book)


  # The actual external method
  def getBooks(self):
    books = []
    books.append(Book('King Lear').__of__(self))
    books.append(Book('Romeo and Juliet').__of__(self))
    books.append(Book('The Tempest').__of__(self))
    return books

Note that we *wrap* the book instances by way of their ``__of__``
methods to obtain a security context before returning them.

Note that this particular example is slightly dangerous.  You need to
be careful that classes defined in external methods not be made
persistent, as this can cause Zope object database inconsistencies.
In terms of this example, this would mean that you would need to be
careful to not attach the Book object returned from the ``getBooks``
method to a persistent object within the ZODB. See
:doc:`ZODBPersistentComponents` for more information.  Thus it's
generally a good idea to define the ``Book`` class in a Product if you
want books to be persistent.  It's also less confusing to have all of
your security declarations in Products.

However, one benefit of the ``SecurityInfo`` approach is that it is
relatively easy to subclass and add security assertions to classes
that you did not write. For example, in an External Method, you may
want to return instances of ``Book`` although ``Book`` is defined in
another module out of your direct control. You can still use
``SecurityInfo`` to define security information for the class by using::

  # an external method that returns Book instances

  from AccessControl import ClassSecurityInfo
  from AccessControl.class_init import InitializeClass
  from Acquisition import Implicit
  import bookstuff

  class Book(Implicit, bookstuff.Book):
      security = ClassSecurityInfo()
      security.declareObjectPublic()
      security.declarePublic('getTitle')

  InitializeClass(Book)

  # The actual external method
  def getBooks(self):
    books=[]
    books.append(Book('King Lear'))
    books.append(Book('Romeo and Juliet'))
    books.append(Book('The Tempest'))
    return books


Module Security Assertions
==========================

Another kind of ``SecurityInfo`` object you will use as a
component developer is the ``ModuleSecurityInfo`` object.

``ModuleSecurityInfo`` objects do for objects defined in modules
what ``ClassSecurityInfo`` objects do for methods defined in
classes.  They allow module-level objects (generally functions) to
be protected by security assertions.  This is most useful when
attempting to allow through-the-web code to ``import`` objects
defined in a Python module.

One major difference between ``ModuleSecurityInfo`` objects and
``ClassSecurityInfo`` objects is that ``ModuleSecurityInfo`` objects
cannot be declared `protected` by a permission.  Instead,
``ModuleSecurityInfo`` objects may only declare that an object is
`public` or `private`.  This is due to the fact that modules are
essentially "placeless", global things, while permission
protection depends heavily on "place" within Zope.


Declaring Module Security
-------------------------

In order to use a filesystem Python module from restricted code such
as Python Scripts, the module must have Zope security declarations
associated with functions within it.  There are a number of ways to
make these declarations:

- By embedding the security declarations in the target module.  A
  module that is written specifically for Zope may do so, whereas a
  module not specifically written for Zope may not be able to do so.

- By creating a wrapper module and embedding security declarations
  within it.  In many cases it is difficult, impossible, or simply
  undesirable to edit the target module.  If the number of objects in
  the module that you want to protect or make public is small, you
  may wish to simply create a wrapper module.  The wrapper module
  imports objects from the wrapped module and provides security
  declarations for them.

- By placing security declarations in a filesystem Product.
  Filesystem Python code, such as the ``__init__.py`` of a Product, can
  make security declarations on behalf of an external module.  This
  is also known as an "external" module security info declaration.

The ``ModuleSecurityInfo`` class is defined in the ``AccessControl``
package of the Zope framework.


Using ModuleSecurityInfo Objects
--------------------------------

Instances of ``ModuleSecurityInfo`` are used in two different
situations.  In embedded declarations, inside the module they
affect.  And in external declarations, made on behalf of a
module which may never be imported.


Embedded ModuleSecurityInfo Declarations
----------------------------------------

An embedded ModuleSecurityInfo declaration causes an object in its
module to be importable by through-the-web code.

Here's an example of an embedded declaration::

  from AccessControl import ModuleSecurityInfo
  modulesecurity = ModuleSecurityInfo()
  modulesecurity.declarePublic('foo')

  def foo():
      return 'hello'
      # foo

  modulesecurity.apply(globals())

When making embedded ``ModuleSecurityInfo`` declarations, you should
instantiate a ``ModuleSecurityInfo`` object and assign it to a name.
It's wise to use the recommended name ``modulesecurity`` for
consistency's sake.  You may then use the ``modulesecurity`` object's
``declarePublic`` method to declare functions inside of the current
module as `public`.  Finally, appending the last line
(``modulesecurity.apply(globals())``) is an important step.  It's
necessary in order to poke the security machinery into action.  The
above example declares the ``foo`` function public.

The name ``modulesecurity`` is used for consistency and for the benefit
of new component authors, who often learn from looking at other
people's code.  You do not have to use the name ``modulesecurity`` for
the security infrastructure to recognize your assertion information,
but it is recommended as a convention.


External ModuleSecurityInfo Declarations
----------------------------------------

By creating a ``ModuleSecurityInfo`` instance with a module name
argument, you can make declarations on behalf of a module without
having to edit or import the module.

Here's an example of an external declaration::

   from AccessControl import ModuleSecurityInfo
   # protect the 'foo' function within (yet-to-be-imported) 'foomodule'
   ModuleSecurityInfo('foomodule').declarePublic('foo')

This declaration will cause the following code to work within
Python Scripts::

   from foomodule import foo

When making external ``ModuleSecurityInfo`` declarations, you needn't use
the ``modulesecurity.apply(globals())`` idiom demonstrated in the
embedded declaration section above.  As a result, you needn't assign
the ``ModuleSecurityInfo`` object to the name ``modulesecurity``.


Providing Access To A Module Contained In A Package
---------------------------------------------------

Note that if you want to provide access to a module inside of a
package which lives in your ``PYTHONPATH``, you'll need to provide
security declarations for *all of the the packages and sub-packages
along the path used to access the module.*

For example, assume you have a function ``foo``, which lives inside a
module named ``module``, which lives inside a package named ``package2``,
which lives inside a package named ``package1`` You might declare the
``foo`` function public via this chain of declarations::

  ModuleSecurityInfo('package1').declarePublic('package2')
  ModuleSecurityInfo('package1.package2').declarePublic('module')
  ModuleSecurityInfo('package1.package2.module').declarePublic('foo')

Note that in the code above we took the following steps:

- make a ``ModuleSecurityInfo`` object for ``package1``

- call the ``declarePublic`` method of the ``package1``
  ``ModuleSecurityInfo`` object, specifying ``package2`` as what
  we're declaring public.  This allows through the web code to
  "see" ``package2`` inside ``package1``.

- make a ``ModuleSecurityInfo`` object for ``package1.package2``.

- call the ``declarePublic`` method of the ``package1.package2``'
  ``ModuleSecurityInfo`` object, specifying ``module`` as what we're
  declaring public.  This allows through the web code to "see"
  ``package1.package2.module``.

- declare ``foo`` public inside the ``ModuleSecurityInfo`` for
  ``package1.package2.module``.

Through-the-web code may now perform an import ala: ``import
package1.package2.module.foo``


Declaring Module Security On Modules Implemented In C
-----------------------------------------------------

Certain modules, such as the standard Python ``sha`` module, provide
extension types instead of classes, as the ``sha`` module is
implemented in C. Security declarations typically cannot be added to
extension types, so the only way to use this sort of module is to
write a Python wrapper class, or use `External Methods`.


Default Module Security Info Declarations
-----------------------------------------

Through-the-web Python Scripts are by default able to import a small
number of Python modules for which there are security
declarations. These include ``string``, ``math``, and ``random``.
The only way to make other Python modules available for import is to
add security declarations to them in the filesystem.


Utility Functions For Allowing Import of Modules By Through The Web Code
------------------------------------------------------------------------

Instead of manually providing security declarations for each function
in a module, the utility function ``allow_class`` and ``allow_module``
have been created to help you declare the entire contents of a class
or module as public.

You can handle a module, such as ``base64``, that contains only safe
functions by writing ``allow_module('module_name')``.  For instance::

  from Products.PythonScripts.Utility import allow_module
  allow_module('base64')

This statement declares all functions in the ``base64`` module (
``encode``, ``decode``, ``encodestring``, and ``decodestring``) as public,
and from a script you will now be able to perform an import statement
such as ``from base64 import encodestring``.


To allow access to only some names in a module, you can eschew the
``allow_class`` and ``allow_module`` functions for the lessons you
learned in the previous section and do the protection "manually"::

  from AccessControl import ModuleSecurityInfo
  ModuleSecurityInfo('module_name').declarePublic('name1','name2', ...)


Making Permission Assertions On A Constructor
---------------------------------------------

When you develop a Python filesystem-based product, you will generally be
required to make "constructor" methods for the objects which you wish
to make accessible via the Zope management interface by users of your
Product.  These constructors are usually defined within the modules
which contain classes which are intended to be turned into Zope
instances.  For more information on how constructors are used in Zope
with security, see the chapter :doc:`Products`.

The Zope Product machinery "bootstraps" Product-based classes with
proper constructors into the namespace of the Zope management
interface `Add` list at Zope startup time.  This is done as a
consequence of registering a class by way of the Product's
``__init__.py`` ``initialize`` function.  If you want to make, for
example, the imaginary ``FooClass`` in your Product available from the
`Add` list, you may construct an ``__init__.py`` file that looks much
like this::

      from FooProduct import FooClass

      def initialize(context):
          """ Initialize classes in the FooProduct module """
          context.registerClass(
              FooProduct.FooClass, # the class object
              permission='Add FooClasses',
              constructors=(FooProduct.manage_addFooClassForm,
                            FooProduct.manage_addFooClass),
              icon='foo.gif'
              )

The line of primary concern to us above is the one which says
``permission='Add FooClasses``.  This is a permission declaration
which, thanks to Zope product initialization, restricts the adding of
FooClasses to those users who have the `Add FooClasses` permission by
way of a role association determined by the system administrator.

If you do not include a ``permission`` argument to ``registerClass``,
then Zope will create a default permission named `Add [meta-type]s`.
So, for example, if your object had a meta_type of ``Animal``, then
Zope would create a default permission, `Add Animals`.  For the most
part, it is much better to be explicit then to rely on Zope to take
care of security details for you, so be sure to specify a permission
for your object.


Designing For Security
======================

"Security is hard." -- Jim Fulton.

When you're under a deadline, and you "just want it to work", dealing
with security can be difficult.  As a component developer, following
these basic guidelines will go a long way toward avoiding problems
with security integration. They also make a good debugging checklist!

- Ensure that any class that needs to work with security has
  ``Acquisition.Implicit`` or ``Acquisition.Explicit`` somewhere
  in its base class hierarchy.

- Design the interface to your objects around methods; don't expect
  clients to access instance attributes directly.

- Ensure that all methods meant for use by restricted code have been
  protected with appropriate security assertions.

- Ensure that you called the global class initializer on all classes
  that need to work with security.


Using The RoleManager Base Class With Your Zope Product
=======================================================

After your Product is deployed, system managers and other users of
your Product often must deal with security settings on instances they
make from your classes.

Product classes which inherit Zope's standard ``RoleManager`` base
class allow instances of the class to present a security interface.
This security interface allows managers and developers of a site to
control an instance's security settings via the Zope management
interface.

The user interface is exposed via the *Security* management view.
From this view, a system administrator may secure instances of your
Product's class by associating roles with permissions and by
asserting that your object instance contains `local roles`.  It also
allows them to create `user-defined roles` within the Zope management
framework in order to associate these roles with the permissions of
your product and with users.  This user interface and its usage
patterns are explained in more detail within the `Zope Book's security
chapter <https://zope.readthedocs.io/en/latest/zopebook/Security.html>`_.

If your Product's class does not inherit from ``RoleManager``, its
methods will still retain the security assertions associated with
them, but you will be unable to allow users to associate roles with
the permissions you've defined respective to instances of your class.
Your objects will also not allow local role definitions.  Note that
objects which inherit from many of the built-in classes such as
``OFS.SimpleItem.SimpleItem`` or ``OFS.ObjectManager.ObjectManager``
already inherit from ``RoleManager``.


Conclusion
==========

Zope security is based upon roles and permissions. Users have
roles. Security policies map permissions to roles. Classes protect
methods with permissions. As a developer your main job is to protect
your classes by associating methods with permissions. Of course there
are many other details such as protecting modules and functions,
creating security user interfaces, and initializing security
settings.
