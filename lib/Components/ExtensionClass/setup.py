#!/usr/bin/env python
"""Support for Python classes implemented in C

A lightweight mechanism has been developed for making Python
extension types more class-like.  Classes can be developed in an
extension language, such as C or C++, and these classes can be
treated like other python classes:
  
- They can be sub-classed in python,
  
- They provide access to method documentation strings, and
  
- They can be used to directly create new instances.
  
An example class shows how extension classes are implemented and how
they differ from extension types.
  
Extension classes provide additional extensions to class and
instance semantics, including:

- A protocol for accessing subobjects "in the context of" their
  containers.  This is used to implement custom method types
  and "environmental acquisition":Acquisition.html.

- A protocol for overriding method call semantics.  This is used
  to implement "synchonized" classes and could be used to
  implement argument type checking.

- A protocol for class initialization that supports execution of a
  special '__class_init__' method after a class has been
  initialized. 
  
Extension classes illustrate how the Python class mechanism can be
extended and may provide a basis for improved or specialized class
models. 
"""

# Setup file for ExtensionClass
# setup.py contributed by A.M. Kuchling <amk1@bigfoot.com>

from distutils.core import setup
from distutils.extension import Extension

ExtensionClass = Extension(name = 'ExtensionClass',
                           sources = ['src/ExtensionClass.c'])

Acquisition = Extension(name = 'Acquisition',
                        sources = ['src/Acquisition.c'])

ComputedAttribute = Extension(name = 'ComputedAttribute',
                              sources = ['src/ComputedAttribute.c'])

MethodObject = Extension(name = 'MethodObject',
                         sources = ['src/MethodObject.c'])

Missing = Extension(name = 'Missing',
                    sources = ['src/Missing.c'])

MultiMapping = Extension(name = 'MultiMapping',
                         sources = ['src/MultiMapping.c'])

Record = Extension(name = 'Record', sources = ['src/Record.c'])

Sync = Extension(name = 'Sync', sources = ['src/Sync.c'])

ThreadLock = Extension(name = 'ThreadLock',
                       sources = ['src/ThreadLock.c'])

setup(name = "ExtensionClass", 
      version = "1.3",
      description = "Support for Python classes implemented in C",
      maintainer = "Digital Creations",
      maintainer_email = "zodb-dev@zope.org",
      url = "http://www.digicool.com/releases/ExtensionClass/",

      ext_modules = [ExtensionClass, Acquisition, ComputedAttribute,
                     MethodObject, Missing, MultiMapping, Sync,
                     ThreadLock, Record],
      headers = ["src/ExtensionClass.h"],

      long_description=__doc__
      )
