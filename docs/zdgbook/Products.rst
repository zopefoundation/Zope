#############
Zope Products
#############

.. attention::

  This document is currently being reviewed and edited for the
  upcoming release of Zope 4.


Introduction
============

In this chapter we are looking at building Python packages that are
**Zope Products**. Products most often provide new addable objects.

.. note:: 
  In the early days of Zope development, it was quite common to
  develop "through the web". This is still possible but no longer
  recommended.
  For further information please refer to the
  `Zope Book <https://zope.readthedocs.io/en/latest/zopebook/index.html>`_.


Development Process
===================

This chapter begins with a discussion of how you will develop
products.  We'll focus on common engineering tasks that you'll
encounter as you develop products.

Consider Alternatives
---------------------

Before you jump into the development of a product you should consider
the alternatives.  Would your problem be better solved with External
Methods, or Python Scripts? Products excel at extending Zope with new
addable classes of objects.  If this does not figure centrally in
your solution, you should look elsewhere.  Products, like External
Methods allow you to write unrestricted Python code on the
filesystem.

Starting with Interfaces
------------------------

The first step in creating a product is to create one or more
interfaces which describe the product.  See Chapter 2 for more
information on interfaces and how to create them.

Creating interfaces before you build an implementation is a good idea
since it helps you see your design and assess how well it fulfills
your requirements.

Consider this interface for a multiple choice poll component (see
`Poll.py <examples/Poll.py>`_)::

  from zope.interface import Interface

  class IPoll(Interface):
      """A multiple choice poll"""

      def castVote(index):
          """Votes for a choice"""

      def getTotalVotes():
          """Returns total number of votes cast"""

      def getVotesFor(index):
          """Returns number of votes cast for a given response"""

      def getResponses():
          """Returns the sequence of responses"""

      def getQuestion():
          """Returns the question"""

How you name your interfaces is entirely up to you.  Here we've
decided to use prefix "I" in the name of the interface.

Implementing Interfaces
-----------------------

After you have defined an interface for your product, the next step
is to create a prototype in Python that implements your interface.

Here is a prototype of a ``PollImplemtation`` class that implements the
interface you just examined (see `PollImplementation.py
<examples/PollImplementation.py>`_)::

  from poll import Poll

  class PollImplementation:
      """A multiple choice poll, implements the Poll interface.

      The poll has a question and a sequence of responses. Votes
      are stored in a dictionary which maps response indexes to a
      number of votes.
      """

      implements(IPoll)

      def __init__(self, question, responses):
          self._question = question
          self._responses = responses
          self._votes = {}
          for i in range(len(responses)):
              self._votes[i] = 0

      def castVote(self, index):
          """Votes for a choice"""
          self._votes[index] = self._votes[index] + 1

      def getTotalVotes(self):
          """Returns total number of votes cast"""
          total = 0
          for v in self._votes.values():
              total = total + v
          return total

      def getVotesFor(self, index):
          """Returns number of votes cast for a given response"""
          return self._votes[index]

      def getResponses(self):
          """Returns the sequence of responses"""
          return tuple(self._responses)

      def getQuestion(self):
          """Returns the question"""
          return self._question

You can use this class interactively and test it.  Here's an example
of interactive testing::

  >>> from PollImplementation import PollImplementation
  >>> p = PollImplementation("What's your favorite color?",
  ...                        ["Red", "Green", "Blue", "I forget"])
  >>> p.getQuestion()
  "What's your favorite color?"
  >>> p.getResponses()
  ('Red', 'Green', 'Blue', 'I forget')
  >>> p.getVotesFor(0)
  0
  >>> p.castVote(0)
  >>> p.getVotesFor(0)
  1
  >>> p.castVote(2)
  >>> p.getTotalVotes()
  2
  >>> p.castVote(4)
  Traceback (innermost last):
  File "<stdin>", line 1, in ?
  File "PollImplementation.py", line 23, in castVote
  self._votes[index] = self._votes[index] + 1
  KeyError: 4

Interactive testing is one of Python's great features.  It lets you
experiment with your code in a simple but powerful way.

At this point you can do a fair amount of work, testing and refining
your interfaces and classes which implement them.  See Chapter 9 for
more information on testing.

So far you have learned how to create Python classes that are
documented with interfaces, and verified with testing.  Next you'll
examine the Zope product architecture.  Then you'll learn how to fit
your well crafted Python classes into the product framework.

Building Product Classes
------------------------

To turn a component into a product you must fulfill many contracts.
For the most part these contracts are not yet defined in terms of
interfaces.  Instead you must subclass from base classes that
implement the contracts.  This makes building products confusing, and
this is an area that we are actively working on improving.

Base Classes
------------

Consider an example product class definition::

  from Acquisition import Implicit
  from Globals import Persistent
  from AccessControl.Role import RoleManager
  from OFS.SimpleItem import Item

  class PollProduct(Implicit, Persistent, RoleManager, Item):
      """
      Poll product class
      """
      ...

