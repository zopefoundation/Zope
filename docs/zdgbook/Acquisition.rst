###########
Acquisition
###########

.. include:: includes/zope2_notice.rst

Acquisition is a mechanism that allows objects to obtain attributes
from their environment.  It is similar to inheritance, except that,
rather than searching an inheritance hierarchy to obtain attributes,
a containment hierarchy is traversed.


Introductory Example
====================

Zope implements acquisition with "Extension Class" mix-in classes. To
use acquisition your classes must inherit from an acquisition base
class. For example::

  import ExtensionClass, Acquisition

  class C(ExtensionClass.Base):
    color = 'red'

  class A(Acquisition.Implicit):

    def report(self):
      print self.color

  a = A()
  c = C()
  c.a = A()

  c.a.report() # prints 'red'

  d = C()
  d.color = 'green'
  d.a = a

  d.a.report() # prints 'green'

  a.report() # raises an attribute error

The class 'A' inherits acquisition behavior from
'Acquisition.Implicit'.  The object, 'a', "has" the color of objects
'c' and 'd' when it is accessed through them, but it has no color by
itself.  The object 'a' obtains attributes from its environment,
where its environment is defined by the access path used to reach
'a'.

Acquisition Wrappers
====================

When an object that supports acquisition is accessed through an
extension class instance, a special object, called an acquisition
wrapper, is returned.  In the example above, the expression 'c.a'
returns an acquisition wrapper that contains references to both 'c'
and 'a'.  It is this wrapper that performs attribute lookup in 'c'
when an attribute cannot be found in 'a'.

Acquisition wrappers provide access to the wrapped objects through
the attributes 'aq_parent', 'aq_self', 'aq_base'.  In the example
above, the expressions::

  'c.a.aq_parent is c'

and::

  'c.a.aq_self is a'


both evaluate to true, but the expression::

  'c.a is a'

evaluates to false, because the expression 'c.a' evaluates to an
acquisition wrapper around 'c' and 'a', not 'a' itself.

The attribute 'aq_base' is similar to 'aq_self'.  Wrappers may be
nested and 'aq_self' may be a wrapped object.  The 'aq_base'
attribute is the underlying object with all wrappers removed.

You can manually wrap an instance of an object that inherits from an
acquisition base class by using its '__of__' method. For example::

  class A(Acquisition.Implicit):
      pass

  a = A()
  a.color = 'red'
  b = A()
  a.b = b

  print b.__of__(a).color # prints red


The expression 'b.__of__(a)' wraps 'b' in an acquisition wrapper
explicitly, and returns the acquisition wrapper.  The 'color'
attrribute of 'a' is found via acquisition when this expression is
executed.


Explicit and Implicit Acquisition
=================================

Two styles of acquisition are supported: implicit and explicit
acquisition.

Implicit acquisition
--------------------

Implicit acquisition is so named because it searches for
attributes from the environment automatically whenever an
attribute cannot be obtained directly from an object or through
inheritance.

An attribute can be implicitly acquired if its name does not
begin with an underscore.

To support implicit acquisition, your class should inherit from
the mix-in class 'Acquisition.Implicit'.

Explicit Acquisition
--------------------

When explicit acquisition is used, attributes are not automatically
obtained from the environment.  Instead, the method 'aq_acquire' must
be used. For example::

  print c.a.aq_acquire('color')

To support explicit acquisition, your class should inherit from the
mix-in class 'Acquisition.Explicit'.

Controlling Acquisition
=======================

A class (or instance) can provide attribute by attribute control over
acquisition.  Your should subclass from 'Acquisition.Explicit', and
set all attributes that should be acquired to the special value
'Acquisition.Acquired'.  Setting an attribute to this value also
allows inherited attributes to be overridden with acquired ones.  For
example::

  class C(Acquisition.Explicit):
     id=1
     secret=2
     color=Acquisition.Acquired
     __roles__=Acquisition.Acquired

The *only* attributes that are automatically acquired from containing
objects are 'color', and '__roles__'.  Note that the '__roles__'
attribute is acquired even though its name begins with an underscore.
In fact, the special 'Acquisition.Acquired' value can be used in
'Acquisition.Implicit' objects to implicitly acquire selected objects
that smell like private objects.

