/*

  $Id: ExtensionClass.h,v 1.5 1997/03/08 12:44:13 jim Exp $

  Extension Class Definitions

     Copyright 

       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
       rights reserved.  Copyright in this software is owned by DCLC,
       unless otherwise indicated. Permission to use, copy and
       distribute this software is hereby granted, provided that the
       above copyright notice appear in all copies and that both that
       copyright notice and this permission notice appear. Note that
       any product, process or technology described in this software
       may be the subject of other Intellectual Property rights
       reserved by Digital Creations, L.C. and are not licensed
       hereunder.

     Trademarks 

       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
       All other trademarks are owned by their respective companies. 

     No Warranty 

       The software is provided "as is" without warranty of any kind,
       either express or implied, including, but not limited to, the
       implied warranties of merchantability, fitness for a particular
       purpose, or non-infringement. This software could include
       technical inaccuracies or typographical errors. Changes are
       periodically made to the software; these changes will be
       incorporated in new editions of the software. DCLC may make
       improvements and/or changes in this software at any time
       without notice.

     Limitation Of Liability 

       In no event will DCLC be liable for direct, indirect, special,
       incidental, economic, cover, or consequential damages arising
       out of the use of or inability to use this software even if
       advised of the possibility of such damages. Some states do not
       allow the exclusion or limitation of implied warranties or
       limitation of liability for incidental or consequential
       damages, so the above limitation or exclusion may not apply to
       you.
  
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
   
    If you have questions regarding this software,
    contact:
   
      Jim Fulton, jim@digicool.com
      Digital Creations L.C.  
   
      (540) 371-6909


  $Log: ExtensionClass.h,v $
  Revision 1.5  1997/03/08 12:44:13  jim
  Moved INSTANCE_DICT macro to public interface.

  Revision 1.4  1997/02/17 16:26:59  jim
  Many changes in access to CAPI.

  Revision 1.3  1996/12/06 17:13:17  jim
  Added support for attro functions and made use of cobject to export C
  interfaces.

  Revision 1.2  1996/11/08 22:07:26  jim
  Added parens in if to make -Wall happy.

  Revision 1.1  1996/10/22 22:25:43  jim
  *** empty log message ***


*/

#ifndef EXTENSIONCLASS_H
#define EXTENSIONCLASS_H

#include "Python.h"
#include "import.h"

/* Declarations for objects of type ExtensionClass */

typedef struct {
	PyObject_VAR_HEAD
	char *tp_name; /* For printing */
	int tp_basicsize, tp_itemsize; /* For allocation */
	
	/* Methods to implement standard operations */
	
	destructor tp_dealloc;
	printfunc tp_print;
	getattrfunc tp_getattr;
	setattrfunc tp_setattr;
	cmpfunc tp_compare;
	reprfunc tp_repr;
	
	/* Method suites for standard classes */
	
	PyNumberMethods *tp_as_number;
	PySequenceMethods *tp_as_sequence;
	PyMappingMethods *tp_as_mapping;

	/* More standard operations (at end for binary compatibility) */

	hashfunc tp_hash;
	ternaryfunc tp_call;
	reprfunc tp_str;
	getattrofunc tp_getattro;
	setattrofunc tp_setattro;
	/* Space for future expansion */
	long tp_xxx3;
	long tp_xxx4;

	char *tp_doc; /* Documentation string */

#ifdef COUNT_ALLOCS
	/* these must be last */
	int tp_alloc;
	int tp_free;
	int tp_maxalloc;
	struct _typeobject *tp_next;
#endif

  /* Here's the juicy stuff: */

  /* Put your method chain here.  If you just have a method
     list, you can use the METHON_CHAIN macro to make a chain.
     */
  PyMethodChain methods;

  /* You may set certain flags here. Only two flags are
     defined at this point, the first of which is not currently
     used.
     */
  long class_flags;
#define EXTENSIONCLASS_DYNAMIC_FLAG 1
#define EXTENSIONCLASS_BINDABLE_FLAG 2

  /* This is the class dictionary, which is normally created for you.
     If you wish, you can provide your own class dictionary object.
     If you do provide your own class dictionary, it *must* be
     a mapping object.  If the object given is also an extension
     instance, then sub-class instance dictionaries will be created
     by calling the class dictionary's class with zero argumemts.
     Otherwise, subclass dictionaries will be of the default type.
     */
  PyObject *class_dictionary;

  /* You should not set the remaining members. */
  PyObject *bases;
  PyObject *reserved;
} PyExtensionClass;

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
#define Py_FindMethod(M,SELF,NAME) \
  (PyExtensionClassCAPI->getattrs((SELF),(NAME)))

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
#define Py_FindAttrString(SELF,NAME) \
  (PyExtensionClassCAPI->getattrs((SELF),(NAME)))

/* Do method or attribute lookup using extension class meta-data.

   This macro is used in base class implementations of tp_getattr to
   lookup methods or attributes that are not managed by the base type
   directly.  The macro is generally used to search for attributes
   after other attribute searches have failed.  */
#define Py_FindAttr(SELF,NAME) (PyExtensionClassCAPI->getattro((SELF),(NAME)))

/* Do method or attribute assignment for an attribute name given by a
   C string using extension class meta-data.

   This macro is used in base class implementations of tp_setattr to
   set attributes that are not managed by the base type directly.  The
   macro is generally used to assign attributes after other attribute
   attempts to assign attributes have failed.

   Note that in Python 1.4, a setattr operation may be provided that
   uses an object argument. Classes that support this new operation
   should use PyEC_SetAttr.
   */