The order of the base classes depends on which classes you want to
take precedence over others.  Most Zope classes do not define similar
names, so you usually don't need to worry about what order these
classes are used in your product.  Let's take a look at each of these
base classes.


Acquisition.Implicit
~~~~~~~~~~~~~~~~~~~~

This is the normal acquisition base class.  See the *API Reference*
for the full details on this class.  Many Zope services such as
object publishing and security use acquisition, so inheriting from
this class is required for products.  Actually, you can choose to
inherit from ``Acquisition.Explicit`` if you prefer, however, it will
prevent folks from dynamically binding Python Scripts and DTML
Methods to instances of your class.  In general you should subclass
from ``Acquisition.Implicit`` unless you have a good reason not to.

  XXX: is this true?  I thought that any ExtensionClass.Base can be
  acquired.  The Implicit and Explicit just control how the class can
  acquire, not how it *is* acquired.

Globals.Persistent
~~~~~~~~~~~~~~~~~~

This base class makes instances of your product persistent.  For more
information on persistence and this class see Chapter 4.

In order to make your poll class persistent you'll need to make one
change.  Since ``_votes`` is a dictionary this means that it's a
mutable non-persistent sub-object.  You'll need to let the
persistence machinery know when you change it::

  def castVote(self, index):
      """Votes for a choice"""
      self._votes[index] = self._votes[index] + 1
      self._p_changed = 1

The last line of this method sets the ``_p_changed`` attribute to 1.
This tells the persistence machinery that this object has changed and
should be marked as ``dirty``, meaning that its new state should be
written to the database at the conclusion of the current transaction.
A more detailed explanation is given in the Persistence chapter of
this guide.


OFS.SimpleItem.Item
~~~~~~~~~~~~~~~~~~~

This base class provides your product with the basics needed to work
with the Zope management interface.  By inheriting from ``Item`` your
product class gains a whole host of features: the ability to be cut
and pasted, capability with management views, WebDAV support,
undo support, ownership support, and traversal controls.
It also gives you some standard methods for management views and
error display including ``manage_main()``.  You also get the
``getId()``, ``title_or_id()``, ``title_and_id()`` methods and the
``this()`` DTML utility method.  Finally this class gives your
product basic *dtml-tree* tag support.  ``Item`` is really an
everything-but-the-kitchen-sink kind of base class.

``Item`` requires that your class and instances have some management
interface related attributes.

- ``meta_type`` -- This attribute should be a short string which is
  the name of your product class as it appears in the product add
  list.  For example, the poll product class could have a
  ``meta_type`` with value as ``Poll``.

- ``id`` or ``__name__`` -- All ``Item`` instances must have an
  ``id`` string attribute which uniquely identifies the instance
  within it's container.  As an alternative you may use ``__name__``
  instead of ``id``.

- ``title`` -- All ``Item`` instances must have a ``title`` string
  attribute.  A title may be an empty string if your instance does
  not have a title.

In order to make your poll class work correctly as an ``Item`` you'll
need to make a few changes.  You must add a ``meta_type`` class
attribute, and you may wish to add an ``id`` parameter to the
constructor::

  class PollProduct(..., Item):

      meta_type = 'Poll'
      ...

      def __init__(self, id, question, responses):
          self.id = id
          self._question = question
          self._responses = responses
          self._votes = {}
          for i in range(len(responses)):
              self._votes[i] = 0


Finally, you should probably place ``Item`` last in your list of base
classes.  The reason for this is that ``Item`` provides defaults that
other classes such as ``ObjectManager`` and ``PropertyManager``
override.  By placing other base classes before ``Item`` you allow
them to override methods in ``Item``.

AccessControl.Role.RoleManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This class provides your product with the ability to have its
security policies controlled through the web.  See Chapter 6 for more
information on security policies and this class.

OFS.ObjectManager
~~~~~~~~~~~~~~~~~

This base class gives your product the ability to contain other
``Item`` instances.  In other words, it makes your product class like
a Zope folder.  This base class is optional. See the *API Reference*
for more details.  This base class gives you facilities for adding
Zope objects, importing and exporting Zope objects and WebDAV.
It also gives you the ``objectIds``, ``objectValues``, and
``objectItems`` methods.

``ObjectManager`` makes few requirements on classes that subclass it.
You can choose to override some of its methods but there is little
that you must do.

If you wish to control which types of objects can be contained by
instances of your product you can set the ``meta_types`` class
attribute.  This attribute should be a tuple of meta_types.  This
keeps other types of objects from being created in or pasted into
instances of your product.  The ``meta_types`` attribute is mostly
useful when you are creating specialized container products.

OFS.PropertyManager
~~~~~~~~~~~~~~~~~~~

