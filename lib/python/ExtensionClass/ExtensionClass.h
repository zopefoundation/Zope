/*****************************************************************************

  Copyright (c) 1996-2002 Zope Foundation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/

/*

  $Id$

  Extension Class Definitions

  Implementing base extension classes
  
    A base extension class is implemented in much the same way that an
    extension type is implemented, except:
  
    - The include file, 'ExtensionClass.h', must be included.
 
    - The type structure is declared to be of type
	  'PyExtensionClass', rather than of type 'PyTypeObject'.
 
    - The type structure has an additional member that must be defined
	  after the documentation string.  This extra member is a method chain
	  ('PyMethodChain') containing a linked list of method definition
	  ('PyMethodDef') lists.  Method chains can be used to implement
	  method inheritance in C.  Most extensions don't use method chains,
	  but simply define method lists, which are null-terminated arrays
	  of method definitions.  A macro, 'METHOD_CHAIN' is defined in
	  'ExtensionClass.h' that converts a method list to a method chain.
	  (See the example below.)
  
    - Module functions that create new instances must be replaced by an
	  '__init__' method that initializes, but does not create storage for 
	  instances.
  
    - The extension class must be initialized and exported to the module
	  with::
  
	      PyExtensionClass_Export(d,"name",type);
  
	  where 'name' is the module name and 'type' is the extension class
	  type object.
  
    Attribute lookup
  
	  Attribute lookup is performed by calling the base extension class
	  'getattr' operation for the base extension class that includes C
	  data, or for the first base extension class, if none of the base
	  extension classes include C data.  'ExtensionClass.h' defines a
	  macro 'Py_FindAttrString' that can be used to find an object's
	  attributes that are stored in the object's instance dictionary or
	  in the object's class or base classes::
  
	     v = Py_FindAttrString(self,name);
  
	  In addition, a macro is provided that replaces 'Py_FindMethod'
	  calls with logic to perform the same sort of lookup that is
	  provided by 'Py_FindAttrString'.
  
    Linking
  
	  The extension class mechanism was designed to be useful with
	  dynamically linked extension modules.  Modules that implement
	  extension classes do not have to be linked against an extension
	  class library.  The macro 'PyExtensionClass_Export' imports the
	  'ExtensionClass' module and uses objects imported from this module
	  to initialize an extension class with necessary behavior.

*/

#ifndef EXTENSIONCLASS_H
#define EXTENSIONCLASS_H

#include "Python.h"
#include "import.h"

/* Declarations for objects of type ExtensionClass */

#define EC PyTypeObject
#define PyExtensionClass PyTypeObject

#define EXTENSIONCLASS_BINDABLE_FLAG      1 << 2
#define EXTENSIONCLASS_NOINSTDICT_FLAG    1 << 5

typedef struct {
  PyObject_HEAD
} _emptyobject;

static struct ExtensionClassCAPIstruct {

/*****************************************************************************

  WARNING: THIS STRUCT IS PRIVATE TO THE EXTENSION CLASS INTERFACE
           IMPLEMENTATION AND IS SUBJECT TO CHANGE !!!

 *****************************************************************************/


  PyObject *(*EC_findiattrs_)(PyObject *self, char *cname);
  int (*PyExtensionClass_Export_)(PyObject *dict, char *name, 
                                  PyTypeObject *typ);
  PyObject *(*PyECMethod_New_)(PyObject *callable, PyObject *inst);
  PyExtensionClass *ECBaseType_;
  PyExtensionClass *ECExtensionClassType_;
}  *PyExtensionClassCAPI = NULL;

#define ECBaseType (PyExtensionClassCAPI->ECBaseType_)
#define ECExtensionClassType (PyExtensionClassCAPI->ECExtensionClassType_)

/* Following are macros that are needed or useful for defining extension
   classes:
   */

/* This macro redefines Py_FindMethod to do attribute for an attribute
   name given by a C string lookup using extension class meta-data.
   This is used by older getattr implementations.

   This macro is used in base class implementations of tp_getattr to
   lookup methods or attributes that are not managed by the base type
   directly.  The macro is generally used to search for attributes
   after other attribute searches have failed.
   
   Note that in Python 1.4, a getattr operation may be provided that
   uses an object argument. Classes that support this new operation
   should use Py_FindAttr.
   */

#define EC_findiattrs (PyExtensionClassCAPI->EC_findiattrs_)

#define Py_FindMethod(M,SELF,NAME) (EC_findiattrs((SELF),(NAME)))

/* Do method or attribute lookup for an attribute name given by a C
   string using extension class meta-data.

   This macro is used in base class implementations of tp_getattro to
   lookup methods or attributes that are not managed by the base type
   directly.  The macro is generally used to search for attributes
   after other attribute searches have failed.
   
   Note that in Python 1.4, a getattr operation may be provided that
   uses an object argument. Classes that support this new operation
   should use Py_FindAttr.
   */
