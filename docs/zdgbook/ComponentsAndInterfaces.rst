#########################
Components and Interfaces
#########################

Zope uses a component architecture internally in many places.  Zope
components is nothing but Python objects with interfaces that
describe them.  As a Zope developer you can use interfaces right now
to build your Zope components.

Zope Components
===============

Components are objects that are associated with interfaces.  An
interface is a Python object that describes how you work with other
Python objects.  In this chapter, you'll see some simple examples of
creating components, and a description of interfaces and how they
work.

Here is a very simple component that says hello.  Like all
components, this one generally consists of two pieces, an interface,
and an implementation::

  from zope.interface import Interface
  from zope.interface import implements

  class IHello(Interface):
      """The Hello interface provides greetings."""

      def hello(name):
          """Say hello to the name"""

  class HelloComponent(object):

      implements(IHello)

      def hello(self, name):
          return "hello %s!" % name

Let's take a look at this step by step.  Here, you see two Python
class statements.  The first class statement creates the *interface*,
and the second class statement creates the *implementation*.

The first class statement creates the ``IHello`` interface.  This
interface describes one method, called ``hello``.  Notice that there
is no implementation for this method, interfaces do not define
behavior, they just describe a specification.

The second ``class`` statement creates the ``HelloComponent`` class.
This class is the actual component that *does* what ``IHello``
*describes*.  This is usually referred to as the *implementation* of
``IHello``.  In order for you to know what interfaces
``HelloComponent`` implements, it must somehow associate itself with
an interface.  The ``implements`` function call inside the class does
just that.  It says, "I implement these interfaces".  In this case,
``HelloComponent`` asserts that it implements one interface,
``IHello``.

The interface describes how you would work with the object, but it
doesn't dictate how that description is implemented.  For example,
here's a more complex implementation of the ``Hello`` interface::

  import xmlrpclib
  class XMLRPCHello:

      implementats(IHello)

      def hello(self, name):
          """Delegates the hello call to a remote object
          using XML-RPC.

          """
          s = xmlrpclib.Server('http://www.zope.org/')
          return s.hello(name)

This component contacts a remote server and gets its hello greeting
from a remote component.

And that's all there is to components, really.  The rest of this
chapter describes interfaces and how you can work with them from the
perspective of components.  In Chapter 3, we'll put all this together
into a Zope product.

Python Interfaces
=================

Interface describe the behavior of an object by containing useful
information about the object.  This information includes:

- Prose documentation about the object.  In Python terms, this is
  called the "doc string" of the interface.  In this element, you
  describe how the object works in prose language and any other
  useful information about the object.

- Descriptions of attributes.  Attribute descriptions include the
  name of the attribute and prose documentation describing the
  attributes usage.

- Descriptions of methods.  Method descriptions can include:

  - Prose "doc string" documentation about the method and its usage.

  - A sequence of parameter objects that describes the parameters
    expected by the method.

- Optional tagged data.  Interface objects (and their attributes,
  methods, and method parameters) can have optional, application
  specific tagged data associated with them.  Examples uses for this
  are security assertions, pre/post conditions, unit tests, and other
  possible information you may want to associate with an Interface or
  its attributes.

Not all of this information is mandatory.  For example, you may only
want the methods of your interface to have prose documentation and
not describe the arguments of the method in exact detail.  Interface
objects are flexible and let you give or take any of these
components.

Why Use Interfaces?
===================

Interfaces solve a number of problems that arise while developing
large systems with lots of developers.

- Developers waste a lot of time looking at the source code of your
  system to figure out how objects work.  This is even worse if
  someone else has already wasted their time doing the same thing.

- Developers who are new to your system may misunderstand how your
  object works, causing, and possibly propagating, usage errors.

- Because an object's interface is inferred from the source,
  developers may end up using methods and attributes that are meant
  for "internal use only".

- Code inspection can be hard, and very discouraging to novice
  programmers trying to understand code written by gurus.

Interfaces try to solve these problems by providing a way for you to
describe how to use an object, and a mechanism for discovering that
description.

Creating Interfaces                                       
===================

The first step to creating a component, as you've been shown, is to
create an interface.

Interface objects can be conveniently constructed using the Python
``class`` statement.  Keep in mind that this syntax can be a little
misleading, because interfaces are *not* classes.  It is important to
understand that using Python's class syntax is just a convenience,
and that the resulting object is an *interface*, not a class.

To create an interface object using Python's class syntax, create a
Python class that subclasses from ``zope.interface.Interface``::

  from zope.interface import Interface

  class IHello(Interface):

      def hello(name):
          """Say hello to the world"""

This interface does not implement behavior for its methods, it just
describes an interface that a typical "Hello" object would realize.
By subclassing the ``zope.interface.Interface`` interface, the
resulting object ``Hello`` is an interface object. The Python
interpreter confirms this::

  >>> IHello
  <InterfaceClass __main__.IHello>