This base class provides your product with the ability to have
user-managed instance attributes.  See the *API Reference* for more
details.  This base class is optional.

Your class may specify that it has one or more predefined properties,
by specifying a '_properties' class attribute.  For example::

  _properties=({'id':'title', 'type': 'string', 'mode': 'w'},
               {'id':'color', 'type': 'string', 'mode': 'w'},
              )

The ``_properties`` structure is a sequence of dictionaries, where
each dictionary represents a predefined property.  Note that if a
predefined property is defined in the ``_properties`` structure, you
must provide an attribute with that name in your class or instance
that contains the default value of the predefined property.

Each entry in the ``_properties`` structure must have at least an
``id`` and a ``type`` key.  The ``id`` key contains the name of the
property, and the ``type`` key contains a string representing the
object's type.  The ``type`` string must be one of the values:
``float``, ``int``, ``long``, ``string``, ``lines``, ``text``,
``date``, ``tokens``, ``selection``, or ``multiple section``.  For
more information on Zope properties see the *Zope Book*.

For ``selection`` and ``multiple selection`` properties, you must
include an addition item in the property dictionary,
``select_variable`` which provides the name of a property or method
which returns a list of strings from which the selection(s) can be
chosen.  For example::

  _properties=({'id' : 'favorite_color',
                'type' : 'selection',
                'select_variable' : 'getColors'
               },
              )

Each entry in the ``_properties`` structure may optionally provide a
``mode`` key, which specifies the mutability of the property. The
``mode`` string, if present, must be ``w``, ``d``, or ``wd``.

A ``w`` present in the mode string indicates that the value of the
property may be changed by the user.  A ``d`` indicates that the user
can delete the property.  An empty mode string indicates that the
property and its value may be shown in property listings, but that it
is read-only and may not be deleted.

Entries in the ``_properties`` structure which do not have a ``mode``
item are assumed to have the mode ``wd`` (writable and deleteable).

Security Declarations
---------------------

In addition to inheriting from a number of standard base classes, you
must declare security information in order to turn your component
into a product.  See Chapter 6 for more information on security and
instructions for declaring security on your components.

Here's an example of how to declare security on the poll class::

  from AccessControl import ClassSecurityInfo

  class PollProduct(...):
      ...

      security = ClassSecurityInfo()

      security.declareProtected('Use Poll', 'castVote')
      def castVote(self, index):
          ...

      security.declareProtected('View Poll results', 'getTotalVotes')
      def getTotalVotes(self):
          ...

      security.declareProtected('View Poll results', 'getVotesFor')
      def getVotesFor(self, index):
          ...

      security.declarePublic('getResponses')
      def getResponses(self):
          ...

      security.declarePublic('getQuestion')
      def getQuestion(self):
          ...

For security declarations to be set up Zope requires that you
initialize your product class.  Here's how to initialize your poll
class::

  from Globals import InitializeClass

  class PollProduct(...):
     ...

  InitializeClass(PollProduct)

Summary
-------

Congratulations, you've created a product class.  Here it is in all
its glory (see `examples/PollProduct.py <PollProduct.py>`_)::

  from Poll import Poll
  from AccessControl import ClassSecurityInfo
  from Globals import InitializeClass
  from Acquisition import Implicit
  from Globals import Persistent
  from AccessControl.Role import RoleManager
  from OFS.SimpleItem import Item

  class PollProduct(Implicit, Persistent, RoleManager, Item):
      """Poll product class, implements Poll interface.

      The poll has a question and a sequence of responses. Votes
      are stored in a dictionary which maps response indexes to a
      number of votes.
      """

      implements(IPoll)

      meta_type = 'Poll'

      security = ClassSecurityInfo()

      def __init__(self, id, question, responses):
          self.id = id
          self._question = question
          self._responses = responses
          self._votes = {}
          for i in range(len(responses)):
              self._votes[i] = 0

      security.declareProtected('Use Poll', 'castVote')
      def castVote(self, index):
          "Votes for a choice"
          self._votes[index] = self._votes[index] + 1
          self._p_changed = 1

      security.declareProtected('View Poll results', 'getTotalVotes')
      def getTotalVotes(self):
          "Returns total number of votes cast"
          total = 0
          for v in self._votes.values():
              total = total + v
          return total

      security.declareProtected('View Poll results', 'getVotesFor')
      def getVotesFor(self, index):
          "Returns number of votes cast for a given response"
          return self._votes[index]

      security.declarePublic('getResponses')
      def getResponses(self):
          "Returns the sequence of responses"
          return tuple(self._responses)

      security.declarePublic('getQuestion')
      def getQuestion(self):
          "Returns the question"
          return self._question

  InitializeClass(Poll)

Now it's time to test your product class in Zope.  To do this you
must register your product class with Zope.

Registering Products
====================

