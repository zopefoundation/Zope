/*****************************************************************************

  Copyright (c) 1996-2003 Zope Corporation and Contributors.
  All Rights Reserved.

  This software is subject to the provisions of the Zope Public License,
  Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
  WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
  FOR A PARTICULAR PURPOSE

 ****************************************************************************/
#include "ExtensionClass/ExtensionClass.h"

#define UNLESS(E) if(!(E))
#define OBJECT(O) ((PyObject*)(O))

typedef struct {
  PyObject_HEAD
  PyObject *callable;
  int level;
} CA;

static PyObject *
CA__init__(CA *self, PyObject *args)
{
  PyObject *callable;
  int level=0;

  UNLESS(PyArg_ParseTuple(args,"O|i",&callable, &level)) return NULL;

  if (level > 0) 
    {
      callable=PyObject_CallFunction(OBJECT(self->ob_type), "Oi", 
				     callable, level-1);
      UNLESS (callable) return NULL;
      self->level=level;
    }
  else
    {
      Py_INCREF(callable);
      self->level=0;
    }

  self->callable=callable;

  Py_INCREF(Py_None);
  return Py_None;
}

static void
CA_dealloc(CA *self)     
{
  Py_DECREF(self->callable);
  Py_DECREF(self->ob_type);
  PyMem_DEL(self);
}

static PyObject *
CA_of(CA *self, PyObject *args)
{
  if (self->level > 0) 
    {
      Py_INCREF(self->callable);
      return self->callable;
    }

  if (PyString_Check(self->callable))
    {
      /* Special case string as simple alias. */
      PyObject *o;

      UNLESS (PyArg_ParseTuple(args,"O", &o)) return NULL;
      return PyObject_GetAttr(o, self->callable);
    }

  return PyObject_CallObject(self->callable, args);
}

static struct PyMethodDef CA_methods[] = {
  {"__init__",(PyCFunction)CA__init__, METH_VARARGS, ""},
  {"__of__",  (PyCFunction)CA_of,      METH_VARARGS, ""},
  {NULL,		NULL}		/* sentinel */
};

static PyExtensionClass ComputedAttributeType = {
  PyObject_HEAD_INIT(NULL) 0,
  "ComputedAttribute", sizeof(CA),
  0,
  (destructor)CA_dealloc,
  0,0,0,0,0,   0,0,0,   0,0,0,0,0,   0,0,
  "ComputedAttribute(callable) -- Create a computed attribute",
  METHOD_CHAIN(CA_methods), 
  (void*)(EXTENSIONCLASS_BINDABLE_FLAG)
};

static struct PyMethodDef methods[] = {
  {NULL,		NULL}
};

void
init_ComputedAttribute(void)
{
  PyObject *m, *d;

  UNLESS(ExtensionClassImported) return;
  
  /* Create the module and add the functions */
  m = Py_InitModule4("_ComputedAttribute", methods,
	   "Provide Computed Attributes\n\n"
	   "$Id$\n",
		     OBJECT(NULL),PYTHON_API_VERSION);

  d = PyModule_GetDict(m);
  PyExtensionClass_Export(d,"ComputedAttribute",ComputedAttributeType);
}
