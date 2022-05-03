Acquisition
###########

.. include:: includes/zope2_notice.rst

Acquisition is the technology that allows dynamic behavior to be
shared between Zope objects via *containment*.

Acquisition's flavor permeates Zope and can be used almost everywhere within
Zope: in Zope Page Templates, in Script (Python) objects, and even in Zope
URLs. Because of its ubiquity in Zope, a basic understanding of acquisition is
important.

Over the years Acquisition has been proven to be a very powerful but often
too complex technology to use. While it is predictable in simple interactions,
it gets increasingly complicated to understand its behavior in most
real-world-sized projects.

In order to understand Zope, you will still need an understanding of
Acquisition today. Basing your application logic on it is highly
discouraged, though.


Acquisition vs. Inheritance
===========================

The chapter entitled `Object Orientation <ObjectOrientation.html>`_
describes a concept called *inheritance*.  Using inheritance, an
object can *inherit* some of the behaviors of a specific class,
*overriding* or adding other behaviors as necessary.  Behaviors of
a class are nearly always defined by its *methods*, although
attributes can be inherited as well.

In a typical object-oriented language, there are rules that define the way
a *subclass* inherits behavior from its *superclasses*.  For
example, in Python (a *multiple-inheritance* language), a class
may have more than one superclass, and rules are used to determine
which of a class' superclasses is used to define behavior in any
given circumstance.

We'll define a few Python classes here to demonstrate.  You don't
really need to know Python inside and out to understand these
examples.  Just know that a 'class' statement defines a class, and
a 'def' statement inside of a class statement defines a method.
A class statement followed by one or more words inside (parentheses)
causes that class to *inherit* behavior from the classes named in
the parentheses (you can play along at home if you like, using the
Python interpreter).::

  >>> class SuperA:
  ...     def amethod(self):
  ...         print "I am the 'amethod' method of the SuperA class"
  ...     def anothermethod(self):
  ...         print "I am the 'anothermethod' method of the SuperA class"
  ...
  >>> class SuperB:
  ...     def amethod(self):
  ...         print "I am the 'amethod' method of the SuperB class"
  ...     def anothermethod(self):
  ...         print "I am the 'anothermethod' method of the SuperB class"
  ...     def athirdmethod(self):
  ...         print "I am the 'athirdmethod' method of the SuperB class"
  ...
  >>> class Sub(SuperA, SuperB):
  ...     def amethod(self):
  ...         print "I am the 'amethod' method of the Sub class"
  ...

If we make an *instance* of the "Sub" class, and attempt to *call*
one of its methods, there are rules in place to determine whether
the behavior of the method will be defined by the Sub class
itself, its SuperA superclass, or its SuperB superclass.  The
rules are fairly simple: if the Sub class has itself defined the
named method, that method definition will be used.  Otherwise, the
*inheritance hierarchy* will be searched for a method definition.

The *inheritance hierarchy* is defined by the class' superclass
definitions.  The case of the Sub class above has a simple
inheritance hierarchy: it inherits first from the SuperA
superclass, then it inherits from the SuperB superclass.  This
means that if you call a method on an instance of the Sub class,
and that method is not defined as part of the Sub class'
definition, it will first search for the method in the SuperA
class.  If it doesn't find it there, it will search in the
SuperB class.  Python performs this search of the base classes
using an order derived from the order of declaration.  Note that for
complex cases (e.g., where the same method is defined in several
ancestors of base classes), the lookup order is too complicated to
explain within the scope of this book.  Please see the online
Python documentation for the "method resolution order",
https://www.python.org/download/releases/2.3/mro/

Here is an example of calling methods on an instance of the
above-defined Sub class::

  >>> instance = Sub()
  >>> instance.amethod()
  I am the 'amethod' method of the Sub class
  >>> instance.anothermethod()
  I am the 'anothermethod' method of the SuperA class
  >>> instance.athirdmethod()
  I am the 'athirdmethod' method of the SuperB class

Note that when we called the 'anothermethod' method on the Sub
instance, we got the return value of SuperA's method definition
for that method, even though both SuperA and SuperB defined that
method.  This is because the inheritance hierarchy specifies that
the first superclass (SuperA) is searched first.

The point of this example is that instances of objects use their
*inheritance hierarchy* to determine their behavior.  In non-Zope
applications, this is the only way that object instances know
about their set of behaviors.  However, in Zope, objects make use
of another facility to search for their behaviors: *acquisition*.

Acquisition Is about Containment
================================

The concept behind acquisition is simple:

- Objects are situated inside other objects, and these objects act as
  their "containers".  For example, the container of a Page Template
  named "apage" inside a Folder "afolder" is the
  "afolder" folder.

- Objects may acquire behavior from their containers.

Inheritance stipulates that an object can learn about its behavior
from its superclasses via an *inheritance hierarchy*.
*Acquisition*, on the other hand, stipulates that an object can
additionally learn about its behavior through its *containment
hierarchy*.  In Zope, an object's inheritance hierarchy is always
searched for behavior before its acquisition hierarchy.  If the
method or attribute is not found in the object's inheritance
hierarchy, then the acquisition hierarchy is searched.

Say What?
=========

Let's toss aside the formal explanations.  Acquisition can be
best explained with a simple example.