Products are Python packages that live in 'lib/python/Products'.
Products are loaded into Zope when Zope starts up.  This process is
called *product initialization*.  During product initialization, each
product is given a chance to register its capabilities with Zope.

Product Initialization
----------------------

When Zope starts up it imports each product and calls the product's
'initialize' function passing it a registrar object.  The
'initialize' function uses the registrar to tell Zope about its
capabilities.  Here is an example '__init__.py' file::

  from PollProduct import PollProduct, addForm, addFunction

  def initialize(registrar):
      registrar.registerClass(
          PollProduct,
          constructors=(addForm, addFunction),
          )

This function makes one call to the *registrar* object which
registers a class as an addable object.  The *registrar* figures out
the name to put in the product add list by looking at the 'meta_type'
of the class.  Zope also deduces a permission based on the class's
meta-type, in this case *Add Polls* (Zope automatically pluralizes
"Poll" by adding an "s").  The 'constructors' argument is a tuple of
objects consisting of two functions: an add form which is called when
a user selects the object from the product add list, and the add
method which is the method called by the add form.  Note that these
functions are protected by the constructor permission.

Note that you cannot restrict which types of containers can contain
instances of your classes.  In other words, when you register a
class, it will appear in the product add list in folders if the user
has the constructor permission.

See the *API Reference* for more information on the
``ProductRegistrar`` interface.

Factories and Constructors
--------------------------

Factories allow you to create Zope objects that can be added to
folders and other object managers.  Factories are discussed in
Chapter 12 of the *Zope Book*.  The basic work a factory does is to
put a name into the product add list and associate a permission and
an action with that name.  If you have the required permission then
the name will appear in the product add list, and when you select the
name from the product add list, the action method will be called.

Products use Zope factory capabilities to allow instances of product
classes to be created with the product add list.  In the above
example of product initialization you saw how a factory is created by
the product registrar.  Now let's see how to create the add form and
the add list.

The add form is a function that returns an HTML form that allows a
users to create an instance of your product class.  Typically this
form collects that id and title of the instance along with other
relevant data.  Here's a very simple add form function for the poll
class::

  def addForm():
      """Returns an HTML form."""
      return """<html>
      <head><title>Add Poll</title></head>
      <body>
      <form action="addFunction">
      id <input type="type" name="id"><br>
      question <input type="type" name="question"><br>
      responses (one per line)
      <textarea name="responses:lines"></textarea>
      </form>
      </body>
      </html>"""

Notice how the action of the form is ``addFunction``.  Also notice
how the lines of the response are marshalled into a sequence.  See
Chapter 2 for more information about argument marshalling and object
publishing.

It's also important to include a HTML ``head`` tag in the add form.
This is necessary so that Zope can set the base URL to make sure that
the relative link to the ``addFunction`` works correctly.

The add function will be passed a ``FactoryDispatcher`` as its first
argument which proxies the location (usually a Folder) where your
product was added.  The add function may also be passed any form
variables which are present in your add form according to normal
object publishing rules.

Here's an add function for your poll class::

  def addFunction(dispatcher, id, question, responses):
      """Create a new poll and add it to myself
      """
      p = PollProduct(id, question, responses)
      dispatcher.Destination()._setObject(id, p)

The dispatcher has three methods:

- ``Destination`` -- The ``ObjectManager`` where your product was added.

- ``DestinationURL`` -- The URL of the ``ObjectManager`` where your
  product was added.

- ``manage_main`` -- Redirects to a management view of the
  ``ObjectManager`` where your product was added.

Notice how it calls the ``_setObject()`` method of the destination
``ObjectManager`` class to add the poll to the folder.  See the *API
Reference* for more information on the ``ObjectManager`` interface.

The add function should also check the validity of its input.  For
example the add function should complain if the question or response
arguments are not of the correct type.

Finally you should recognize that the constructor functions are *not*
methods on your product class.  In fact they are called before any
instances of your product class are created.  The constructor
functions are published on the web so they need to have doc strings,
and are protected by a permission defined in during product
initialization.

Testing
-------

Now you're ready to register your product with Zope.  You need to add
the add form and add method to the poll module.  Then you should
create a `Poll` directory in your `lib/python/Products` directory and
add the `Poll.py`, `PollProduct.py`, and `__init__.py` files.  Then
restart Zope.

Now login to Zope as a manager and visit the web management
interface.  You should see a 'Poll' product listed inside the
*Products* folder in the *Control_Panel*.  If Zope had trouble
initializing your product you will see a traceback here.  Fix your
problems, if any and restart Zope.  If you are tired of all this
restarting, take a look at the *Refresh* facility covered in Chapter
7.

Now go to the root folder.  Select *Poll* from the product add list.
Notice how you are taken to the add form.  Provide an id, a question,
and a list of responses and click *Add*.  Notice how you get a black
screen.  This is because your add method does not return anything.
Notice also that your poll has a broken icon, and only has the
management views.  Don't worry about these problems now, you'll find
out how to fix these problems in the next section.

