/*

  $Id: ExtensionClass.h,v 1.3 1996/12/06 17:13:17 jim Exp $

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

    If you have questions regarding this software,
    contact:
   
      Jim Fulton, jim@digicool.com
      Digital Creations L.C.  
   
      (540) 371-6909


  $Log: ExtensionClass.h,v $
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

#if PYTHON_API_VERSION < 1005
typedef long getattrofunc;
typedef long setattrofunc;
#endif

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

  /* Here's the juicy stuff */
  PyMethodChain methods;
  PyObject *class_dictionary;
  PyObject *bases;
  long class_flags;
#define EXTENSIONCLASS_DYNAMIC_FLAG 1
#define EXTENSIONCLASS_BINDABLE_FLAG 2

#ifdef COUNT_ALLOCS
	/* these must be last */
	int tp_alloc;
	int tp_free;
	int tp_maxalloc;
	struct _typeobject *tp_next;
#endif
} PyExtensionClass;

#ifdef Py_COBJECT_H
PyObject *(*PyEC_getattrs)(PyObject *, char *)=NULL;
PyObject *(*PyEC_getattro)(PyObject *, PyObject *)=NULL;
int (*PyEC_setattrs)(PyObject *, char *, PyObject *)=NULL;
int (*PyEC_setattro)(PyObject *, PyObject *, PyObject *)=NULL;

#define Py_FindMethod(M,SELF,NAME) PyEC_getattrs((SELF),(NAME))

#define Py_FindAttrString(SELF,NAME) PyEC_getattrs((SELF),(NAME))
#define Py_FindAttr(SELF,NAME)       PyEC_getattro((SELF),(NAME))
#define PyEC_SetAttrString(SELF,NAME,V) PyEC_setattrs((SELF),(NAME),(V))
#define PyEC_SetAttr(SELF,NAME,V)       PyEC_setattro((SELF),(NAME),(V))

#define IMPORT_C_OBJECT(P,C,M) { \
  PyObject *_IMPORT_C_OBJECT; \
  if((_IMPORT_C_OBJECT=PyObject_GetAttrString(M,#P))) { \
    C=PyCObject_AsVoidPtr(_IMPORT_C_OBJECT); \
    Py_DECREF(_IMPORT_C_OBJECT); }}

#define PyExtensionClass_Export(D,N,T) { \
  PyObject *_ExtensionClass_module, *_ExtensionClass_spam; \
  if((_ExtensionClass_module=PyImport_ImportModule("ExtensionClass"))) { \
      if(_ExtensionClass_spam= \
	 PyObject_CallMethod(_ExtensionClass_module, \
			     "ExtensionClassType", "Oi", &T, 42)) { \
	Py_DECREF(_ExtensionClass_spam); \
	PyMapping_SetItemString(D,N,(PyObject*)&T); } \
      IMPORT_C_OBJECT(_PyEC_getattrs,PyEC_getattrs,_ExtensionClass_module) \
      IMPORT_C_OBJECT(_PyEC_getattro,PyEC_getattro,_ExtensionClass_module) \
      IMPORT_C_OBJECT(_PyEC_setattrs,PyEC_setattrs,_ExtensionClass_module) \
      IMPORT_C_OBJECT(_PyEC_setattro,PyEC_setattro,_ExtensionClass_module) \
      Py_DECREF(_ExtensionClass_module); }}

#else

/* Don't look at this. :-) */
#define Py_FindMethod(M,SELF,NAME) \
 ((getattrfunc)((SELF)->ob_type->ob_type->tp_getattr((SELF)->ob_type,"."))) \
     ((SELF),(NAME)) 

#define Py_FindAttrString(SELF,NAME) \
 ((getattrfunc)((SELF)->ob_type->ob_type->tp_getattr((SELF)->ob_type,"."))) \
     ((SELF),(NAME) )

#define PyEC_SetAttrString(SELF,NAME,V) \
 ((setattrfunc)((SELF)->ob_type->ob_type->tp_getattr((SELF)->ob_type, \
						     ".s"))) \
     ((SELF),(NAME),(V)) 

#define PyExtensionClass_Export(D,N,T) { \
  PyObject *_ExtensionClass_module; \
  if((_ExtensionClass_module=PyImport_ImportModule("ExtensionClass"))) { \
      if(PyObject_CallMethod(_ExtensionClass_module, \
			     "ExtensionClassType", "Oi", &T, 42)) \
	PyMapping_SetItemString(D,N,(PyObject*)&T); \
      Py_DECREF(_ExtensionClass_module); \
  } \
}

#endif

#define METHOD_CHAIN(DEF) { DEF, NULL }

#define CHECK_FOR_ERRORS(MESS) \
if(PyErr_Occurred()) { \
  PyObject *__sys_exc_type, *__sys_exc_value, *__sys_exc_traceback; \
  PyErr_Fetch( &__sys_exc_type, &__sys_exc_value, &__sys_exc_traceback); \
  fprintf(stderr, # MESS ":\n\t"); \
  PyObject_Print(__sys_exc_type, stderr,0); \
  fprintf(stderr,", "); \
  PyObject_Print(__sys_exc_value, stderr,0); \
  fprintf(stderr,"\n"); \
  fflush(stderr); \
  Py_FatalError(# MESS); \
}
  
#endif


