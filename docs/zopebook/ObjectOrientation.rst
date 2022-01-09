Object Orientation
==================

.. include:: includes/zope2_notice.rst

To make the best use of Zope, you will need a grasp on the concept of *object
orientation*, which is a software development pattern used in many programming
languages (C++, Java, Python and others) and computer systems that simulate
"real-world" behavior. It stipulates that you should design an application in
terms of *objects*. This chapter provides a broad overview of the fundamentals
of object orientation from the perspective of a Zope developer.

Objects
-------

In Zope, as in other object-oriented systems, your application is designed
around *objects*, or self-contained "bundles" of data and logic.  It is
easiest to describe these bundles by comparing them to other programming
concepts.

In a typical, non-object-oriented application, you will have two things:

- Code.  For example, a typical CGI-based web application may have a bit of
  logic in the form of a PHP script, which retrieves employee data from a
  database and displays tabular data to a user.

- Data.  For example, you may have employee data stored in a database, such
  as MySQL or Oracle, on which some code performs read or change
  operations.  This data exists almost solely for the purpose of the code
  that operates upon it; without this code, the data holds little to no
  value.

In a typical object-oriented application, however, you will have one thing, and
one thing only:

- Objects.  Simply stated, these objects are collections of code and data
  wrapped up together.  For example, you may have an "Employee" object that
  represents an employee.  It will contain data about the employee, such as
  a phone number, name, and address, much like the information that would
  be stored in a database.  However, the object will also contain "logic,"
  or code, that can manipulate and display its data.

In a non-object-oriented application, your data is kept separate from your
code. But in an object-oriented application, both your data and your code are
stored in one or more objects, each of which represents a particular "thing".
These objects can represent just about anything. In Zope, the *Control_Panel*
is an object, Folders that you create are objects, and even the Zope "root
folder" is an object. When you use the Zope "add list" to create a new item in
the Zope Management Interface, you are creating an object. People who extend
Zope by creating add-ons define their own types of objects, which are then
entered in to the Zope "add list" so that you can create objects based on them.
An add-on author might define a "Form" object or a "Weblog" object. Basically,
anything that can be defined using a noun can be modeled as a Zope object.

As a programming methodology, object orientation allows software developers
to design and create programs in terms of "real-world" things, such as
Folders, Control_Panels, Forms, and Employees, instead of designing
programs based around more "computerish" concepts like bits, streams, and
integers.  Instead of teaching the computer about our problem by descending
to its basic vocabulary (bits and bytes), we use an abstraction to teach
the computer about the problem in terms of a vocabulary that is more
natural to humans.  The core purpose of object orientation is to allow
developers to create, to the largest extent possible, a system based on
abstractions of the natural language of a computer (bits and bytes) into
the real-world objects, like Employees and Forms, that we can understand
more readily and quickly.

The concept of abstraction also encourages programmers to break up a larger
problem by addressing the problem as smaller, more independent
"sub-problems," which allows developers to define and address solutions in
much smaller, more feasible terms.  When you design an application in terms
of objects, they become the pieces that eventually define the solution to
all the "sub-problems" of a particular "big" problem.

Attributes
----------

An object's data is defined by its *attributes*, or pieces of data that
describe aspects of the object.  For example, an attribute of an Employee
object might be called "phone_number," which might contain a series of
characters that represent the employee's phone number.  Other attributes of
an Employee object might be "first_name," "last_name", and "job_title," all
of which give additional, detailed information about each Employee.

It may help to think of the set of attributes belonging to an object as a
sort of "mini-database" that contains information representing the
"real-world thing" that the object is attempting to describe.  The complete
collection of attributes assigned to an object defines that object's
*state*.  When one or more of an object's attributes are modified, the
object is said to have *changed its state*.

Methods
-------

The set of actions that an object may perform is defined by its *methods*.
Methods are code definitions attached to an object that perform actions
based on the object's attributes.  For example, a method of an Employee
object named "getFirstName" may return the value of the object's
"first_name" attribute, while a method of an Employee object named
"setFirstName" might *change* the value of the object's "first_name"
attribute.  The "getTitle" method of an Employee object may return a value
of "Vice President" or "Janitor, depending on which Employee object is
being queried.

Methods are similar to *functions* in procedural languages like 'C'.  The
key difference between a method and a function is that a method is "bound"
to, or attached to, an object: instead of operating solely on "external"
data that is passed to it via arguments, it may also operate on the
attributes of the object to which it is bound.

Messages
--------

In an object-oriented system, to do any useful work, an object is required
to communicate with other objects in the same system. For example, it
wouldn't be particularly useful to have a single Employee object just
sitting around in "object-land" with no way to communicate with it.  It
would then just be as "dumb" as a regular old relational database row, just
storing some data without the ability to do much else.  We want the
capability to ask the object to do something useful, or more precisely: we
want the capability for *other* objects to ask our Employee object to do
something useful.  For instance, if we create an object named
"EmployeeSummary," which is responsible for collecting the names of all of
our employees for later display, we want the EmployeeSummary object to be
able to ask a set of Employee objects for their first and last names.

When one object communicates with another, it is said to send a *message*
to another object.  Messages are sent to objects by way of the object's
*methods*.  For example, our EmployeeSummary object may send a message to
our Employee object by way of "calling" its "getFirstName" method.  Our
Employee object would receive the message and return the value of its
"first_name" attribute.  Messages are sent from one object to another when
a "sender" object calls a method of a "receiver" object.

When you access a URL that "points to" a Zope object, you are almost always
sending that Zope object a message.  When you request a response from Zope
by way of invoking a Zope URL with a web browser, the Zope `object
publisher <https://zope.readthedocs.io/en/latest/zdgbook/ObjectPublishing.html>`_
receives the request from your browser.  It then sends a Zope object a
message on your browser's behalf by "calling a method" on the Zope object
specified in the URL.  The Zope object responds to the object publisher
with a return value, and the object publisher returns the value to your
browser.