Now you should build some DTML Methods and Python Scripts to test
your poll instance.  Here's a Python Script to figure out voting
percentages::

  ## Script (Python) "getPercentFor"
  ##parameters=index
  ##
  """Returns the percentage of the vote given a response index. Note,
  this script should be bound a poll by acquisition context."""
  poll = context
  return float(poll.getVotesFor(index)) / poll.getTotalVotes()


Here's a DTML Method that displays poll results and allows you to
vote::

  <dtml-var standard_html_header>

  <h2>
    <dtml-var getQuestion>
  </h2>

  <form> <!-- calls this dtml method -->

  <dtml-in getResponses>
    <p>
      <input type="radio" name="index" value="&dtml-sequence-index;">
      <dtml-var sequence-item>
    </p>
  </dtml-in>

  <input type="submit" value=" Vote ">

  </form>

  <!-- process form -->

  <dtml-if index>
    <dtml-call expr="castVote(index)">
  </dtml-if>

  <!-- display results -->

  <h2>Results</h2>

  <p><dtml-var getTotalVotes> votes cast</p>

  <dtml-in getResponses>
    <p>
      <dtml-var sequence-item> -
      <dtml-var expr="getPercentFor(_.get('sequence-index'))">%
    </p>
  </dtml-in>

  <dtml-var standard_html_footer>

To use this DTML Method, call it on your poll instance.  Notice how
this DTML makes calls to both your poll instance and the
``getPercentFor`` Python script.

At this point there's quite a bit of testing and refinement that you
can do.  Your main annoyance will be having to restart Zope each time
you make a change to your product class (but see Chapter 9 for
information on how to avoid all this restarting).  If you vastly
change your class you may break existing poll instances, and will
need to delete them and create new ones.  See Chapter 9 for more
information on debugging techniques which will come in handy.

Building Management Interfaces
------------------------------

Now that you have a working product let's see how to beef up its user
interface and create online management facilities.

Defining Management Views
-------------------------

All Zope products can be managed through the web.  Products have a
collection of management tabs or *views* which allow managers to
control different aspects of the product.

A product's management views are defined in the ``manage_options``
class attribute.  Here's an example::

        manage_options=(
            {'label' : 'Edit', 'action' : 'editMethod'},
            {'label' : 'View', 'action' : 'viewMethod'},
            )

The ``manage_options`` structure is a tuple that contains
dictionaries.  Each dictionary defines a management view.  The view
dictionary can have a number of items.

- 'label' -- This is the name of the management view

- 'action' -- This is the URL that is called when the view is
  chosen. Normally this is the name of a method that displays a
  management view.

- 'target' -- An optional target frame to display the action. This
  item is rarely needed.

- 'help' -- Optional help information associated with the
  view. You'll find out more about this option later.

Management views are displayed in the order they are defined.
However, only those management views for which the current user has
permissions are displayed.  This means that different users may see
different management views when managing your product.

Normally you will define a couple custom views and reusing some
existing views that are defined in your base classes.  Here's an
example::

  class PollProduct(..., Item):
      ...

      manage_options=(
          {'label' : 'Edit', 'action' : 'editMethod'},
          {'label' : 'Options', 'action' : 'optionsMethod'},
          ) + RoleManager.manage_options + Item.manage_options

This example would include the standard management view defined by
``RoleManager`` which is *Security* and those defined by ``Item``
which are *Undo* and *Ownership*.  You should include these standard
management views unless you have good reason not to. If your class
has a default view method (``index_html``) you should also include a
*View* view whose action is an empty string.  See Chapter 2 for more
information on ``index_html``.

Note: you should not make the *View* view the first view on your
class.  The reason is that the first management view is displayed
when you click on an object in the Zope management interface.  If the
*View* view is displayed first, users will be unable to navigate to
the other management views since the view tabs will not be visible.

Creating Management Views
-------------------------

The normal way to create management view methods is to use DTML.  You
can use the ``DTMLFile`` class to create a DTML Method from a file.
For example::

  from Globals import DTMLFile

  class PollProduct(...):
    ...

    editForm = DTMLFile('dtml/edit', globals())
    ...

This creates a DTML Method on your class which is defined in the
`dtml/edit.dtml` file.  Notice that you do not have to include the
``.dtml`` file extension.  Also, don't worry about the forward slash
as a path separator; this convention will work fine on Windows. By
convention DTML files are placed in a ``dtml`` subdirectory of your
product.  The ``globals()`` argument to the ``DTMLFile`` constructor
allows it to locate your product directory.  If you are running Zope
in debug mode then changes to DTML files are reflected right away. In
other words you can change the DTML of your product's views without
restarting Zope to see the changes.

