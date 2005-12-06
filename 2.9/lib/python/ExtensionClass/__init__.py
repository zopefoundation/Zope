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
"""ExtensionClass

Extension Class exists to support types derived from the old ExtensionType
meta-class that preceeded Python 2.2 and new-style classes.

As a meta-class, ExtensionClass provides the following features:

- Support for a class initialiser:

  >>> from ExtensionClass import ExtensionClass, Base

  >>> class C(Base):
  ...   def __class_init__(self):
  ...      print 'class init called'
  ...      print self.__name__
  ...   def bar(self):
  ...      return 'bar called'
  class init called
  C
  >>> c = C()
  >>> int(c.__class__ is C)
  1
  >>> int(c.__class__ is type(c))
  1

- Making sure that every instance of the meta-class has Base as a base class:

  >>> class X:
  ...     __metaclass__ = ExtensionClass

  >>> Base in X.__mro__
  1

- Provide an inheritedAttribute method for looking up attributes in
  base classes:

  >>> class C2(C):
  ...   def bar(*a):
  ...      return C2.inheritedAttribute('bar')(*a), 42
  class init called
  C2
  >>> o = C2()
  >>> o.bar()
  ('bar called', 42)

  This is for compatability with old code. New code should use super
  instead.   

The base class, Base, exists mainly to support the __of__ protocol.
The __of__ protocol is similar to __get__ except that __of__ is called
when an implementor is retrieved from an instance as well as from a
class:

>>> class O(Base):
...   def __of__(*a):
...      return a
 
>>> o1 = O()
>>> o2 = O()
>>> C.o1 = o1
>>> c.o2 = o2
>>> c.o1 == (o1, c)
1
>>> C.o1 == o1
1
>>> int(c.o2 == (o2, c))
1

We accomplish this by making a class that implements __of__ a
descriptor and treating all descriptor ExtensionClasses this way. That
is, if an extension class is a descriptor, it's __get__ method will be
called even when it is retrieved from an instance.

>>> class O(Base):
...   def __get__(*a):
...      return a
... 
>>> o1 = O()
>>> o2 = O()
>>> C.o1 = o1
>>> c.o2 = o2
>>> int(c.o1 == (o1, c, type(c)))
1
>>> int(C.o1 == (o1, None, type(c)))
1
>>> int(c.o2 == (o2, c, type(c)))
1
  
$Id$
"""

from _ExtensionClass import *