#define PyEC_SetAttrString(SELF,NAME,V) \
  (PyExtensionClassCAPI->setattrs((SELF),(NAME),(V)))

/* Do attribute assignment for an attribute.

   This macro is used in base class implementations of tp_setattro to
   set attributes that are not managed by the base type directly.  The
   macro is generally used to assign attributes after other attribute
   attempts to assign attributes have failed.
   */
#define PyEC_SetAttr(SELF,NAME,V) \
     (PyExtensionClassCAPI->setattro((SELF),(NAME),(V)))

/* Export an Extension Base class in a given module dictionary with a
   given name and ExtensionClass structure.
   */
#define PyExtensionClass_Export(D,N,T) \
 if(PyExtensionClassCAPI || \
   (PyExtensionClassCAPI= PyCObject_Import("ExtensionClass","CAPI"))) \
   { PyExtensionClassCAPI->Export(D,N,&T); }

/* Convert a method list to a method chain.  */
#define METHOD_CHAIN(DEF) { DEF, NULL }

/* The following macro checks whether a type is an extension class: */
#define PyExtensionClass_Check(TYPE) \
  ((PyObject*)(TYPE)->ob_type==PyExtensionClassCAPI->ExtensionClassType)

/* The following macro checks whether an instance is an extension instance: */
#define PyExtensionInstance_Check(INST) \
  ((PyObject*)(INST)->ob_type->ob_type== \
     PyExtensionClassCAPI->ExtensionClassType)

/* The following macro checks for errors and prints out an error
   message that is more informative than the one given by Python when
   an extension module initialization fails.
   */
#define CHECK_FOR_ERRORS(MESS) \
if(PyErr_Occurred()) { \
  PyObject *__sys_exc_type, *__sys_exc_value, *__sys_exc_traceback; \
  PyErr_Fetch( &__sys_exc_type, &__sys_exc_value, \
	       &__sys_exc_traceback); \
  fprintf(stderr, # MESS ":\n\t"); \
  PyObject_Print(__sys_exc_type, stderr,0); \
  fprintf(stderr,", "); \
  PyObject_Print(__sys_exc_value, stderr,0); \
  fprintf(stderr,"\n"); \
  fflush(stderr); \
  Py_FatalError(# MESS); \
}

/* The following macro can be used to define an extension base class
   that only provides method and that is used as a pure mix-in class. */
#define PURE_MIXIN_CLASS(NAME,DOC,METHODS) \
static PyExtensionClass NAME ## Type = { PyObject_HEAD_INIT(NULL) \
	0, # NAME, sizeof(PyPureMixinObject), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, \
	0, 0, 0, 0, 0, 0, 0, DOC, {METHODS, NULL}};

/* The following macros provide limited access to extension-class
   method facilities. */

/* Test for an ExtensionClass method: */
#define PyECMethod_Check(O) \
  ((PyObject*)(O)->ob_type==PyExtensionClassCAPI->MethodType)

/* Create a method object that wraps a callable object and an
   instance. Note that if the callable object is an extension class
   method, then the new method will wrap the callable object that is
   wrapped by the extension class method.  Also note that if the
   callable object is an extension class method with a reference
   count of 1, then the callable object will be rebound to the
   instance and returned with an incremented reference count.
   */
#define PyECMethod_New(CALLABLE,INST) \
  (PyExtensionClassCAPI->Method_New(CALLABLE,INST))

/* Return the instance that is bound by an extension class method. */
#define PyECMethod_Self(M) (((PyECMethodObject*)M)->self)

/* Check whether an object has an __of__ method for returning itself
   in the context of it's container. */
#define has__of__(O) \
   ((O)->ob_type->ob_type == \
        (PyTypeObject*)PyExtensionClassCAPI->ExtensionClassType && \
    (((PyExtensionClass*)((O)->ob_type))->class_flags & \
     EXTENSIONCLASS_BINDABLE_FLAG))

/* Get an object's instance dictionary.  Use with caution */
#define INSTANCE_DICT(inst) \
*(((PyObject**)inst) + (inst->ob_type->tp_basicsize/sizeof(PyObject*) - 1))


/*****************************************************************************

  WARNING: EVERYTHING BELOW HERE IS PRIVATE TO THE EXTENSION CLASS INTERFACE
           IMPLEMENTATION AND IS SUBJECT TO CHANGE !!!

 *****************************************************************************/

static struct ExtensionClassCAPIstruct {
  int (*Export)(PyObject *dict, char *name, PyExtensionClass *ob_type);
  PyObject *(*getattrs)(PyObject *, char *);
  PyObject *(*getattro)(PyObject *, PyObject *);
  int (*setattrs)(PyObject *, char *, PyObject *);
  int (*setattro)(PyObject *, PyObject *, PyObject *);
  PyObject *ExtensionClassType;
  PyObject *MethodType;
  PyObject *(*Method_New)(PyObject *callable, PyObject *inst);
} *PyExtensionClassCAPI = NULL;

typedef struct { PyObject_HEAD } PyPureMixinObject;

typedef struct {
  PyObject_HEAD
  PyTypeObject *type;
  PyObject     *self;
  PyObject     *meth;
} PyECMethodObject;

static void *
PyCObject_Import(char *module_name, char *name)
{
  PyObject *m, *c;
  void *r=NULL;
  
  if(m=PyImport_ImportModule(module_name))
    {
      if(c=PyObject_GetAttrString(m,name))
	{
	  r=PyCObject_AsVoidPtr(c);
	  Py_DECREF(c);
	}
      Py_DECREF(m);
    }

  return r;
}

#endif