DTML class methods are callable directly from the web, just like
other methods.  So now users can see your edit form by calling the
``editForm`` method on instances of your poll class.  Typically DTML
methods will make calls back to your instance to gather information
to display.  Alternatively you may decide to wrap your DTML methods
with normal methods.  This allows you to calculate information needed
by your DTML before you call it.  This arrangement also ensures that
users always access your DTML through your wrapper.  Here's an
example::

  from Globals import DTMLFile

  class PollProduct(...):
    ...

    _editForm = DTMLFile('dtml/edit', globals())

    def editForm(self, ...):
        ...

        return self._editForm(REQUEST, ...)


When creating management views you should include the DTML variables
``manage_page_header`` and ``manage_tabs`` at the top, and
``manage_page_footer`` at the bottom.  These variables are acquired
by your product and draw a standard management view header, tabs
widgets, and footer.  The management header also includes CSS
information which you can take advantage of. You can use any of the styles
Bootstrap 4 provides - see https://getbootstrap.com/docs/4.6/.

Here's an example management view for your poll class.  It allows you
to edit the poll question and responses (see ``editPollForm.dtml``)::

  <dtml-var manage_page_header>
  <dtml-var manage_tabs>

  <p class="form-help">
  This form allows you to change the poll's question and
  responses. <b>Changing a poll's question and responses
  will reset the poll's vote tally.</b>.
  </p>

  <form action="editPoll">
  <table>

    <tr valign="top">
      <th class="form-label">Question</th>
      <td><input type="text" name="question" class="form-element"
      value="&dtml-getQuestion;"></td>
    </tr>

    <tr valign="top">
      <th class="form-label">Responses</th>
      <td><textarea name="responses:lines" cols="50" rows="10">
      <dtml-in getResponses>
      <dtml-var sequence-item html_quote>
      </dtml-in>
      </textarea>
      </td>
    </tr>

    <tr>
      <td></td>
      <td><input type="submit" value="Change" class="form-element"></td>
    </tr>

  </table>
  </form>

  <dtml-var manage_page_header>

This DTML method displays an edit form that allows you to change the
questions and responses of your poll.  Notice how poll properties are
HTML quoted either by using ``html_quote`` in the ``dtml-var`` tag,
or by using the ``dtml-var`` entity syntax.

Assuming this DTML is stored in a file ``editPollForm.dtml`` in your
product's ``dtml`` directory, here's how to define this method on
your class::

  class PollProduct(...):
      ...

      security.declareProtected('View management screens', 'editPollForm')
      editPollForm = DTML('dtml/editPollForm', globals())

Notice how the edit form is protected by the `View management
screens` permission.  This ensures that only managers will be able to
call this method.

Notice also that the action of this form is ``editPoll``.  Since the
poll as it stands doesn't include any edit methods you must define
one to accept the changes.  Here's an ``editPoll`` method::

  class PollProduct(...):
      ...

      def __init__(self, id, question, responses):
          self.id = id
          self.editPoll(question, response)

      ...

      security.declareProtected('Change Poll', 'editPoll')
      def editPoll(self, question, responses):
          """
          Changes the question and responses.
          """
          self._question = question
          self._responses = responses
          self._votes = {}
          for i in range(len(responses)):
              self._votes[i] = 0

Notice how the ``__init__`` method has been refactored to use the new
``editPoll`` method.  Also notice how the ``editPoll`` method is
protected by a new permissions, ``Change Poll``.

There still is a problem with the ``editPoll`` method.  When you call
it from the ``editPollForm`` through the web nothing is returned.
This is a bad management interface.  You want this method to return
an HTML response when called from the web, but you do not want it to
do this when it is called from ``__init__``.  Here's the solution::

  class Poll(...):
      ...

      def editPoll(self, question, responses, REQUEST=None):
          """Changes the question and responses."""
          self._question = question
          self._responses = responses
          self._votes = {}
          for i in range(len(responses)):
              self._votes[i] = 0
          if REQUEST is not None:
              return self.editPollForm(REQUEST,
                  manage_tabs_message='Poll question and responses changed.')

If this method is called from the web, then Zope will automatically
supply the ``REQUEST`` parameter.  (See chapter 4 for more
information on object publishing).  By testing the ``REQUEST`` you
can find out if your method was called from the web or not.  If you
were called from the web you return the edit form again.

A management interface convention that you should use is the
``manage_tab_message`` DTML variable.  If you set this variable when
calling a management view, it displays a status message at the top of
the page.  You should use this to provide feedback to users
indicating that their actions have been taken when it is not obvious.
For example, if you don't return a status message from your
``editPoll`` method, users may be confused and may not realize that
their changes have been made.