Sometimes, you want to dynamically make an implicitly acquiring
object acquire explicitly. You can do this by getting the object's
'aq_explicit' attribute. This attribute provides the object with an
explicit wrapper that places the original implicit wrapper.

Filtered Acquisition
====================

The acquisition method, 'aq_acquire', accepts two optional
arguments. The first of the additional arguments is a "filtering"
function that is used when considering whether to acquire an object.
The second of the additional arguments is an object that is passed as
extra data when calling the filtering function and which defaults to
'None'.  The filter function is called with five arguments:

- The object that the 'aq_acquire' method was called on,

- The object where an object was found,

- The name of the object, as passed to 'aq_acquire',

- The object found, and

- The extra data passed to 'aq_acquire'.

If the filter returns a true object that the object found is
returned, otherwise, the acquisition search continues.

For example, in::

  from Acquisition import Explicit

  class HandyForTesting:
      def __init__(self, name):
          self.name = name
      def __str__(self):
          return "%s(%s)" % (self.name, self.__class__.__name__)
      __repr__ = __str__

  class E(Explicit, HandyForTesting): pass

  class Nice(HandyForTesting):
      isNice = 1
      def __str__(self):
          return HandyForTesting.__str__(self) + ' and I am nice!'
      __repr__ = __str__

  a = E('a')
  a.b = E('b')
  a.b.c = E('c')
  a.p = Nice('spam')
  a.b.p = E('p')

  def find_nice(self, ancestor, name, object, extra):
      return hasattr(object,'isNice') and object.isNice

  print a.b.c.aq_acquire('p', find_nice)

The filtered acquisition in the last line skips over the first
attribute it finds with the name 'p', because the attribute doesn't
satisfy the condition given in the filter. The output of the last
line is::

  spam(Nice) and I am nice!

Filtered acquisition is rarely used in Zope.

Acquiring from Context
======================

Normally acquisition allows objects to acquire data from their
containers. However an object can acquire from objects that aren't
its containers.

Most of the example's we've seen so far show establishing of an
acquisition *context* using 'getattr' symanitics. For example, 'a.b'
is a reference to 'b' in the context of 'a'.


You can also manuallyset acquisition context using the '__of__'
method.  For example::

  from Acquisition import Implicit
  class C(Implicit): pass
  a = C()
  b = C()
  a.color = "red"
  print b.__of__(a).color # prints red

In this case, 'a' does not contain 'b', but it is put in 'b''s
context using the '__of__' method.

Here's another subtler example that shows how you can construct an
acquisition context that includes non-container objects::

  from Acquisition import Implicit

  class C(Implicit):
      def __init__(self, name):
          self.name = name

  a = C("a")
  a.b = C("b")
  a.b.color = "red"
  a.x = C("x")

  print a.b.x.color # prints red

Even though 'b' does not contain 'x', 'x' can acquire the 'color'
attribute from 'b'. This works because in this case, 'x' is accessed
in the context of 'b' even though it is not contained by 'b'.

Here acquisition context is defined by the objects used to access
another object.

Containment Before Context
==========================

If in the example above suppose both 'a' and 'b' have an 'color'
attribute::

  a = C("a")
  a.color = "green"
  a.b = C("b")
  a.b.color = "red"
  a.x = C("x")

  print a.b.x.color # prints green


Why does 'a.b.x.color' acquire 'color' from 'a' and not from 'b'?
The answer is that an object acquires from its containers before
non-containers in its context.

To see why consider this example in terms of expressions using the
'__of__' method::

   a.x -> x.__of__(a)

   a.b -> b.__of__(a)

   a.b.x -> x.__of__(a).__of__(b.__of__(a))

Keep in mind that attribute lookup in a wrapper is done by trying to
look up the attribute in the wrapped object first and then in the
parent object.  So in the expressions above proceeds from left to
right.


The upshot of these rules is that attributes are looked up by
containment before context.

This rule holds true also for more complex examples. For example,
'a.b.c.d.e.f.g.attribute' would search for 'attribute' in 'g' and all
its containers first. (Containers are searched in order from the
innermost parent to the outermost container.) If the attribute is not
found in g or any of its containers, then the search moves to 'f' and
all its containers, and so on.

Additional Attributes and Methods
=================================

