##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Acquisition test cases (and useful examples)

  Acquisition [1] is a mechanism that allows objects to obtain
  attributes from their environment.  It is similar to inheritence,
  except that, rather than traversing an inheritence hierarchy
  to obtain attributes, a containment hierarchy is traversed.

  The "ExtensionClass":ExtensionClass.html. release includes mix-in
  extension base classes that can be used to add acquisition as a
  feature to extension subclasses.  These mix-in classes use the
  context-wrapping feature of ExtensionClasses to implement
  acquisition. Consider the following example::

    >>> import ExtensionClass, Acquisition

    >>> class C(ExtensionClass.Base):
    ...   color='red'

    >>> class A(Acquisition.Implicit):
    ...   def report(self):
    ...     print self.color

    >>> a = A()
    >>> c = C()
    >>> c.a = a

    >>> c.a.report()
    red

    >>> d = C()
    >>> d.color = 'green'
    >>> d.a = a

    >>> d.a.report()
    green

    >>> a.report() # raises an attribute error
    Traceback (most recent call last):
    ...
    AttributeError: color

  The class 'A' inherits acquisition behavior from
  'Acquisition.Implicit'.  The object, 'a', "has" the color of
  objects 'c' and 'd' when it is accessed through them, but it
  has no color by itself.  The object 'a' obtains attributes
  from it's environment, where it's environment is defined by
  the access path used to reach 'a'.

  Acquisition wrappers

    When an object that supports acquisition is accessed through
    an extension class instance, a special object, called an
    acquisition wrapper, is returned.  In the example above, the
    expression 'c.a' returns an acquisition wrapper that
    contains references to both 'c' and 'a'.  It is this wrapper
    that performs attribute lookup in 'c' when an attribute
    cannot be found in 'a'.

    Aquisition wrappers provide access to the wrapped objects
    through the attributes 'aq_parent', 'aq_self', 'aq_base'.  
    In the example above, the expressions::
      
       >>> c.a.aq_parent is c
       1

    and::

       >>> c.a.aq_self is a
       1

    both evaluate to true, but the expression::

       >>> c.a is a
       0

    evaluates to false, because the expression 'c.a' evaluates
    to an acquisition wrapper around 'c' and 'a', not 'a' itself.

    The attribute 'aq_base' is similar to 'aq_self'.  Wrappers may be
    nested and 'aq_self' may be a wrapped object.  The 'aq_base'
    attribute is the underlying object with all wrappers removed.

  Acquisition Control

    Two styles of acquisition are supported in the current
    ExtensionClass release, implicit and explicit aquisition.
  
    Implicit acquisition
    
      Implicit acquisition is so named because it searches for
      attributes from the environment automatically whenever an
      attribute cannot be obtained directly from an object or
      through inheritence.
  
      An attribute may be implicitly acquired if it's name does
      not begin with an underscore, '_'.
  
      To support implicit acquisition, an object should inherit
      from the mix-in class 'Acquisition.Implicit'.
  
    Explicit Acquisition
  
      When explicit acquisition is used, attributes are not
      automatically obtained from the environment.  Instead, the
      method 'aq_aquire' must be used, as in::
  
        print c.a.aq_acquire('color')
  
      To support explicit acquisition, an object should inherit
      from the mix-in class 'Acquisition.Explicit'.

    Controlled Acquisition

      A class (or instance) can provide attribute by attribute control
      over acquisition.  This is done by:

      - subclassing from 'Acquisition.Explicit', and

      - setting all attributes that should be acquired to the special
        value: 'Acquisition.Acquired'.  Setting an attribute to this
        value also allows inherited attributes to be overridden with
        acquired ones.

        For example, in::

          >>> class E(Acquisition.Explicit):
          ...    id = 1
          ...    secret = 2
          ...    color = Acquisition.Acquired
          ...    __roles__ = Acquisition.Acquired

        The *only* attributes that are automatically acquired from
        containing objects are 'color', and '__roles__'.

          >>> c = C()
          >>> c.foo = 'foo'
          >>> c.e = E()
          >>> c.e.color
          'red'
          >>> c.e.foo
          Traceback (most recent call last):
          ...
          AttributeError: foo

        Note also that the '__roles__' attribute is acquired even
        though it's name begins with an underscore:

          >>> c.__roles__ = 'Manager', 'Member'
          >>> c.e.__roles__
          ('Manager', 'Member')

        In fact, the special 'Acquisition.Acquired' value can be used
        in 'Acquisition.Implicit' objects to implicitly acquire
        selected objects that smell like private objects.

          >>> class I(Acquisition.Implicit):
          ...    __roles__ = Acquisition.Acquired

          >>> c.x = C()
          >>> c.x.__roles__
          Traceback (most recent call last):
          ...
          AttributeError: __roles__

          >>> c.x = I()
          >>> c.x.__roles__
          ('Manager', 'Member')

    Filtered Acquisition

      The acquisition method, 'aq_acquire', accepts two optional
      arguments. The first of the additional arguments is a
      "filtering" function that is used when considering whether to
      acquire an object.  The second of the additional arguments is an
      object that is passed as extra data when calling the filtering
      function and which defaults to 'None'.

      The filter function is called with five arguments:

      - The object that the 'aq_acquire' method was called on,

      - The object where an object was found,

      - The name of the object, as passed to 'aq_acquire',

      - The object found, and

      - The extra data passed to 'aq_acquire'.

      If the filter returns a true object that the object found is
      returned, otherwise, the acquisition search continues.

      For example, in::

        >>> from Acquisition import Explicit
        
        >>> class HandyForTesting:
        ...     def __init__(self, name): self.name=name
        ...     def __str__(self):
        ...       return "%s(%s)" % (self.name, self.__class__.__name__)
        ...     __repr__=__str__
        
        >>> class E(Explicit, HandyForTesting):
        ...     pass
        
        >>> class Nice(HandyForTesting):
        ...     isNice=1
        ...     def __str__(self):
        ...        return HandyForTesting.__str__(self)+' and I am nice!'
        ...     __repr__=__str__
        
        >>> a = E('a')
        >>> a.b = E('b')
        >>> a.b.c = E('c')
        >>> a.p = Nice('spam')
        >>> a.b.p = E('p')
        
        >>> def find_nice(self, ancestor, name, object, extra):
        ...     return hasattr(object,'isNice') and object.isNice
        
        >>> print a.b.c.aq_acquire('p', find_nice)
        spam(Nice) and I am nice!

      The filtered acquisition in the last line skips over the first
      attribute it finds with the name 'p', because the attribute
      doesn't satisfy the condition given in the filter.

  Acquisition and methods

    Python methods of objects that support acquisition can use
    acquired attributes as in the 'report' method of the first example
    above.  When a Python method is called on an object that is
    wrapped by an acquisition wrapper, the wrapper is passed to the
    method as the first argument.  This rule also applies to
    user-defined method types and to C methods defined in pure mix-in
    classes.

    Unfortunately, C methods defined in extension base classes that
    define their own data structures, cannot use aquired attributes at
    this time.  This is because wrapper objects do not conform to the
    data structures expected by these methods.

  Acquiring Acquiring objects

    Consider the following example::

      >>> from Acquisition import Implicit
      
      >>> class C(Implicit):
      ...     def __init__(self, name): self.name=name
      ...     def __str__(self):
      ...         return "%s(%s)" % (self.name, self.__class__.__name__)
      ...     __repr__=__str__
      
      >>> a = C("a")
      >>> a.b = C("b")
      >>> a.b.pref = "spam"
      >>> a.b.c = C("c")
      >>> a.b.c.color = "red"
      >>> a.b.c.pref = "eggs"
      >>> a.x = C("x")

      >>> o = a.b.c.x

    The expression 'o.color' might be expected to return '"red"'. In
    earlier versions of ExtensionClass, however, this expression
    failed.  Acquired acquiring objects did not acquire from the
    environment they were accessed in, because objects were only
    wrapped when they were first found, and were not rewrapped as they
    were passed down the acquisition tree.

    In the current release of ExtensionClass, the expression "o.color"
    does indeed return '"red"'.

      >>> o.color
      'red'

    When searching for an attribute in 'o', objects are searched in
    the order 'x', 'a', 'b', 'c'. So, for example, the expression,
    'o.pref' returns '"spam"', not '"eggs"'::

      >>> o.pref
      'spam'

    In earlier releases of ExtensionClass, the attempt to get the
    'pref' attribute from 'o' would have failed.

    If desired, the current rules for looking up attributes in complex
    expressions can best be understood through repeated application of
    the '__of__' method:

    'a.x' -- 'x.__of__(a)'

    'a.b' -- 'b.__of__(a)'

    'a.b.x' -- 'x.__of__(a).__of__(b.__of__(a))'

    'a.b.c' -- 'c.__of__(b.__of__(a))'

    'a.b.c.x' --
        'x.__of__(a).__of__(b.__of__(a)).__of__(c.__of__(b.__of__(a)))'

    and by keeping in mind that attribute lookup in a wrapper
    is done by trying to lookup the attribute in the wrapped object
    first and then in the parent object.  In the expressions above
    involving the '__of__' method, lookup proceeds from left to right.

    Note that heuristics are used to avoid most of the repeated
    lookups. For example, in the expression: 'a.b.c.x.foo', the object
    'a' is searched no more than once, even though it is wrapped three
    times.