Sometimes when displaying management views, the wrong tab will be
highlighted.  This is because 'manage_tabs' can't figure out from the
URL which view should be highlighted.  The solution is to set the
'management_view' variable to the label of the view that should be
highlighted.  Here's an example, using the 'editPoll' method::

  def editPoll(self, question, responses, REQUEST=None):
      """
      Changes the question and responses.
      """
      self._question = question
      self._responses = responses
      self._votes = {}
      for i in range(len(responses)):
          self._votes[i] = 0
      if REQUEST is not None:
          return self.editPollForm(REQUEST,
              management_view='Edit',
              manage_tabs_message='Poll question and responses changed.')

Now let's take a look a how to define an icon for your product.

Icons
-----

Zope products are identified in the management interface with icons.
An icon should be a 16 by 16 pixel GIF image with a transparent
background.  Normally icons files are located in a ``www``
subdirectory of your product package.  To associate an icon with a
product class, use the ``icon`` parameter to the ``registerClass``
method in your product's constructor.  For example::

  def initialize(registrar):
      registrar.registerClass(
          PollProduct,
          constructors=(addForm, addFunction),
          icon='www/poll.gif'
          )

Notice how in this example, the icon is identified as being within
the product's ``www`` subdirectory.

See the *API Reference* for more information on the ``registerClass``
method of the ``ProductRegistrar`` interface.

Online Help
-----------

Zope has an online help system that you can use to provide help for
your products.  Its main features are context-sensitive help and API
help.  You should provide both for your product.


Context Sensitive Help
----------------------

To create context sensitive help, create one help file per management
view in your product's ``help`` directory.  You have a choice of
formats including: HTML, DTML, structured text, GIF, JPG, and PNG.

Register your help files at product initialization with the
``registerHelp()`` method on the registrar object::

  def initialize(registrar):
      ...
      registrar.registerHelp()

This method will take care of locating your help files and creating
help topics for each help file.  It can recognize these file
extensions: ``.html``, ``.htm``, ``.dtml``, ``.txt``, ``.stx``,
``.gif``, ``.jpg``, ``.png``.

If you want more control over how your help topics are created you
can use the ``registerHelpTopic()`` method which takes an id and a
help topic object as arguments.  For example::

  from mySpecialHelpTopics import MyTopic

  def initialize(context):
      ...
      context.registerHelpTopic('myTopic', MyTopic())

Your help topic should adhere to the 'HelpTopic' interface. See the
*API Reference* for more details.

The chief way to bind a help topic to a management screen is to
include information about the help topic in the class's
manage_options structure. For example::

  manage_options = (
      {'label': 'Edit',
       'action': 'editMethod',
       'help': ('productId','topicId')},
      )

The `help` value should be a tuple with the name of your product's
Python package, and the file name (or other id) of your help topic.
Given this information, Zope will automatically draw a *Help* button
on your management screen and link it to your help topic.

To draw a help button on a management screen that is not a view (such
as an add form), use the 'HelpButton' method of the 'HelpSys' object
like so::

  <dtml-var "HelpSys.HelpButton('productId', 'topicId')">

This will draw a help button linked to the specified help topic.  If
you prefer to draw your own help button you can use the helpURL
method instead like so::

  <dtml-var "HelpSys.helpURL(
    topic='productId',
    product='topicId')">

This will give you a URL to the help topic.  You can choose to draw
whatever sort of button or link you wish.

Other User Interfaces
---------------------

In addition to providing a through the web management interface your
products may also support many other user interfaces.  You product
might have no web management interfaces, and might be controlled
completely through some other network protocol.  Zope provides
interfaces and support for WebDAV and XML-RPC.  If this isn't
enough you can add other protocols.

WebDAV Interfaces
-----------------

WebDAV treats Zope objects like files and
directories.  See Chapter 3 for more information on WebDAV.

By simply sub-classing from 'SimpleItem.Item' and 'ObjectManager' if
necessary, you gain basic WebDAV support.  Without any work
your objects will appear in directory listings and if your class
is an 'ObjectManager' its contents will be accessible via WebDAV.
See Chapter 2 for more information on implementing WebDAV support.

XML-RPC and Network Services
----------------------------

XML-RPC is covered in Chapter 2.  All your product's methods can be
accessible via XML-RPC.  However, if your are implementing network
services, you should explicitly plan one or more methods for use with
XML-RPC.

Since XML-RPC allows marshalling of simple strings, lists, and
dictionaries, your XML-RPC methods should only accept and return
these types.  These methods should never accept or return Zope
objects.  XML-RPC also does not support 'None' so you should use zero
or something else in place of 'None'.

Another issue to consider when using XML-RPC is security.  Many
XML-RPC clients still don't support HTTP basic authorization.
Depending on which XML-RPC clients you anticipate, you may wish to
make your XML-RPC methods public and accept authentication
credentials as arguments to your methods.

Packaging Products
------------------

Zope products are normally packaged as tarballs.  You should create
your product tarball in such a way as to allow it to be unpacked in
the Products directory.  For example, `cd` to the Products directory
and then issue a `tar` comand like so::

  $ tar zcvf MyProduct-1.0.1.tgz MyProduct