Now, you can associate the ``Hello`` Interface with your new concrete
class in which you define your user behavior.  For example::

  class HelloComponent:

      implements(IHello)

      def hello(self, name):
          return "Hello %s!" % name

This new class, ``HelloComponent`` is a concrete class that
implements the ``Hello`` interface.  A class can realize more than
one interface.  For example, say you had an interface called 'Item'
that described how an object worked as an item in a "Container"
object.  If you wanted to assert that ``HelloComponent`` instances
realized the ``Item`` interface as well as ``Hello``, you can provide
a sequence of Interface objects to the 'HelloComponent' class::

  class HelloComponent:

      implements(IHello, IItem)


The Interface Model
===================

Interfaces can extend other interfaces.  For example, let's extend
the ``IHello`` interface by adding an additional method::

  class ISmartHello(IHello):
      """A Hello object that remembers who it's greeted"""

      def lastGreeted(self):
          """Returns the name of the last person greeted."""


``ISmartHello`` extends the ``IHello`` interface.  It does this by
using the same syntax a class would use to subclass another class.

Now, you can ask the ``ISmartHello`` for a list of the interfaces it
extends with ``getBases``::

  >>> ISmartHello.getBases()
  (<InterfaceClass __main__.IHello>,)

An interface can extend any number of other interfaces, and
``getBases`` will return that list of interfaces for you.  If you
want to know if ``ISmartHello`` extends any other interface, you
could call ``getBases`` and search through the list, but a
convenience method called ``extends`` is provided that returns true
or false for this purpose::

  >>> ISmartHello.extends(IHello)
  True
  >>> ISandwich(Interface):
  ...     pass
  >>> ISmartHello.extends(ISandwich)
  False

Here you can see ``extends`` can be used to determine if one
interface extends another.

You may notice a similarity between interfaces extending from other
interfaces and classes sub-classing from other classes.  This *is* a
similar concept, but the two should not be considered equal.  There
is no assumption that classes and interfaces exist in a one to one
relationship; one class may implement several interfaces, and a class
may not implement its base classes's interfaces.

The distinction between a class and an interface should always be
kept clear.  The purpose of a class is to share the implementation of
how an object works.  The purpose of an interface is to document how
to work *with* an object, not how the object is implemented.  It is
possible to have several different classes with very different
implementations realize the same interface.  Because of this,
interfaces and classes should never be confused.


Querying an Interface
=====================

Interfaces can be queried for information.  The simplest case is to
ask an interface the names of all the various interface items it
describes.  From the Python interpreter, for example, you can walk
right up to an interface and ask it for its *names*::

  >>> IUser.names()
  ['getUserName', 'getFavoriteColor', 'getPassword']

Interfaces can also give you more interesting information about their
items.  Interface objects can return a list of '(name, description)'
tuples about their items by calling the *namesAndDescriptions*
method.

For example::

  >>> IUser.namesAndDescriptions()
  [('getUserName', <zope.interface.interface.Method.Method object at 80f38f0>),
  ('getFavoriteColor', <zope.interface.interface.Method.Method object at 80b24f0>),
  ('getPassword', <zope.interface.interface.Method.Method object at 80fded8>)]

As you can see, the "description" of the Interface's three items in
these cases are all `Method` objects.  Description objects can be
either 'Attribute' or `Method` objects.  Attributes, methods, and
interface objects implement the following interface::

- `getName()` -- Returns the name of the object.

- `getDoc()` -- Returns the documentation for the object.

Method objects provide a way to describe rich meta-data about Python
methods. Method objects have the following methods:

- `getSignatureInfo()` -- Returns a dictionary describing the method
  parameters.

- `getSignatureString()` -- Returns a human-readable string
  representation of the method's signature.

For example::

  >>> m = IUser.namesAndDescriptions()[0][1]
  >>> m
  <zope.interface.interface.Method.Method object at 80f38f0>
  >>> m.getSignatureString()
  '(fullName=1)'
  >>> m.getSignatureInfo()   
  {'varargs': None, 'kwargs': None, 'optional': {'fullName': 1}, 
  'required': (), 'positional': ('fullName',)}  

You can use `getSignatureInfo` to find out the names and types of the
method parameters.


Checking Implementation
=======================

You can ask an interface if a certain class or instance that you hand
it implements that interface.  For example, say you want to know if
instances of the `HelloComponent` class implement 'Hello'::

  IHello.implementedBy(HelloComponent)

This is a true expression.  If you had an instance of
`HelloComponent`, you can also ask the interface if that instance
implements the interface::

  IHello.implementedBy(my_hello_instance)

This would also return true if *my_hello_instance* was an instance of
*HelloComponent*, or any other class that implemented the *Hello*
Interface.

Conclusion
==========

Interfaces provide a simple way to describe your Python objects.  By
using interfaces you document capabilities of objects.  As Zope
becomes more component oriented, your objects will fit right in.
While components and interfaces are forward looking technologies,
they are useful today for documentation and verification.
