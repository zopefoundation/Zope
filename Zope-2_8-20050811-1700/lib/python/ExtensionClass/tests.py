##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id$
"""

from ExtensionClass import *
import pickle


def print_dict(d):
    d = d.items()
    d.sort()
    print '{%s}' % (', '.join(
        [('%r: %r' % (k, v)) for (k, v) in d]
        ))

def test_mixing():
    """Test working with a classic class

    >>> class Classic: 
    ...   def x(self): 
    ...     return 42

    >>> class O(Base):
    ...   def __of__(*a):
    ...      return a

    >>> class O2(Classic, O):
    ...   def __of__(*a):
    ...      return (O2.inheritedAttribute('__of__')(*a), 
    ...              O2.inheritedAttribute('x')(a[0]))

    >>> class C(Base):
    ...   def __class_init__(self):
    ...      print 'class init called'
    ...      print self.__name__
    ...   def bar(self):
    ...      return 'bar called'
    class init called
    C

    >>> c = C()
    >>> o2 = O2()
    >>> c.o2 = o2
    >>> int(c.o2 == ((o2, c), 42))
    1

    Test working with a new style

    >>> class Modern(object): 
    ...   def x(self): 
    ...     return 42

    >>> class O2(Modern, O):
    ...   def __of__(*a):
    ...      return (O2.inheritedAttribute('__of__')(*a), 
    ...              O2.inheritedAttribute('x')(a[0]))

    >>> o2 = O2()
    >>> c.o2 = o2
    >>> int(c.o2 == ((o2, c), 42))
    1

    """

def test_class_creation_under_stress():
    """
    >>> for i in range(100): 
    ...   class B(Base):
    ...     print i,
    ...     if i and i%20 == 0:
    ...         print
    0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20
    21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40
    41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60
    61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80
    81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99

    >>> import gc
    >>> x = gc.collect()

    """

def old_test_add():
    """test_add.py from old EC
    
    >>> class foo(Base):
    ...     def __add__(self,other): print 'add called'

    
    >>> foo()+foo()
    add called
    """

def proper_error_on_deleattr():
    """
    Florent Guillaume wrote:

    ...

    Excellent.
    Will it also fix this particularity of ExtensionClass:
    
    
    >>> class A(Base):
    ...   def foo(self):
    ...     self.gee
    ...   def bar(self):
    ...     del self.gee
    
    >>> a=A()
    >>> a.foo()
    Traceback (most recent call last):
    ...
    AttributeError: gee
    
    >>> a.bar()
    Traceback (most recent call last):
    ...
    AttributeError: 'A' object has no attribute 'gee'
    
    I.e., the fact that KeyError is raised whereas a normal class would
    raise AttributeError.
    """

def test_NoInstanceDictionaryBase():
    """
    >>> class B(NoInstanceDictionaryBase): pass
    ... 
    >>> B().__dict__
    Traceback (most recent call last):
    ...
    AttributeError: This object has no __dict__
    >>> class B(NoInstanceDictionaryBase): 
    ...   __slots__ = ('a', 'b')
    ... 
    >>> class BB(B): pass
    ... 
    >>> b = BB()
    >>> b.__dict__
    Traceback (most recent call last):
    ...
    AttributeError: This object has no __dict__
    >>> b.a = 1
    >>> b.b = 2
    >>> b.a
    1
    >>> b.b
    2
    
    """

def test__basicnew__():
    """
    >>> x = Simple.__basicnew__()
    >>> x.__dict__
    {}
    """



def cmpattrs(self, other, *attrs):
    for attr in attrs:
        if attr[:3] in ('_v_', '_p_'):
            continue
        c = cmp(getattr(self, attr, None), getattr(other, attr, None))
        if c:
            return c
    return 0

class Simple(Base):
    def __init__(self, name, **kw):
        self.__name__ = name
        self.__dict__.update(kw)
        self._v_favorite_color = 'blue'
        self._p_foo = 'bar'

    def __cmp__(self, other):
        return cmpattrs(self, other, '__class__', *(self.__dict__.keys()))

def test_basic_pickling():
    """
    >>> x = Simple('x', aaa=1, bbb='foo')

    >>> x.__getnewargs__()
    ()

    >>> print_dict(x.__getstate__())
    {'__name__': 'x', 'aaa': 1, 'bbb': 'foo'}
    
    >>> f, (c,), state = x.__reduce__()
    >>> f.__name__
    '__newobj__'
    >>> f.__module__
    'copy_reg'
    >>> c.__name__
    'Simple'
    
    >>> print_dict(state)
    {'__name__': 'x', 'aaa': 1, 'bbb': 'foo'}
    
    >>> pickle.loads(pickle.dumps(x)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 0)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 1)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 2)) == x
    1

    >>> x.__setstate__({'z': 1})
    >>> x.__dict__
    {'z': 1}

    """

class Custom(Simple):

    def __new__(cls, x, y):
        r = Base.__new__(cls)
        r.x, r.y = x, y
        return r

    def __init__(self, x, y):
        self.a = 42

    def __getnewargs__(self):
        return self.x, self.y

    def __getstate__(self):
        return self.a

    def __setstate__(self, a):
        self.a = a


def test_pickling_w_overrides():
    """
    >>> x = Custom('x', 'y')
    >>> x.a = 99

    >>> (f, (c, ax, ay), a) = x.__reduce__()
    >>> f.__name__
    '__newobj__'
    >>> f.__module__
    'copy_reg'
    >>> c.__name__
    'Custom'
    >>> ax, ay, a
    ('x', 'y', 99)
    
    >>> pickle.loads(pickle.dumps(x)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 0)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 1)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 2)) == x
    1
    
    """

class Slotted(Base):
    __slots__ = 's1', 's2', '_p_splat', '_v_eek'
    def __init__(self, s1, s2):
        self.s1, self.s2 = s1, s2
        self._v_eek = 1
        self._p_splat = 2

class SubSlotted(Slotted):
    __slots__ = 's3', 's4'
    def __init__(self, s1, s2, s3):
        Slotted.__init__(self, s1, s2)
        self.s3 = s3

        
    def __cmp__(self, other):
        return cmpattrs(self, other, '__class__', 's1', 's2', 's3', 's4')


def test_pickling_w_slots_only():
    """
    >>> x = SubSlotted('x', 'y', 'z')

    >>> x.__getnewargs__()
    ()

    >>> d, s = x.__getstate__()
    >>> d
    >>> print_dict(s)
    {'s1': 'x', 's2': 'y', 's3': 'z'}
    
    >>> pickle.loads(pickle.dumps(x)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 0)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 1)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 2)) == x
    1

    >>> x.s4 = 'spam'
    
    >>> d, s = x.__getstate__()
    >>> d
    >>> print_dict(s)
    {'s1': 'x', 's2': 'y', 's3': 'z', 's4': 'spam'}
    
    >>> pickle.loads(pickle.dumps(x)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 0)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 1)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 2)) == x
    1

    """

class SubSubSlotted(SubSlotted):

    def __init__(self, s1, s2, s3, **kw):
        SubSlotted.__init__(self, s1, s2, s3)
        self.__dict__.update(kw)
        self._v_favorite_color = 'blue'
        self._p_foo = 'bar'
        
    def __cmp__(self, other):
        return cmpattrs(self, other,
                        '__class__', 's1', 's2', 's3', 's4',
                        *(self.__dict__.keys()))

def test_pickling_w_slots():
    """
    >>> x = SubSubSlotted('x', 'y', 'z', aaa=1, bbb='foo')

    >>> x.__getnewargs__()
    ()

    >>> d, s = x.__getstate__()
    >>> print_dict(d)
    {'aaa': 1, 'bbb': 'foo'}
    >>> print_dict(s)
    {'s1': 'x', 's2': 'y', 's3': 'z'}
    
    >>> pickle.loads(pickle.dumps(x)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 0)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 1)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 2)) == x
    1

    >>> x.s4 = 'spam'
    
    >>> d, s = x.__getstate__()
    >>> print_dict(d)
    {'aaa': 1, 'bbb': 'foo'}
    >>> print_dict(s)
    {'s1': 'x', 's2': 'y', 's3': 'z', 's4': 'spam'}

    >>> pickle.loads(pickle.dumps(x)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 0)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 1)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 2)) == x
    1

    """

def test_pickling_w_slots_w_empty_dict():
    """
    >>> x = SubSubSlotted('x', 'y', 'z')

    >>> x.__getnewargs__()
    ()

    >>> d, s = x.__getstate__()
    >>> print_dict(d)
    {}
    >>> print_dict(s)
    {'s1': 'x', 's2': 'y', 's3': 'z'}
    
    >>> pickle.loads(pickle.dumps(x)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 0)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 1)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 2)) == x
    1

    >>> x.s4 = 'spam'
    
    >>> d, s = x.__getstate__()
    >>> print_dict(d)
    {}
    >>> print_dict(s)
    {'s1': 'x', 's2': 'y', 's3': 'z', 's4': 'spam'}

    >>> pickle.loads(pickle.dumps(x)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 0)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 1)) == x
    1
    >>> pickle.loads(pickle.dumps(x, 2)) == x
    1

    """
    
def test_setattr_on_extension_type():
    """
    >>> for name in 'x', '_x', 'x_', '__x_y__', '___x__', '__x___', '_x_':
    ...     setattr(Base, name, 1)
    ...     print getattr(Base, name)
    ...     delattr(Base, name)
    ...     print getattr(Base, name, 0)
    1
    0
    1
    0
    1
    0
    1
    0
    1
    0
    1
    0
    1
    0

    >>> Base.__foo__ = 1
    Traceback (most recent call last):
    ...
    TypeError: can't set attributes of built-in/extension type """ \
        """'ExtensionClass.Base' if the attribute name begins """ \
        """and ends with __ and contains only 4 _ characters

    >>> Base.__foo__
    Traceback (most recent call last):
    ...
    AttributeError: type object 'ExtensionClass.Base' """ \
        """has no attribute '__foo__'

    >>> del Base.__foo__
    Traceback (most recent call last):
    ...
    TypeError: can't set attributes of built-in/extension type """ \
        """'ExtensionClass.Base' if the attribute name begins """ \
        """and ends with __ and contains only 4 _ characters

    """

def test_mro():
    """ExtensionClass method-resolution order

    The EC MRO is chosen to maximize backward compatibility and
    provide a model that is easy to reason about.  The basic idea is:

    I'll call this the "encapsulated base"  scheme.

    Consider:

      >>> class X(Base):
      ...    pass
      >>> class Y(Base):
      ...    pass
      >>> class Z(Base):
      ...    pass

      >>> class C(X, Y, Z):
      ...    def foo(self):
      ...       return 42

    When we look up an attribute, we do the following:

    - Look in C's dictionary first.

    - Look up the attribute in X.  We don't care how we get the
      attribute from X. If X is a new-style-class, we use the new
      algorithm. If X is a classic class, we use left-to-right
      depth-first. If X is an nsEC, use the "encapsulated base"
      algorithm.

      If we don't find the attribute in X, look in Y and then in Z,
      using the same approach.

      This algorithm will produce backward compatible results, providing
      the equivalent of left-to-right depth-first for nsECs and classic
      classes.

    We'll actually do something less abstract.  We'll use a simple
    algorthm to merge the __mro__ of the base classes, computing an
    __mro__ for classic classes using the left-to-right depth-first
    algorithm. We'll basically lay the mros end-to-end left-to-right
    and remove repeats, keeping the first occurence of each class.

    >>> [c.__name__ for c in C.__mro__]
    ['C', 'X', 'Y', 'Z', 'Base', 'object']

    For backward-compatability's sake, we actually depart from the
    above description a bit. We always put Base and object last in the
    mro, as shown in the example above. The primary reason for this is
    that object provides a do-nothing __init__ method.  It is common
    practice to mix a C-implemented base class that implements a few
    methods with a Python class that implements those methods and
    others. The idea is that the C implementation overrides selected
    methods in C, so the C subclass is listed first. Unfortunately,
    because all extension classes are required to subclass Base, and
    thus, object, the C subclass brings along the __init__ object
    from objects, which would hide any __init__ method provided by the
    Python mix-in.

    Base and object are special in that they are implied by their meta
    classes.   For example, a new-style class always has object as an
    ancestor, even if it isn't listed as a base:

    >>> class O: 
    ...     __metaclass__ = type
    
    >>> [c.__name__ for c in O.__bases__]
    ['object']
    >>> [c.__name__ for c in O.__mro__]
    ['O', 'object']

    Similarly, Base is always an ancestor of an extension class:

    >>> class E: 
    ...     __metaclass__ = ExtensionClass
    
    >>> [c.__name__ for c in E.__bases__]
    ['Base']
    >>> [c.__name__ for c in E.__mro__]
    ['E', 'Base', 'object']
    
    Base and object are generally added soley to get a particular meta
    class. They aren't used to provide application functionality and
    really shouldn't be considered when reasoning about where
    attributes come from.  They do provide some useful default
    functionality and should be included at the end of the mro.

    Here are more examples:

    >>> from ExtensionClass import Base

    >>> class NA(object):
    ...  pass
    >>> class NB(NA):
    ...  pass
    >>> class NC(NA):
    ...  pass
    >>> class ND(NB, NC):
    ...  pass
    >>> [c.__name__ for c in ND.__mro__]
    ['ND', 'NB', 'NC', 'NA', 'object']

    >>> class EA(Base):
    ...  pass
    >>> class EB(EA):
    ...  pass
    >>> class EC(EA):
    ...  pass
    >>> class ED(EB, EC):
    ...  pass
    >>> [c.__name__ for c in ED.__mro__]
    ['ED', 'EB', 'EA', 'EC', 'Base', 'object']

    >>> class EE(ED, ND):
    ...  pass
    >>> [c.__name__ for c in EE.__mro__]
    ['EE', 'ED', 'EB', 'EA', 'EC', 'ND', 'NB', 'NC', 'NA', 'Base', 'object']

    >>> class EF(ND, ED):
    ...  pass
    >>> [c.__name__ for c in EF.__mro__]
    ['EF', 'ND', 'NB', 'NC', 'NA', 'ED', 'EB', 'EA', 'EC', 'Base', 'object']

    >>> class CA:
    ...  pass
    >>> class CB(CA):
    ...  pass
    >>> class CC(CA):
    ...  pass
    >>> class CD(CB, CC):
    ...  pass

    >>> class ECD(Base, CD):
    ...  pass
    >>> [c.__name__ for c in ECD.__mro__]
    ['ECD', 'CD', 'CB', 'CA', 'CC', 'Base', 'object']

    >>> class CDE(CD, Base):
    ...  pass
    >>> [c.__name__ for c in CDE.__mro__]
    ['CDE', 'CD', 'CB', 'CA', 'CC', 'Base', 'object']

    >>> class CEND(CD, ED, ND):
    ...  pass
    >>> [c.__name__ for c in CEND.__mro__]
    ['CEND', 'CD', 'CB', 'CA', 'CC', """ \
       """'ED', 'EB', 'EA', 'EC', 'ND', 'NB', 'NC', 'NA', 'Base', 'object']
    """

def test_avoiding___init__decoy_w_inheritedAttribute():
    """

    >>> class Decoy(Base):
    ...    pass

    >>> class B(Base):
    ...    def __init__(self, a, b):
    ...       print '__init__', a, b

    >>> class C(Decoy, B):
    ...    def __init__(self):
    ...       print 'C init'
    ...       C.inheritedAttribute('__init__')(self, 1, 2)

    >>> x = C()
    C init
    __init__ 1 2
    
    """

def test_of_not_called_when_not_accessed_through_EC_instance():
    """

    >>> class Eek(Base):
    ...     def __of__(self, parent):
    ...         return self, parent

    If I define an EC instance as an attr of an ordinary class:
    
    >>> class O(object):
    ...     eek = Eek()
    
    >>> class C:
    ...     eek = Eek()

    I get the instance, without calling __of__, when I get it from
    either tha class:

    >>> O.eek is O.__dict__['eek']
    True

    >>> C.eek is C.__dict__['eek']
    True

    or an instance of the class:

    >>> O().eek is O.__dict__['eek']
    True

    >>> C().eek is C.__dict__['eek']
    True

    If I define an EC instance as an attr of an extension class:
    
    >>> class E(Base):
    ...     eek = Eek()
    

    I get the instance, without calling __of__, when I get it from
    tha class:

    >>> E.eek is E.__dict__['eek']
    True

    But __of__ is called if I go through the instance:

    >>> e = E()
    >>> e.eek == (E.__dict__['eek'], e)
    True

    """

def test_inheriting___doc__():
    """Old-style ExtensionClass inherited __doc__ from base classes.

    >>> class E(Base):
    ...     "eek"

    >>> class EE(E):
    ...     pass

    >>> EE.__doc__
    'eek'

    >>> EE().__doc__
    'eek'

    """

def test___of___w_metaclass_instance():
    """When looking for extension class instances, need to handle meta classes

    >>> class C(Base):
    ...     pass

    >>> class O(Base):
    ...     def __of__(self, parent):
    ...         print '__of__ called on an O'

    >>> class M(ExtensionClass):
    ...     pass

    >>> class X:
    ...     __metaclass__ = M
    ...     

    >>> class S(X, O):
    ...     pass

    >>> c = C()
    >>> c.s = S()
    >>> c.s
    __of__ called on an O

    """

def test___of__set_after_creation():
    """We may need to set __of__ after a class is created.

    Normally, in a class's __init__, the initialization code checks for
    an __of__ method and, if it isn't already set, sets __get__.

    If a class is persistent and loaded from the database, we want
    this to happen in __setstate__.  The pmc_init_of function allws us
    to do that.

    We'll create an extension class without a __of__. We'll also give
    it a special meta class, just to make sure that this works with
    funny metaclasses too:

    >>> import ExtensionClass
    >>> class M(ExtensionClass.ExtensionClass):
    ...     "A meta class"
    >>> class B(ExtensionClass.Base):
    ...     __metaclass__ = M
    ...     def __init__(self, name):
    ...         self.name = name
    ...     def __repr__(self):
    ...         return self.name

    >>> B.__class__ is M
    True

    >>> x = B('x')
    >>> x.y = B('y')
    >>> x.y
    y

    We define a __of__ method for B after the fact:

    >>> def __of__(self, other):
    ...     print '__of__(%r, %r)' % (self, other)
    ...     return self

    >>> B.__of__ = __of__

    We see that this has no effect:

    >>> x.y
    y

    Until we use pmc_init_of:

    >>> ExtensionClass.pmc_init_of(B)
    >>> x.y
    __of__(y, x)
    y
    
    Note that there is no harm in calling pmc_init_of multiple times:
    
    >>> ExtensionClass.pmc_init_of(B)
    >>> ExtensionClass.pmc_init_of(B)
    >>> ExtensionClass.pmc_init_of(B)
    >>> x.y
    __of__(y, x)
    y

    If we remove __of__, we'll go back to the behavior we had before:

    >>> del B.__of__
    >>> ExtensionClass.pmc_init_of(B)
    >>> x.y
    y
    

    """

def test_Basic_gc():
    """Test to make sure that EC instances participate in GC

    >>> from ExtensionClass import Base
    >>> import gc
    >>> class C1(Base):
    ...     pass
    ... 
    >>> class C2(Base):
    ...     def __del__(self):
    ...         print 'removed'
    ... 
    >>> a=C1()
    >>> a.b = C1()
    >>> a.b.a = a
    >>> a.b.c = C2()
    >>> thresholds = gc.get_threshold()
    >>> gc.set_threshold(0)
    >>> ignore = gc.collect()
    >>> del a
    >>> ignored = gc.collect()
    removed
    >>> ignored > 0
    True
    >>> gc.set_threshold(*thresholds)

"""

from zope.testing.doctest import DocTestSuite
import unittest

def test_suite():
    return unittest.TestSuite((
        DocTestSuite('ExtensionClass'),
        DocTestSuite(),
        ))

if __name__ == '__main__': unittest.main()