This will create a gzipped tar archive containing your product.  You
should include your product name and version number in file name of
the archive.

See the `Poll-1.0.tgz <examples/Poll-1.0.tgz>`_ file for an example
of a fully packaged Python product.


Product Information Files
-------------------------

Along with your Python and ZPT files you should include some
information about your product in its root directory.

- `README.txt` -- Provides basic information about your product.
   Zope will parse this file as StructuredText and make it available
   on the *README* view of your product in the control panel.

- `VERSION.txt` -- Contains the name and version of your product on a
  single line. For example, 'Multiple Choice Poll 1.1.0'.  Zope will
  display this information as the 'version' property of your product
  in the control panel.

- `LICENSE.txt` -- Contains your product license, or a link to it.

You may also wish to provide additional information.  Here are some
suggested optional files to include with your product.

- `INSTALL.txt` -- Provides special instructions for installing the
  product and components on which it depends.  This file is only
  optional if your product does not require more than an ungzip/untar
  into a Zope installation to work.

- `TODO.txt` -- This file should make clear where this product
  release needs work, and what the product author intends to do about
  it.

- `CHANGES.txt` and `HISTORY.txt` -- 'CHANGES.txt' should enumerate
  changes made in particular product versions from the last release
  of the product. Optionally, a 'HISTORY.txt' file can be used for
  older changes, while 'CHANGES.txt' lists only recent changes.

- `DEPENDENCIES.txt` -- Lists dependencies including required os
  platform, required Python version, required Zope version, required
  Python packages, and required Zope products.

Product Directory Layout
------------------------

By convention your product will contain a number of sub-directories.
Some of these directories have already been discussed in this
chapter. Here is a summary of them.

- `www` -- Contains your icon & ZPT files.

- `help` -- Contains your help files.

- `tests` -- Contains your unit tests.

It is not necessary to include these directories if your don't have
anything to go in them.

Evolving Products
=================

As you develop your product classes you will generally make a series
of product releases.  While you don't know in advance how your
product will change, when it does change there are measures that you
can take to minimize problems.

Evolving Classes
----------------

Issues can occur when you change your product class because instances
of these classes are generally persistent.  This means that instances
created with an old class will start using a new class.  If your
class changes drastically this can break existing instances.

The simplest way to handle this situation is to provide class
attributes as defaults for newly added attributes.  For example if
the latest version of your class expects an 'improved_spam' instance
attribute while earlier versions only sported 'spam' attributes, you
may wish to define an 'improved_spam' class attribute in your new
class so your old objects won't break when they run with your new
class.  You might set 'improved_spam' to None in your class, and in
methods where you use this attribute you may have to take into
account that it may be None.  For example::

  class Sandwich(...):

      improved_spam = None
      ...

      def assembleSandwichMeats(self):
          ...
          # test for old sandwich instances
          if self.improved_spam is None:
              self.updateToNewSpam()
          ...

Another solution is to use the standard Python pickling hook
'__setstate__', however, this is in general more error prone and
complex.

A third option is to create a method to update old instances.  Then
you can manually call this method on instances to update to them.
Note, this won't work unless the instances function well enough to be
accessible via the Zope management screens.

While you are developing a product you won't have to worry too much
about these details, since you can always delete old instances that
break with new class definitions.  However, once you release your
product and other people start using it, then you need to start
planning for the eventuality of upgrading.

Another nasty problem that can occur is breakage caused by renaming
your product classes.  You should avoid this since it breaks all
existing instances.  If you really must change your class name,
provide aliases to it using the old name.  You may however, change
your class's base classes without causing these kinds of problems.

Evolving Interfaces
-------------------

The basic rule of evolving interfaces is *don't do it*.  While you
are working privately you can change your interfaces all you wish.
But as soon as you make your interfaces public you should freeze
them.  The reason is that it is not fair to users of your interfaces
to changes them after the fact.  An interface is contract.  It
specifies how to use a component and it specifies how to implement
types of components.  Both users and developers will have problems if
your change the interfaces they are using or implementing.

The general solution is to create simple interfaces in the first
place, and create new ones when you need to change an existing
interface.  If your new interfaces are compatible with your existing
interfaces you can indicate this by making your new interfaces extend
your old ones.  If your new interface replaces an old one but does
not extend it you should give it a new name such as,
``WidgetWithBellsOn``.  Your components should continue to support
the old interface in addition to the new one for a few releases.

Conclusion
==========

Migrating your components into fully fledged Zope products is a
process with a number of steps.  There are many details to keep track
of.  However, if you follow the recipe laid out in this chapter you
should have no problems.

Zope products are a powerful framework for building web applications.
By creating products you can take advantage of Zope's features
including security, scalability, through the web management, and
collaboration.