#define Py_FindAttrString(SELF,NAME)  (EC_findiattrs((SELF),(NAME)))

/* Do method or attribute lookup using extension class meta-data.

   This macro is used in base class implementations of tp_getattr to
   lookup methods or attributes that are not managed by the base type
   directly.  The macro is generally used to search for attributes
   after other attribute searches have failed.  */
#define Py_FindAttr (ECBaseType->tp_getattro)

/* Do attribute assignment for an attribute.

   This macro is used in base class implementations of tp_setattro to
   set attributes that are not managed by the base type directly.  The
   macro is generally used to assign attributes after other attribute
   attempts to assign attributes have failed.
   */
#define PyEC_SetAttr(SELF,NAME,V) (ECBaseType->tp_setattro(SELF, NAME, V))


/* Convert a method list to a method chain.  */
#define METHOD_CHAIN(DEF) (traverseproc)(DEF)

/* The following macro checks whether a type is an extension class: */
#define PyExtensionClass_Check(TYPE) \
  PyObject_TypeCheck((PyObject*)(TYPE), ECExtensionClassType)

/* The following macro checks whether an instance is an extension instance: */
#define PyExtensionInstance_Check(INST) \
  PyObject_TypeCheck(((PyObject*)(INST))->ob_type, ECExtensionClassType)

#define CHECK_FOR_ERRORS(MESS) 

/* The following macro can be used to define an extension base class
   that only provides method and that is used as a pure mix-in class. */
#define PURE_MIXIN_CLASS(NAME,DOC,METHODS) \
static PyExtensionClass NAME ## Type = { PyObject_HEAD_INIT(NULL) 0, # NAME, \
   0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, \
   0 , DOC, (traverseproc)METHODS, }

/* The following macros provide limited access to extension-class
   method facilities. */

/* Test for an ExtensionClass method: */
#define PyECMethod_Check(O) PyMethod_Check((O))

/* Create a method object that wraps a callable object and an
   instance. Note that if the callable object is an extension class
   method, then the new method will wrap the callable object that is
   wrapped by the extension class method.  Also note that if the
   callable object is an extension class method with a reference
   count of 1, then the callable object will be rebound to the
   instance and returned with an incremented reference count.
   */
#define PyECMethod_New(CALLABLE, INST) \
  PyExtensionClassCAPI->PyECMethod_New_((CALLABLE),(INST))

/* Return the instance that is bound by an extension class method. */
#define PyECMethod_Self(M) \
(PyMethod_Check((M)) ? ((PyMethodObject*)(M))->im_self : NULL)

/* Check whether an object has an __of__ method for returning itself
   in the context of it's container. */
#define has__of__(O) (PyObject_TypeCheck((O)->ob_type, ECExtensionClassType) \
                      && (O)->ob_type->tp_descr_get != NULL)

/* The following macros are used to check whether an instance
   or a class' instanses have instance dictionaries: */
#define HasInstDict(O) (_PyObject_GetDictPtr(O) != NULL)

#define ClassHasInstDict(C) ((C)->tp_dictoffset > 0))

/* Get an object's instance dictionary.  Use with caution */
#define INSTANCE_DICT(inst) (_PyObject_GetDictPtr(O))

/* Test whether an ExtensionClass, S, is a subclass of ExtensionClass C. */
#define ExtensionClassSubclass_Check(S,C) PyType_IsSubtype((S), (C))

/* Test whether an ExtensionClass instance , I, is a subclass of 
   ExtensionClass C. */
#define ExtensionClassSubclassInstance_Check(I,C) PyObject_TypeCheck((I), (C))


/* Export an Extension Base class in a given module dictionary with a
   given name and ExtensionClass structure.
   */

#define PyExtensionClass_Export(D,N,T) \
  if (! ExtensionClassImported || \
      PyExtensionClassCAPI->PyExtensionClass_Export_((D),(N),&(T)) < 0) return;


#define ExtensionClassImported \
  ((PyExtensionClassCAPI != NULL) || \
   (PyExtensionClassCAPI = PyCObject_Import("ExtensionClass","CAPI2")))


/* These are being overridded to use tp_free when used with
   new-style classes. This is to allow old extention-class code
   to work.
*/

#undef PyMem_DEL
#undef PyObject_DEL

#define PyMem_DEL(O)                                   \
  if (((O)->ob_type->tp_flags & Py_TPFLAGS_HAVE_CLASS) \
      && ((O)->ob_type->tp_free != NULL))              \
    (O)->ob_type->tp_free((PyObject*)(O));             \
  else                                                 \
    PyObject_FREE((O));

#define PyObject_DEL(O) PyMem_DEL(O)

#endif /* EXTENSIONCLASS_H */