Classes and Instances
---------------------

A *class* defines an object's behavior and acts as a *constructor* for an
object.  When we talk about a "kind" of object, like an "Employee" object,
we actually mean "objects constructed using the Employee class" or, more
likely, just "objects of the Employee class."  Most objects are members of
a class.

It is typical to find many objects in a system that are essentially similar
to one another, save for the values of their attributes.  For instance, you
may have many Employee objects in your system, each with "first_name" and
"last_name" attributes. The only difference between these Employee objects
is the values contained within their attributes.  For example, the
"first_name" of one Employee object might be "Fred" while another might be
"Jim".  It is likely that each of these objects would be *members of the
same class*.

A class is to an object as a set of blueprints is to a house: as many
houses can be constructed using the same set of blueprints, many objects
can be constructed using the same class. Objects that share a class
typically behave identically to one other.  If you visit two houses that
share the same set of blueprints, you will likely notice striking
similarities: the layout will be the same, the light switches will be in the
same places, and the fireplace will almost certainly be in the same
location.  The shower curtains might be different in each house, but this
is an *attribute* of each particular house that doesn't change its
essential similarity with the other.  It is much the same with instances of
a class: if you "visit" two instances of a class, you would interact with
both instances in essentially the same way: by calling the same set of
methods on each.  The data kept in the instance (by way of its attributes)
might be different, but these instances *behave* in exactly the same way.

The behavior of two objects constructed from the same class is similar
because they both share the same *methods*, which are not typically defined
by an object itself, but are instead defined by an object's *class*.  For
instance, if the Employee class defines the 'getFirstName' method, all
objects that are members of the Employee class share that method
definition.  The set of methods assigned to an object's class define the
*behavior* of that object.

The objects constructed by a class are called *instances of the class*, or
(more often) just *instances*.  For example, the Zope 'index' page is
an *instance of* the 'Page Template' class. The 'index' page has an 'id'
attribute of 'index', while another page may have an 'id' attribute of
'my_page'.  However, while they have different attribute values, since
they are both instances of the same class, they both behave identically.
All the objects that can be administered using the ZMI are instances of a
class.  Typically, the classes from which these objects are constructed are
defined in the add-ons created by Zope developers and community members.

Inheritance
-----------

It is sometimes desirable for objects to share the same essential behavior,
except for small deviations.  For example, you may want to create a
ContractedEmployee object that has all the behavior of a "normal" Employee
object, except that you must keep track of a tax identification number on
instances of the ContractedEmployee class that is irrelevant for "normal"
instances of the Employee class.

*Inheritance* is the mechanism that allows you to share essential behavior
between two objects, while customizing one with a slightly modified set of
behaviors that differ from or extend the other.

Inheritance is specified at the *class level*.  Since *classes define
behavior*, if we want to change an object's behavior, we almost always need
to change its class.

If we base our new "ContractedEmployee" class on the Employee class, but
add a method to it named "getTaxIdNumber" and an attribute named
"tax_id_number," the ContractedEmployee class would be said to *inherit
from* the Employee class.  In the jargon of object orientation, the
ContractedEmployee class would be said to *subclass from* the Employee
class, and the *Employee* class would be said to be a *superclass of* the
ContractedEmployee class.

When a subclass inherits behavior from another class, it doesn't need to
sit idly by and accept all the method definitions of its superclass if they
don't suit its needs: if necessary, the subclass can *override* the method
definitions of its superclass.  For instance, we may want our
ContractedEmployee class to return a different "title" than instances of
our Employee class.  In our ContractedEmployee class, we might cause the
'getTitle' method of the Employee class to be *overridden* by creating a
method within ContractedEmployee with a different implementation.  For
example, it may always return "Contractor" instead of a job-specific title.

Inheritance is used extensively in Zope objects.  For example, the Zope
"Image" class inherits its behavior from the Zope "File" class, since
images are really just another kind of file, and both classes share many
behavior requirements.  But the "Image" class adds a bit of behavior that
allows it to "render itself inline" by printing its content within HTML
tags, instead of causing a file download.  It does this by *overriding* the
'index_html' method of the File class.

Object Lifetimes
----------------

Object instances have a specific *lifetime*, which is typically controlled
by either a programmer or a user of the system in which the objects "live".

Instances of web-manageable objects in Zope, such as Files, Folders, and
Page Templates, span from the time the user creates them until they are
deleted. You will often hear these kinds of objects described as
*persistent* objects.  These objects are stored in Zope's object database
(the ZODB).

Other Zope object instances have different lifetimes: some object instances
last for a "programmer-controlled" period of time.  For instance, the
object that represents a web request in Zope (often called REQUEST) has a
well-defined lifetime, which lasts from the moment the object publisher
receives the request from a remote browser, until a response is sent back
to that browser, after which it is destroyed automatically.  Zope "session
data" objects have another well-defined lifetime, which spans from the time
a programmer creates one on behalf of the user via code, until such time
that the system (on behalf of the programmer or site administrator) deems
it necessary to throw away the object in order to conserve space, or to
indicate an "end" to the user's session.  This is defined by default as 20
minutes of "inactivity" by the user for whom the object was created.

Summary
-------

Zope is an object-oriented development environment.  Understanding Zope
fully requires a grasp of the basic concepts of object orientation,
including attributes, methods, classes, and inheritance, before setting out
on a "for-production" Zope development project.

For a more comprehensive treatment on the subject of object orientation,
buy and read `The Object
Primer <https://www.amazon.com/Object-Primer-Agile-Model-Driven-Development/dp/0521540186/>`_ by Scott Ambler.