Place a Page Template named 'acquisition_test' in your Zope root
folder.  Give it the following body::

  <html>
  <body>
    <p>
     I am being called from within the
     <span tal:replace="context/title" />
     Folder!
    </p>
  </body>
  </html>

Save it, and then use the Page Template "View" tab to see the result
of the template in your Workspace frame.  You will see
something not unlike the following::

  I am being called from within the Zope Folder!

The 'title' of the Zope root folder is 'Zope', so this makes
sense.  Now create a Folder inside your Zope root folder
named 'AcquisitionTestFolder' and a title of
"TheAcquisitionTest".  We're going to invoke the
'acquisition_test' page *in the context of* the
AcquisitionTestFolder folder.  To do this, assuming your
Zope is running on your local machine on port 8080, visit
the URL
'http://localhost:8080/AcquisitionTestFolder/acquisition_test'.
You will see something not unlike the following::

  I am being called from within the TheAcquisitionTest Folder!

Note that even though an object named 'acquisition_test' does not
"live" inside the AcquisitionTestFolder folder, Zope found the
page and displayed a result anyway!  Not only did Zope display a
result, instead of inserting the 'title' of the Zope root folder, it
inserted the 'title' of the AcquisitionTestFolder folder!

This is an example of acquisition in action.  The concept is simple:
if a named object is not found as an attribute of the object you're
searching, its containers are searched until the object is found.
In this way, acquisition can *add behavior* to objects.  In this
case, we added a behavior to the AcqusitionTestFolder folder that
it didn't have before (by way of adding an 'acquisition_test' page).

Providing Services
==================

It can be said that acquisition allows objects to acquire
*services* by way of containment.  For example, our
AcquisitionTestFolder folder acquired the services of the
'acquisition_test' page.

Not only do objects *acquire* services, but they also *provide* them. For
example, adding a Mail Host object to a Folder named 'AFolder'
provides other objects in that folder with the ability to send
mail.  But it also provides objects contained in *subfolders* of
that folder with the capability to send mail.  If you create
subfolders of 'AFolder' named 'AnotherFolder' and 'AThirdFolder',
you can be assured that objects placed in *these* folders will
also be able to send mail in exactly the same way as objects
placed in 'AFolder'.

Acquisition "goes both ways": when you create an object in Zope,
it has the capability to automatically acquire services.
Additionally, it automatically provides services that other
objects can acquire. This makes reuse of services very easy, since
you don't have to do anything special in order to make services available
to other objects.

Getting Deeper with Multiple Levels
===================================

If you place a method in the root folder, and create a subfolder
in the root folder, you can acquire the method's behaviors. So
what happens if things get more complex?  Perhaps you have a
method that needs to be acquired from within a couple of
folders. Is it acquired from its parent, or its parent's parent,
or what?

The answer is that acquisition works on the entire object
hierarchy. If, for example, you have a Page Template, "HappySong",
in the root folder, and also in the root folder you have three
nested Folders named "Users", "Barney" and "Songs",
you may call this URL::

  /Users/Barney/Songs/HappySong

The HappySong page is found in the root folder, unless one of the
other folders "Users", "Barney" or "Songs" happens to also have a
page named "HappySong", in which case *that* page is used instead.
The HappySong page is searched for first directly in the "Songs"
folder.  If it is not found, the acquisition hierarchy is searched
starting at the first container in the hierarchy: "Barney".  If it
is not found in "Barney", the "Users" folder is searched.  If it
is not found in the "Users" folder, the root folder is searched.
This search is called *searching the acquisition path* or
alternately *searching the containment hierarchy*.

Acquisition is not limited to searching a containment hierarchy: it
can also search a *context hierarchy*.  Acquisition by context is
terribly difficult to explain, and you should avoid it if at all
possible.

In the example above, for instance, in order to find and publish
the "HappySong" template at the end of the URL, acquisition searches
the *containment hierarchy* of the "Songs" folder first.  Because
"Songs" is contained within "Barney", and "Barney" within "Users",
the *containment hierarchy* for "Songs" consists of each folder "up"
from "Users" to the root.

Once the "HappySongs" template is found, there are two hierarchies of
interest:

- Because "HappySongs" is located directly within the root, its
  *containment hierarchy* consists of only itself and the root.

- Because "HappySongs" was found by traversing first through the
  "Users", "Barney", and "Songs" folders, its *context hierarchy*
  includes those objects.

Acquisition searches the *context hierarchy* only after failing
to find the named object in the *containment hierarchy*.

As with understanding Python's concept of multiple inheritance, explaining
the exact strategy used to order that search is not within the scope of this
book.

Summary
=======

Acquisition allows behavior to be distributed hierarchically throughout the
system. When you add a new object to Zope, you don't need to
specify all of its behavior, only the part of its behavior that is
unique to that object. For the rest of its behavior, it relies on other
objects. This means that you can change an object's behavior by
changing where it is located in the object hierarchy. This is a
very powerful function that gives your Zope applications
flexibility.

Acquisition is useful for providing objects with behavior that
doesn't need to be specified by their own methods or methods found
in their inheritance hierarchies.  Acquisition is particularly
useful for sharing information (such as headers and footers)
between objects in different folders as well.  You will see how
you can make use of acquisition within different Zope technologies
in upcoming chapters.