.. [1] Gil, J., Lorenz, D., 
   "Environmental Acquisition--A New Inheritance-Like Abstraction Mechanism",
   http://www.bell-labs.com/people/cope/oopsla/Oopsla96TechnicalProgramAbstracts.html#GilLorenz, 
   OOPSLA '96 Proceedings, ACM SIG-PLAN, October, 1996

$Id$
"""

import ExtensionClass
import Acquisition

class I(Acquisition.Implicit):
    def __init__(self, id):
        self.id = id
    def __repr__(self):
        return self.id

class E(Acquisition.Explicit):
    def __init__(self, id):
        self.id = id
    def __repr__(self):
        return self.id

def test_unwrapped():
    """
    >>> c = I('unwrapped')
    >>> show(c)
    unwrapped

    >>> c.aq_parent
    Traceback (most recent call last):
    ...
    AttributeError: aq_parent

    >>> Acquisition.aq_acquire(c, 'id')
    'unwrapped'
    >>> Acquisition.aq_acquire(c, 'x')
    Traceback (most recent call last):
    ...
    AttributeError: x
    
    >>> Acquisition.aq_acquire(c, 'id',
    ...  lambda searched, parent, name, ob, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: id

    >>> Acquisition.aq_acquire(c, 'id',
    ...        lambda searched, parent, name, ob, extra: extra,
    ...        1)
    'unwrapped'

    >>> Acquisition.aq_base(c) is c
    1

    >>> Acquisition.aq_chain(c)
    [unwrapped]

    >>> Acquisition.aq_chain(c, 1)
    [unwrapped]

    >>> Acquisition.aq_get(c, 'id')
    'unwrapped'

    >>> Acquisition.aq_get(c, 'x')
    Traceback (most recent call last):
    ...
    AttributeError: x
    >>> Acquisition.aq_get(c, 'x', 'foo')
    'foo'
    >>> Acquisition.aq_get(c, 'x', 'foo', 1)
    'foo'

    >>> Acquisition.aq_inner(c) is c
    1

    >>> Acquisition.aq_parent(c)

    >>> Acquisition.aq_self(c) is c
    1

    
    
    """

def test_simple():
    """
    >>> a = I('a')
    >>> a.y = 42
    >>> a.b = I('b')
    >>> a.b.c = I('c')
    >>> show(a.b.c)
    c
    |
    b
    |
    a

    >>> show(a.b.c.aq_parent)
    b
    |
    a

    >>> show(a.b.c.aq_self)
    c

    >>> show(a.b.c.aq_base)
    c

    >>> show(a.b.c.aq_inner)
    c
    |
    b
    |
    a

    >>> a.b.c.y
    42

    >>> a.b.c.aq_chain
    [c, b, a]

    >>> a.b.c.aq_inContextOf(a)
    1
    >>> a.b.c.aq_inContextOf(a.b)
    1
    >>> a.b.c.aq_inContextOf(a.b.c)
    1


    >>> a.b.c.aq_acquire('y')
    42

    >>> a.b.c.aq_acquire('id')
    'c'

    >>> a.b.c.aq_acquire('x')
    Traceback (most recent call last):
    ...
    AttributeError: x
    
    >>> a.b.c.aq_acquire('id',
    ...  lambda searched, parent, name, ob, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: id

    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...        lambda searched, parent, name, ob, extra: extra,
    ...        1)
    'c'

    >>> Acquisition.aq_acquire(a.b.c, 'id')
    'c'

    >>> Acquisition.aq_acquire(a.b.c, 'x')
    Traceback (most recent call last):
    ...
    AttributeError: x

    >>> Acquisition.aq_acquire(a.b.c, 'y')
    42
    
    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...  lambda searched, parent, name, ob, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: id

    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...        lambda searched, parent, name, ob, extra: extra,
    ...        1)
    'c'

    >>> show(Acquisition.aq_base(a.b.c))
    c

    >>> Acquisition.aq_chain(a.b.c)
    [c, b, a]

    >>> Acquisition.aq_chain(a.b.c, 1)
    [c, b, a]

    >>> Acquisition.aq_get(a.b.c, 'id')
    'c'

    >>> Acquisition.aq_get(a.b.c, 'x')
    Traceback (most recent call last):
    ...
    AttributeError: x
    >>> Acquisition.aq_get(a.b.c, 'x', 'foo')
    'foo'
    >>> Acquisition.aq_get(a.b.c, 'x', 'foo', 1)
    'foo'

    >>> show(Acquisition.aq_inner(a.b.c))
    c
    |
    b
    |
    a

    >>> show(Acquisition.aq_parent(a.b.c))
    b
    |
    a

    >>> show(Acquisition.aq_self(a.b.c))
    c

    """

def test__of__exception():
    """
    Wrapper_findattr did't check for an exception in a user defined
    __of__ method before passing the result to the filter. In this
    case the 'value' argument of the filter was NULL, which caused
    a segfault when being accessed.

    >>> class UserError(Exception):
    ...     pass
    ...
    >>> class X(Acquisition.Implicit):
    ...     def __of__(self, parent):
    ...         if Acquisition.aq_base(parent) is not parent:
    ...             raise UserError, 'ack'
    ...         return X.inheritedAttribute('__of__')(self, parent)
    ...
    >>> a = I('a')
    >>> a.b = I('b')
    >>> a.b.x = X('x')
    >>> Acquisition.aq_acquire(a.b, 'x',
    ...     lambda self, object, name, value, extra: repr(value))
    Traceback (most recent call last):
    ...
    UserError: ack

    """

def test_muliple():
    r"""
    >>> a = I('a')
    >>> a.color = 'red'
    >>> a.a1 = I('a1')
    >>> a.a1.color = 'green'
    >>> a.a1.a11 = I('a11')
    >>> a.a2 = I('a2')
    >>> a.a2.a21 = I('a21')
    >>> show(a.a1.a11.a2.a21)
    a21
    |
    (a2)
    |  \
    |   (a2)
    |   |  \
    |   |   a2
    |   |   |
    |   |   a
    |   |
    |   a1
    |   |
    |   a
    |
    a11
    |
    a1
    |
    a

    >>> a.a1.a11.a2.a21.color
    'red'

    >>> show(a.a1.a11.a2.a21.aq_parent)
    (a2)
    |  \
    |   (a2)
    |   |  \
    |   |   a2
    |   |   |
    |   |   a
    |   |
    |   a1
    |   |
    |   a
    |
    a11
    |
    a1
    |
    a

    >>> show(a.a1.a11.a2.a21.aq_parent.aq_parent)
    a11
    |
    a1
    |
    a

    >>> show(a.a1.a11.a2.a21.aq_self)
    a21

    >>> show(a.a1.a11.a2.a21.aq_parent.aq_self)
    (a2)
    |  \
    |   a2
    |   |
    |   a
    |
    a1
    |
    a

    >>> show(a.a1.a11.a2.a21.aq_base)
    a21

    >>> show(a.a1.a11.a2.a21.aq_inner)
    a21
    |
    (a2)
    |  \
    |   (a2)
    |   |  \
    |   |   a2
    |   |   |
    |   |   a
    |   |
    |   a1
    |   |
    |   a
    |
    a11
    |
    a1
    |
    a

    >>> show(a.a1.a11.a2.a21.aq_inner.aq_parent.aq_inner)
    a2
    |
    a

    >>> show(a.a1.a11.a2.a21.aq_inner.aq_parent.aq_inner.aq_parent)
    a
    
    >>> a.a1.a11.a2.a21.aq_chain
    [a21, a2, a11, a1, a]
    
    >>> a.a1.a11.a2.a21.aq_inContextOf(a)
    1
    
    >>> a.a1.a11.a2.a21.aq_inContextOf(a.a2)
    1

    >>> a.a1.a11.a2.a21.aq_inContextOf(a.a1)
    0
    
    >>> a.a1.a11.a2.a21.aq_acquire('color')
    'red'
    >>> a.a1.a11.a2.a21.aq_acquire('id')
    'a21'

    >>> a.a1.a11.a2.a21.aq_acquire('color',
    ...     lambda ob, parent, name, v, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: color

    >>> a.a1.a11.a2.a21.aq_acquire('color',
    ...     lambda ob, parent, name, v, extra: extra, 1)
    'red'
    
    >>> a.a1.y = 42
    >>> a.a1.a11.a2.a21.aq_acquire('y')
    42

    >>> a.a1.a11.a2.a21.aq_acquire('y', containment=1)
    Traceback (most recent call last):
    ...
    AttributeError: y

    Much of the same, but with methods:

    >>> show(Acquisition.aq_parent(a.a1.a11.a2.a21))
    (a2)
    |  \
    |   (a2)
    |   |  \
    |   |   a2
    |   |   |
    |   |   a
    |   |
    |   a1
    |   |
    |   a
    |
    a11
    |
    a1
    |
    a

    >>> show(Acquisition.aq_parent(a.a1.a11.a2.a21.aq_parent))
    a11
    |
    a1
    |
    a

    >>> show(Acquisition.aq_self(a.a1.a11.a2.a21))
    a21

    >>> show(Acquisition.aq_self(a.a1.a11.a2.a21.aq_parent))
    (a2)
    |  \
    |   a2
    |   |
    |   a
    |
    a1
    |
    a

    >>> show(Acquisition.aq_base(a.a1.a11.a2.a21))
    a21

    >>> show(Acquisition.aq_inner(a.a1.a11.a2.a21))
    a21
    |
    (a2)
    |  \
    |   (a2)
    |   |  \
    |   |   a2
    |   |   |
    |   |   a
    |   |
    |   a1
    |   |
    |   a
    |
    a11
    |
    a1
    |
    a

    >>> show(Acquisition.aq_inner(a.a1.a11.a2.a21.aq_inner.aq_parent))
    a2
    |
    a

    >>> show(Acquisition.aq_parent(
    ...       a.a1.a11.a2.a21.aq_inner.aq_parent.aq_inner))
    a
    
    >>> Acquisition.aq_chain(a.a1.a11.a2.a21)
    [a21, a2, a11, a1, a]
    
    >>> Acquisition.aq_chain(a.a1.a11.a2.a21, 1)
    [a21, a2, a]
    
    >>> Acquisition.aq_acquire(a.a1.a11.a2.a21, 'color')
    'red'
    >>> Acquisition.aq_acquire(a.a1.a11.a2.a21, 'id')
    'a21'

    >>> Acquisition.aq_acquire(a.a1.a11.a2.a21, 'color',
    ...     lambda ob, parent, name, v, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: color

    >>> Acquisition.aq_acquire(a.a1.a11.a2.a21, 'color',
    ...     lambda ob, parent, name, v, extra: extra, 1)
    'red'
    
    >>> a.a1.y = 42
    >>> Acquisition.aq_acquire(a.a1.a11.a2.a21, 'y')
    42

    >>> Acquisition.aq_acquire(a.a1.a11.a2.a21, 'y', containment=1)
    Traceback (most recent call last):
    ...
    AttributeError: y


    """
    
def test_pinball():
    r"""
    >>> a = I('a')
    >>> a.a1 = I('a1')
    >>> a.a1.a11 = I('a11')
    >>> a.a1.a12 = I('a12')
    >>> a.a2 = I('a2')
    >>> a.a2.a21 = I('a21')
    >>> a.a2.a22 = I('a22')
    >>> show(a.a1.a11.a1.a12.a2.a21.a2.a22)
    a22
    |
    (a2)
    |  \
    |   (a2)
    |   |  \
    |   |   a2
    |   |   |
    |   |   a
    |   |
    |   (a2)
    |   |  \
    |   |   (a2)
    |   |   |  \
    |   |   |   a2
    |   |   |   |
    |   |   |   a
    |   |   |
    |   |   (a1)
    |   |   |  \
    |   |   |   (a1)
    |   |   |   |  \
    |   |   |   |   a1
    |   |   |   |   |
    |   |   |   |   a
    |   |   |   |
    |   |   |   a1
    |   |   |   |
    |   |   |   a
    |   |   |
    |   |   a11
    |   |   |
    |   |   a1
    |   |   |
    |   |   a
    |   |
    |   a12
    |   |
    |   (a1)
    |   |  \
    |   |   (a1)
    |   |   |  \
    |   |   |   a1
    |   |   |   |
    |   |   |   a
    |   |   |
    |   |   a1
    |   |   |
    |   |   a
    |   |
    |   a11
    |   |
    |   a1
    |   |
    |   a
    |
    a21
    |
    (a2)
    |  \
    |   (a2)
    |   |  \
    |   |   a2
    |   |   |
    |   |   a
    |   |
    |   (a1)
    |   |  \
    |   |   (a1)
    |   |   |  \
    |   |   |   a1
    |   |   |   |
    |   |   |   a
    |   |   |
    |   |   a1
    |   |   |
    |   |   a
    |   |
    |   a11
    |   |
    |   a1
    |   |
    |   a
    |
    a12
    |
    (a1)
    |  \
    |   (a1)
    |   |  \
    |   |   a1
    |   |   |
    |   |   a
    |   |
    |   a1
    |   |
    |   a
    |
    a11
    |
    a1
    |
    a
    
    """

def test_explicit():
    """
    >>> a = E('a')
    >>> a.y = 42
    >>> a.b = E('b')
    >>> a.b.c = E('c')
    >>> show(a.b.c)
    c
    |
    b
    |
    a

    >>> show(a.b.c.aq_parent)
    b
    |
    a

    >>> show(a.b.c.aq_self)
    c

    >>> show(a.b.c.aq_base)
    c

    >>> show(a.b.c.aq_inner)
    c
    |
    b
    |
    a

    >>> a.b.c.y
    Traceback (most recent call last):
    ...
    AttributeError: y

    >>> a.b.c.aq_chain
    [c, b, a]

    >>> a.b.c.aq_inContextOf(a)
    1
    >>> a.b.c.aq_inContextOf(a.b)
    1
    >>> a.b.c.aq_inContextOf(a.b.c)
    1


    >>> a.b.c.aq_acquire('y')
    42

    >>> a.b.c.aq_acquire('id')
    'c'

    >>> a.b.c.aq_acquire('x')
    Traceback (most recent call last):
    ...
    AttributeError: x
    
    >>> a.b.c.aq_acquire('id',
    ...  lambda searched, parent, name, ob, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: id

    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...        lambda searched, parent, name, ob, extra: extra,
    ...        1)
    'c'

    >>> Acquisition.aq_acquire(a.b.c, 'id')
    'c'

    >>> Acquisition.aq_acquire(a.b.c, 'x')
    Traceback (most recent call last):
    ...
    AttributeError: x

    >>> Acquisition.aq_acquire(a.b.c, 'y')
    42
    
    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...  lambda searched, parent, name, ob, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: id

    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...        lambda searched, parent, name, ob, extra: extra,
    ...        1)
    'c'

    >>> show(Acquisition.aq_base(a.b.c))
    c

    >>> Acquisition.aq_chain(a.b.c)
    [c, b, a]

    >>> Acquisition.aq_chain(a.b.c, 1)
    [c, b, a]

    >>> Acquisition.aq_get(a.b.c, 'id')
    'c'

    >>> Acquisition.aq_get(a.b.c, 'x')
    Traceback (most recent call last):
    ...
    AttributeError: x

    >>> Acquisition.aq_get(a.b.c, 'y')
    42

    >>> Acquisition.aq_get(a.b.c, 'x', 'foo')
    'foo'
    >>> Acquisition.aq_get(a.b.c, 'x', 'foo', 1)
    'foo'

    >>> show(Acquisition.aq_inner(a.b.c))
    c
    |
    b
    |
    a

    >>> show(Acquisition.aq_parent(a.b.c))
    b
    |
    a

    >>> show(Acquisition.aq_self(a.b.c))
    c

    """

def test_mixed_explicit_and_explicit():
    """
    >>> a = I('a')
    >>> a.y = 42
    >>> a.b = E('b')
    >>> a.b.z = 3
    >>> a.b.c = I('c')
    >>> show(a.b.c)
    c
    |
    b
    |
    a

    >>> show(a.b.c.aq_parent)
    b
    |
    a

    >>> show(a.b.c.aq_self)
    c

    >>> show(a.b.c.aq_base)
    c

    >>> show(a.b.c.aq_inner)
    c
    |
    b
    |
    a

    >>> a.b.c.y
    42

    >>> a.b.c.z
    3

    >>> a.b.c.aq_chain
    [c, b, a]

    >>> a.b.c.aq_inContextOf(a)
    1
    >>> a.b.c.aq_inContextOf(a.b)
    1
    >>> a.b.c.aq_inContextOf(a.b.c)
    1

    >>> a.b.c.aq_acquire('y')
    42

    >>> a.b.c.aq_acquire('z')
    3

    >>> a.b.c.aq_acquire('z', explicit=False)
    3

    >>> a.b.c.aq_acquire('id')
    'c'

    >>> a.b.c.aq_acquire('x')
    Traceback (most recent call last):
    ...
    AttributeError: x
    
    >>> a.b.c.aq_acquire('id',
    ...  lambda searched, parent, name, ob, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: id

    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...        lambda searched, parent, name, ob, extra: extra,
    ...        1)
    'c'

    >>> Acquisition.aq_acquire(a.b.c, 'id')
    'c'

    >>> Acquisition.aq_acquire(a.b.c, 'x')
    Traceback (most recent call last):
    ...
    AttributeError: x

    >>> Acquisition.aq_acquire(a.b.c, 'y')
    42
    
    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...  lambda searched, parent, name, ob, extra: extra)
    Traceback (most recent call last):
    ...
    AttributeError: id

    >>> Acquisition.aq_acquire(a.b.c, 'id',
    ...        lambda searched, parent, name, ob, extra: extra,
    ...        1)
    'c'

    >>> show(Acquisition.aq_base(a.b.c))
    c

    >>> Acquisition.aq_chain(a.b.c)
    [c, b, a]

    >>> Acquisition.aq_chain(a.b.c, 1)
    [c, b, a]

    >>> Acquisition.aq_get(a.b.c, 'id')
    'c'

    >>> Acquisition.aq_get(a.b.c, 'x')
    Traceback (most recent call last):
    ...
    AttributeError: x

    >>> Acquisition.aq_get(a.b.c, 'y')
    42

    >>> Acquisition.aq_get(a.b.c, 'x', 'foo')
    'foo'
    >>> Acquisition.aq_get(a.b.c, 'x', 'foo', 1)
    'foo'

    >>> show(Acquisition.aq_inner(a.b.c))
    c
    |
    b
    |
    a

    >>> show(Acquisition.aq_parent(a.b.c))
    b
    |
    a

    >>> show(Acquisition.aq_self(a.b.c))
    c

    """


def old_tests():
    """    
    >>> from ExtensionClass import Base
    >>> import Acquisition

    >>> class B(Base):
    ...     color='red'

    >>> class A(Acquisition.Implicit):
    ...     def hi(self):
    ...         print "%s()" % self.__class__.__name__, self.color

    >>> b=B()
    >>> b.a=A()
    >>> b.a.hi()
    A() red
    >>> b.a.color='green'
    >>> b.a.hi()
    A() green
    >>> try:
    ...     A().hi()
    ...     raise 'Program error', 'spam'
    ... except AttributeError: pass
    A()
    
       New test for wrapper comparisons.
    
    >>> foo = b.a
    >>> bar = b.a
    >>> foo == bar
    1
    >>> c = A()
    >>> b.c = c
    >>> b.c.d = c
    >>> b.c.d == c
    1
    >>> b.c.d == b.c
    1
    >>> b.c == c
    1


    >>> def checkContext(self, o):
    ...     # Python equivalent to aq_inContextOf
    ...     from Acquisition import aq_base, aq_parent, aq_inner
    ...     subob = self
    ...     o = aq_base(o)
    ...     while 1:
    ...         if aq_base(subob) is o: return 1
    ...         self = aq_inner(subob)
    ...         if self is None: break
    ...         subob = aq_parent(self)
    ...         if subob is None: break


    >>> checkContext(b.c, b)
    1
    >>> not checkContext(b.c, b.a)
    1
    
    >>> b.a.aq_inContextOf(b)
    1
    >>> b.c.aq_inContextOf(b)
    1
    >>> b.c.d.aq_inContextOf(b)
    1
    >>> b.c.d.aq_inContextOf(c)
    1
    >>> b.c.d.aq_inContextOf(b.c)
    1
    >>> not b.c.aq_inContextOf(foo)
    1
    >>> not b.c.aq_inContextOf(b.a)
    1
    >>> not b.a.aq_inContextOf('somestring')
    1
    """

def test_AqAlg():
    """
    >>> A=I('A')
    >>> A.B=I('B')
    >>> A.B.color='red'
    >>> A.C=I('C')
    >>> A.C.D=I('D')

    >>> A
    A
    >>> Acquisition.aq_chain(A)
    [A]
    >>> Acquisition.aq_chain(A, 1)
    [A]
    >>> map(Acquisition.aq_base, Acquisition.aq_chain(A, 1))
    [A]
    >>> A.C
    C
    >>> Acquisition.aq_chain(A.C)
    [C, A]
    >>> Acquisition.aq_chain(A.C, 1)
    [C, A]
    >>> map(Acquisition.aq_base, Acquisition.aq_chain(A.C, 1))
    [C, A]

    >>> A.C.D
    D
    >>> Acquisition.aq_chain(A.C.D)
    [D, C, A]
    >>> Acquisition.aq_chain(A.C.D, 1)
    [D, C, A]
    >>> map(Acquisition.aq_base, Acquisition.aq_chain(A.C.D, 1))
    [D, C, A]

    >>> A.B.C
    C
    >>> Acquisition.aq_chain(A.B.C)
    [C, B, A]
    >>> Acquisition.aq_chain(A.B.C, 1)
    [C, A]
    >>> map(Acquisition.aq_base, Acquisition.aq_chain(A.B.C, 1))
    [C, A]

    >>> A.B.C.D
    D
    >>> Acquisition.aq_chain(A.B.C.D)
    [D, C, B, A]
    >>> Acquisition.aq_chain(A.B.C.D, 1)
    [D, C, A]
    >>> map(Acquisition.aq_base, Acquisition.aq_chain(A.B.C.D, 1))
    [D, C, A]
    

    >>> A.B.C.D.color
    'red'
    >>> Acquisition.aq_get(A.B.C.D, "color", None)
    'red'
    >>> Acquisition.aq_get(A.B.C.D, "color", None, 1)
    
    """

def test_explicit_acquisition():
    """
    >>> from ExtensionClass import Base
    >>> import Acquisition

    >>> class B(Base):
    ...     color='red'

    >>> class A(Acquisition.Explicit):
    ...     def hi(self):
    ...         print self.__class__.__name__, self.acquire('color')

    >>> b=B()
    >>> b.a=A()
    >>> b.a.hi()
    A red
    >>> b.a.color='green'
    >>> b.a.hi()
    A green

    >>> try:
    ...     A().hi()
    ...     raise 'Program error', 'spam'
    ... except AttributeError: pass
    A
    
    """

def test_creating_wrappers_directly():
    """
    >>> from ExtensionClass import Base
    >>> from Acquisition import ImplicitAcquisitionWrapper

    >>> class B(Base):
    ...     pass


    >>> a = B()
    >>> a.color = 'red'
    >>> a.b = B()
    >>> w = ImplicitAcquisitionWrapper(a.b, a)
    >>> w.color
    'red'

    >>> w = ImplicitAcquisitionWrapper(a.b)
    Traceback (most recent call last):
    ...
    TypeError: __init__() takes exactly 2 arguments (1 given)

    We can reassign aq_parent

    >>> x = B()
    >>> x.color = 'green'
    >>> w.aq_parent = x
    >>> w.color
    'green'

    >>> w = ImplicitAcquisitionWrapper()
    Traceback (most recent call last):
    ...
    TypeError: __init__() takes exactly 2 arguments (0 given)

    >>> w = ImplicitAcquisitionWrapper(obj=1)
    Traceback (most recent call last):
    ...
    TypeError: kwyword arguments not allowed
    """

def test_cant_pickle_acquisition_wrappers_classic():
    """
    >>> import pickle

    >>> class X:
    ...     def __getstate__(self):
    ...         return 1

    We shouldn't be able to pickle wrappers:

    >>> from Acquisition import ImplicitAcquisitionWrapper
    >>> w = ImplicitAcquisitionWrapper(X(), X())
    >>> pickle.dumps(w)
    Traceback (most recent call last):
    ...
    TypeError: Can't pickle objects in acquisition wrappers.

    But that's not enough. We need to defeat persistence as well. :)
    This is tricky. We want to generate the error in __getstate__, not
    in the attr access, as attribute errors are too-often hidden:

    >>> getstate = w.__getstate__
    >>> getstate()
    Traceback (most recent call last):
    ...
    TypeError: Can't pickle objects in acquisition wrappers.

    We shouldn't be able to pickle wrappers:

    >>> from Acquisition import ExplicitAcquisitionWrapper
    >>> w = ExplicitAcquisitionWrapper(X(), X())
    >>> pickle.dumps(w)
    Traceback (most recent call last):
    ...
    TypeError: Can't pickle objects in acquisition wrappers.

    But that's not enough. We need to defeat persistence as well. :)
    This is tricky. We want to generate the error in __getstate__, not
    in the attr access, as attribute errors are too-often hidden:

    >>> getstate = w.__getstate__
    >>> getstate()
    Traceback (most recent call last):
    ...
    TypeError: Can't pickle objects in acquisition wrappers.
    """

def test_cant_pickle_acquisition_wrappers_newstyle():
    """
    >>> import pickle

    >>> class X(object):
    ...     def __getstate__(self):
    ...         return 1

    We shouldn't be able to pickle wrappers:

    >>> from Acquisition import ImplicitAcquisitionWrapper
    >>> w = ImplicitAcquisitionWrapper(X(), X())
    >>> pickle.dumps(w)
    Traceback (most recent call last):
    ...
    TypeError: Can't pickle objects in acquisition wrappers.

    But that's not enough. We need to defeat persistence as well. :)
    This is tricky. We want to generate the error in __getstate__, not
    in the attr access, as attribute errors are too-often hidden:

    >>> getstate = w.__getstate__
    >>> getstate()
    Traceback (most recent call last):
    ...
    TypeError: Can't pickle objects in acquisition wrappers.

    We shouldn't be able to pickle wrappers:

    >>> from Acquisition import ExplicitAcquisitionWrapper
    >>> w = ExplicitAcquisitionWrapper(X(), X())
    >>> pickle.dumps(w)
    Traceback (most recent call last):
    ...
    TypeError: Can't pickle objects in acquisition wrappers.

    But that's not enough. We need to defeat persistence as well. :)
    This is tricky. We want to generate the error in __getstate__, not
    in the attr access, as attribute errors are too-often hidden:

    >>> getstate = w.__getstate__
    >>> getstate()
    Traceback (most recent call last):
    ...
    TypeError: Can't pickle objects in acquisition wrappers.
    """

def test_z3interfaces():
    """
    >>> from zope.interface.verify import verifyClass

    Explicit and Implicit implement IAcquirer:

    >>> from Acquisition import Explicit
    >>> from Acquisition import Implicit
    >>> from Acquisition.interfaces import IAcquirer
    >>> verifyClass(IAcquirer, Explicit)
    True
    >>> verifyClass(IAcquirer, Implicit)
    True

    ExplicitAcquisitionWrapper and ImplicitAcquisitionWrapper implement
    IAcquisitionWrapper:

    >>> from Acquisition import ExplicitAcquisitionWrapper
    >>> from Acquisition import ImplicitAcquisitionWrapper
    >>> from Acquisition.interfaces import IAcquisitionWrapper
    >>> verifyClass(IAcquisitionWrapper, ExplicitAcquisitionWrapper)
    True
    >>> verifyClass(IAcquisitionWrapper, ImplicitAcquisitionWrapper)
    True
    """

def show(x):
    print showaq(x).strip()
    
def showaq(m_self, indent=''):
    rval = ''
    obj = m_self
    base = getattr(obj, 'aq_base', obj)
    try: id = base.id
    except: id = str(base)
    try: id = id()
    except: pass

    if hasattr(obj, 'aq_self'):
        if hasattr(obj.aq_self, 'aq_self'):
            rval = rval + indent + "(" + id + ")\n"
            rval = rval + indent + "|  \\\n"
            rval = rval + showaq(obj.aq_self, '|   ' + indent)
            rval = rval + indent + "|\n"
            rval = rval + showaq(obj.aq_parent, indent)
        elif hasattr(obj, 'aq_parent'):
            rval = rval + indent + id + "\n"
            rval = rval + indent + "|\n"
            rval = rval + showaq(obj.aq_parent, indent)
    else:
        rval = rval + indent + id + "\n"
    return rval



def test_Basic_gc():
    """Test to make sure that EC instances participate in GC

    >>> from ExtensionClass import Base
    >>> import gc
    >>> thresholds = gc.get_threshold()
    >>> gc.set_threshold(0)

    >>> for B in I, E:
    ...     class C1(B):
    ...         pass
    ... 
    ...     class C2(Base):
    ...         def __del__(self):
    ...             print 'removed'
    ... 
    ...     a=C1('a')
    ...     a.b = C1('a.b')
    ...     a.b.a = a
    ...     a.b.c = C2()
    ...     ignore = gc.collect()
    ...     del a
    ...     removed = gc.collect()
    ...     print removed > 0
    removed
    True
    removed
    True

    >>> gc.set_threshold(*thresholds)

    """

def test_Wrapper_gc():
    """Test to make sure that EC instances participate in GC

    >>> import gc
    >>> thresholds = gc.get_threshold()
    >>> gc.set_threshold(0)

    >>> for B in I, E:
    ...     class C:
    ...         def __del__(self):
    ...             print 'removed'
    ... 
    ...     a=B('a')
    ...     a.b = B('b')
    ...     a.a_b = a.b # circ ref through wrapper
    ...     a.b.c = C()
    ...     ignored = gc.collect()
    ...     del a
    ...     removed = gc.collect()
    ...     removed > 0
    removed
    True
    removed
    True

    >>> gc.set_threshold(*thresholds)

"""


def test_proxying():
    """Make sure that recent python slots are proxied.

    >>> import Acquisition
    >>> class Impl(Acquisition.Implicit):
    ...     pass

    >>> class C(Acquisition.Implicit):
    ...     def __getitem__(self, key):
    ...         print 'getitem', key
    ...         if key == 4:
    ...             raise IndexError
    ...         return key
    ...     def __contains__(self, key):
    ...         print 'contains', repr(key)
    ...         return key == 5

    The naked class behaves like this:

    >>> c = C()
    >>> 3 in c
    contains 3
    False
    >>> 5 in c
    contains 5
    True

    Let's put c in the context of i:

    >>> i = Impl()
    >>> i.c = c

    Now check that __contains__ is properly used:

    >>> 3 in i.c # c.__of__(i)
    contains 3
    False
    >>> 5 in i.c
    contains 5
    True

    """


import unittest
from zope.testing.doctest import DocTestSuite

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