You can use the special method 'aq_inner' to access an object wrapped
only by containment. So in the example above::

  a.b.x.aq_inner

is equivalent to::

  a.x

You can find out the acquisition context of an object using the
'aq_chain' method like so::

  a.b.x.aq_chain # returns [x, b, a]

You can find out if an object is in the acquisition context of
another object using the 'aq_inContextOf' method. For example::

  a.b.x.aq_inContextOf(a.b) # returns 1


You can also pass an additional argument to 'aq_inContextOf' to
indicate whether to only check containment rather than the full
acquisition context. For example::

  a.b.x.aq_inContextOf(a.b, 1) # returns 0

Note: as of this writing the 'aq_inContextOf' examples don't
work. According to Jim, this is because 'aq_inContextOf' works by
comparing object pointer addresses, which (because they are actually
different wrapper objects) doesn't give you the expected results. He
acknowledges that this behavior is controversial, and says that there
is a collector entry to change it so that you would get the answer
you expect in the above. (We just need to get to it).


Acquisition Module Functions
----------------------------

In addition to using acquisition attributes and methods directly on
objects you can use similar functions defined in the 'Acquisition'
module. These functions have the advantage that you don't need to
check to make sure that the object has the method or attribute before
calling it.

'aq_acquire(object, name [, filter, extra, explicit, default, containment])' -- Acquires an object with the given name.

This function can be used to explictly acquire when using explicit
acquisition and to acquire names that wouldn't normally be acquired.

The function accepts a number of optional arguments:

- 'filter' -- A callable filter object that is used to decide if an
  object should be acquired.

  The filter is called with five arguments:

  - The object that the aq_acquire method was called on,

  - The object where an object was found,

  - The name of the object, as passed to aq_acquire,

  - The object found, and

  - The extra argument passed to aq_acquire.

  If the filter returns a true object that the object found is
  returned, otherwise, the acquisition search continues.

- 'extra' -- extra data to be passed as the last argument to the
  filter.

- 'explicit' -- A flag (boolean value) indicating whether explicit
  acquisition should be used. The default value is true.  If the flag
  is true, then acquisition will proceed regardless of whether
  wrappers encountered in the search of the acquisition hierarchy are
  explicit or implicit wrappers. If the flag is false, then parents
  of explicit wrappers are not searched.

  This argument is useful if you want to apply a filter without
  overriding explicit wrappers.

- 'default' -- A default value to return if no value can be acquired.

- 'containment' -- A flag indicating whether the search should be
  limited to the containment hierarchy.

In addition, arguments can be provided as keywords.

- 'aq_base(object)' -- Return the object with all wrapping removed.

- 'aq_chain(object [, containment])' -- Return a list containing the
  object and it's acquisition parents. The optional argument,
  'containment', controls whether the containment or access hierarchy
  is used.

- 'aq_get(object, name [, default, containment])' -- Acquire an
  attribute, name. A default value can be provided, as can a flag
  that limits search to the containment hierarchy.

- 'aq_inner(object)' -- Return the object with all but the innermost
  layer of wrapping removed.

- 'aq_parent(object)' -- Return the acquisition parent of the object
  or 'None' if the object is unwrapped.

- 'aq_self(object)' -- Return the object with one layer of wrapping
  removed, unless the object is unwrapped, in which case the object
  is returned.

In most cases it is more convenient to use these module functions
instead of the acquisition attributes and methods directly.

Acquisition and Methods
=======================

Python methods of objects that support acquisition can use acquired
attributes.  When a Python method is called on an object that is
wrapped by an acquisition wrapper, the wrapper is passed to the
method as the first argument.  This rule also applies to user-defined
method types and to C methods defined in pure mix-in classes.

Unfortunately, C methods defined in extension base classes that
define their own data structures, cannot use aquired attributes at
this time.  This is because wrapper objects do not conform to the
data structures expected by these methods. In practice, you will
seldom find this a problem.

Conclusion
==========

Acquisition provides a powerful way to dynamically share information
between objects. Zope using acquisition for a number of its key
features including security, object publishing, and DTML variable
lookup. Acquisition also provides an elegant solution to the problem
of circular references for many classes of problems. While
acquisition is powerful, you should take care when using acquisition
in your applications. The details can get complex, especially with
the differences between acquiring from context and acquiring from
containment.
